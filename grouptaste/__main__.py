"""CLI: python -m grouptaste --person "Asha: Arijit Singh, 3 Idiots" --person "..." """

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .planner import Person, build_plan, render_markdown
from .qloo import QlooError, cli_executor


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="grouptaste", description=__doc__)
    ap.add_argument("--person", action="append", required=True, help="'Name: like, like' (repeat)")
    ap.add_argument("--type", default="movie", help="what to pick: movie, artist, book, tv_show ...")
    ap.add_argument("--city", help="also suggest a place in this city")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--json", action="store_true", help="print the plan as JSON")
    args = ap.parse_args(argv)
    try:
        people = [Person.parse(p) for p in args.person]
        plan = build_plan(people, cli_executor, args.type, args.city, args.top)
    except (ValueError, QlooError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(asdict(plan), indent=2) if args.json else render_markdown(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
