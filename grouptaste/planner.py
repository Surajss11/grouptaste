"""Group consensus planning on top of Qloo recommendations.

The idea: ask Qloo once per person (their own taste) and once for the whole
group, then pick what is acceptable to *everyone* rather than what is loved by
the loudest person. Each pick keeps the Qloo requests that support it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .qloo import Executor, QlooError

PER_PERSON_LIMIT = 20


@dataclass(frozen=True)
class Person:
    name: str
    likes: tuple[str, ...]

    @classmethod
    def parse(cls, spec: str) -> Person:
        """Parse `Name: like one, like two` into a Person."""
        name, sep, rest = spec.partition(":")
        likes = tuple(x.strip() for x in rest.split(",") if x.strip())
        if not sep or not name.strip() or not likes:
            raise ValueError(f"expected 'Name: like, like', got {spec!r}")
        return cls(name.strip(), likes)


@dataclass
class Pick:
    entity_id: str
    name: str
    score: float
    fans: list[str]
    missing: list[str]
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def coverage(self) -> str:
        total = len(self.fans) + len(self.missing)
        return f"{len(self.fans)}/{total}"


@dataclass
class Plan:
    target_type: str
    people: list[Person]
    picks: list[Pick]
    venue: list[dict[str, Any]]
    requests: list[dict[str, Any]]
    notes: list[str]


def _results(data: dict[str, Any]) -> list[dict[str, Any]]:
    if data.get("status") == "needs_input":
        raise QlooError(str(data.get("operation", "recommend")), "NEEDS_INPUT", str(data.get("summary", "")))
    return [r for r in data.get("results", []) if isinstance(r, dict) and r.get("entity_id") and r.get("name")]


def _requests(data: dict[str, Any]) -> list[dict[str, Any]]:
    prov = data.get("provenance") or {}
    return list(prov.get("requests", [])) if isinstance(prov, dict) else []


def score_candidates(
    per_person: dict[str, list[dict[str, Any]]],
    group: list[dict[str, Any]],
) -> list[Pick]:
    """Score candidates so that broad agreement beats one person's favourite.

    Each list contributes a rank score of (n - rank) / n. The group list counts
    once like any person. Final score = mean over people + 0.5 * group score,
    multiplied by the share of people who got the item at all. That share term
    is what keeps a niche pick that only one person sees from winning.
    """
    people = list(per_person)
    seen: dict[str, dict[str, Any]] = {}
    person_scores: dict[str, dict[str, float]] = {}
    for person, items in per_person.items():
        n = max(len(items), 1)
        for rank, item in enumerate(items):
            eid = item["entity_id"]
            seen.setdefault(eid, item)
            person_scores.setdefault(eid, {})[person] = (n - rank) / n
    group_scores: dict[str, float] = {}
    n_group = max(len(group), 1)
    for rank, item in enumerate(group):
        seen.setdefault(item["entity_id"], item)
        group_scores[item["entity_id"]] = (n_group - rank) / n_group

    picks = []
    for eid, item in seen.items():
        scores = person_scores.get(eid, {})
        fans = [p for p in people if p in scores]
        share = len(fans) / len(people) if people else 0.0
        mean = sum(scores.values()) / len(people) if people else 0.0
        total = (mean + 0.5 * group_scores.get(eid, 0.0)) * (0.25 + 0.75 * share)
        picks.append(
            Pick(
                entity_id=eid,
                name=str(item["name"]),
                score=round(total, 4),
                fans=fans,
                missing=[p for p in people if p not in scores],
                details={k: item[k] for k in ("type", "popularity", "properties") if k in item},
            )
        )
    picks.sort(key=lambda p: (-p.score, -len(p.fans), p.name.lower()))
    return picks


def build_plan(
    people: list[Person],
    executor: Executor,
    target_type: str = "movie",
    city: str | None = None,
    top: int = 3,
) -> Plan:
    if len(people) < 2:
        raise ValueError("a group needs at least two people")
    requests: list[dict[str, Any]] = []
    notes: list[str] = []
    per_person: dict[str, list[dict[str, Any]]] = {}
    for person in people:
        data = executor(
            "recommend",
            {"target_type": target_type, "signals": list(person.likes), "limit": PER_PERSON_LIMIT},
        )
        per_person[person.name] = _results(data)
        requests.extend(_requests(data))
        if not per_person[person.name]:
            notes.append(f"Qloo returned nothing for {person.name}'s likes; they count as no vote.")

    all_likes = sorted({like for p in people for like in p.likes})
    group_data = executor(
        "recommend",
        {"target_type": target_type, "signals": all_likes, "limit": PER_PERSON_LIMIT},
    )
    group = _results(group_data)
    requests.extend(_requests(group_data))

    picks = score_candidates(per_person, group)[:top]
    venue: list[dict[str, Any]] = []
    if city:
        venue_data = executor(
            "recommend",
            {"target_type": "place", "signals": all_likes, "filter_location": city, "limit": 3},
        )
        venue = _results(venue_data)
        requests.extend(_requests(venue_data))
        if not venue:
            notes.append(f"No venue in {city} came back for this group's taste.")
    return Plan(target_type, people, picks, venue, requests, notes)


def render_markdown(plan: Plan) -> str:
    lines = [f"# Group night plan ({plan.target_type})", ""]
    lines.append("**Group:** " + "; ".join(f"{p.name} ({', '.join(p.likes)})" for p in plan.people))
    lines += ["", "## Picks everyone can live with", ""]
    if not plan.picks:
        lines.append("_No shared pick found. Try adding more likes per person._")
    for i, pick in enumerate(plan.picks, 1):
        weak = f" - weakest for {', '.join(pick.missing)}" if pick.missing else ""
        lines.append(f"{i}. **{pick.name}** - in {pick.coverage} personal lists, score {pick.score}{weak}")
    if plan.venue:
        lines += ["", "## Where to go", ""]
        for v in plan.venue:
            addr = (v.get("properties") or {}).get("address", "")
            lines.append(f"- **{v['name']}**" + (f" - {addr}" if addr else ""))
    if plan.notes:
        lines += ["", "## Notes", ""] + [f"- {n}" for n in plan.notes]
    lines += [
        "",
        "## Evidence",
        "",
        f"{len(plan.requests)} Qloo Insights requests (`/v2/insights`): one per person, one combined-group call, plus place lookups when --city is set.",
        "Qloo results describe aggregate taste affinities, not any person's actual preferences.",
    ]
    return "\n".join(lines) + "\n"
