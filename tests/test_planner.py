import json

import pytest

from grouptaste.planner import Person, build_plan, render_markdown, score_candidates
from grouptaste.qloo import QlooError, parse_result


def ent(eid, name=None):
    return {"entity_id": eid, "name": name or eid.upper(), "type": "urn:entity:movie"}


def test_person_parse():
    p = Person.parse("Asha: Arijit Singh,  3 Idiots ,")
    assert p == Person("Asha", ("Arijit Singh", "3 Idiots"))
    for bad in ["no colon", "Asha:", ": x"]:
        with pytest.raises(ValueError):
            Person.parse(bad)


def test_broad_agreement_beats_one_persons_top_pick():
    per = {
        "a": [ent("niche"), ent("shared")],
        "b": [ent("x"), ent("shared")],
        "c": [ent("y"), ent("shared")],
    }
    picks = score_candidates(per, [])
    assert picks[0].entity_id == "shared"
    assert picks[0].coverage == "3/3"
    niche = next(p for p in picks if p.entity_id == "niche")
    assert niche.missing == ["b", "c"]


def test_group_list_breaks_ties():
    per = {"a": [ent("m1"), ent("m2")], "b": [ent("m2"), ent("m1")]}
    assert score_candidates(per, [ent("m2")])[0].entity_id == "m2"


class FakeQloo:
    def __init__(self, table):
        self.table = table
        self.calls = []

    def __call__(self, op, payload):
        self.calls.append((op, payload))
        key = payload.get("filter_location") or ",".join(payload["signals"])
        return {
            "operation": op,
            "status": "ok",
            "results": self.table.get(key, []),
            "provenance": {"requests": [{"path": "/v2/insights", "query": payload}]},
        }


def test_build_plan_end_to_end_with_venue():
    fake = FakeQloo({
        "Arijit Singh,3 Idiots": [ent("dil"), ent("pk")],
        "Interstellar": [ent("inception"), ent("pk")],
        "3 Idiots,Arijit Singh,Interstellar": [ent("pk")],
        "Pune": [{"entity_id": "cafe", "name": "Cafe X", "properties": {"address": "FC Road"}}],
    })
    people = [Person("Asha", ("Arijit Singh", "3 Idiots")), Person("Ravi", ("Interstellar",))]
    plan = build_plan(people, fake, city="Pune")
    assert plan.picks[0].name == "PK"
    assert plan.picks[0].fans == ["Asha", "Ravi"]
    assert [v["name"] for v in plan.venue] == ["Cafe X"]
    assert len(plan.requests) == 4 == len(fake.calls)
    md = render_markdown(plan)
    assert "**PK** - in 2/2" in md and "FC Road" in md and "aggregate taste" in md


def test_needs_input_is_an_error_not_an_empty_plan():
    def ex(op, payload):
        return {"operation": op, "status": "needs_input", "summary": "pick one", "results": []}

    with pytest.raises(QlooError, match="NEEDS_INPUT"):
        build_plan([Person("a", ("x",)), Person("b", ("y",))], ex)


def test_empty_person_is_noted():
    fake = FakeQloo({"y": [ent("m")], "x,y": [ent("m")]})
    plan = build_plan([Person("a", ("x",)), Person("b", ("y",))], fake)
    assert any("a's likes" in n for n in plan.notes)


def test_group_of_one_rejected():
    with pytest.raises(ValueError):
        build_plan([Person("a", ("x",))], FakeQloo({}))


def test_parse_result_surfaces_cli_errors():
    err = json.dumps({"error": {"code": "QLOO_AUTH", "recovery": "Set QLOO_API_KEY"}})
    with pytest.raises(QlooError, match="QLOO_AUTH"):
        parse_result("recommend", err)
    with pytest.raises(QlooError, match="EMPTY_OUTPUT"):
        parse_result("recommend", "  \n")
    ok = '{"event":"started"}\n{"operation":"recommend","results":[]}\n'
    assert parse_result("recommend", ok)["operation"] == "recommend"
