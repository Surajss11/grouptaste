# Devpost submission draft — GroupTaste

**Do not submit until the user approves.** Repo and demo links below are ready to paste.

## Project name
GroupTaste

## Tagline
Plan a night out the whole group can live with — powered by Qloo Taste AI, not the loudest friend.

## Demo URL
https://surajss11.github.io/grouptaste/

(Static GitHub Pages page showing a **real live Qloo API run** from 31 Oct 2026 IST, plus run-it-yourself instructions. The product itself is the CLI in the public repo.)

## Repository URL
https://github.com/Surajss11/grouptaste

## Built with
- Python 3
- Qloo Taste AI / Insights API (`/v2/insights`, `/search`)
- `@qloo/qloo-harness` (`qloo exec recommend`)
- GitHub Pages (demo)

## Inspiration
Every group chat about "what should we watch / where should we go" collapses into whoever argues hardest. Generic LLM recommenders invent vibes. We wanted something that **grounds the compromise in real cultural taste data** — per person and for the group — and shows its work (coverage, weakest-for, request count).

## What it does
GroupTaste is a CLI agentic planner:

1. Takes `--person "Name: like, like"` for 2+ people.
2. Resolves likes to Qloo entities (auto-disambiguates when a name hits movie vs album vs artist).
3. Calls Qloo `recommend` once per person and once for the combined group.
4. Scores candidates so broad agreement beats a niche favourite.
5. Optionally recommends a `place` in `--city`.
6. Prints a Markdown (or JSON) plan with coverage, weakest-for, venues, and evidence.

## How we built it
- Thin Python package (`grouptaste`) with a pure scoring core covered by offline tests.
- Live I/O only through `qloo exec recommend` so the hackathon API key never enters the repo.
- Auto-resolution loop: on `needs_input`, pick the top-popularity candidate (preferring `target_type` for signals) and retry with entity IDs.
- Real end-to-end run saved in `docs/sample_run.md` and rendered on the demo page.

## Challenges we ran into
- Ambiguous entity names (`Interstellar` movie vs albums) made first `recommend` calls return `needs_input` — fixed with auto-resolve + retry.
- Hackathon API uses `https://hackathon.api.qloo.com`, which must be explicitly trusted in the harness config (`trusted_base_url` / `QLOO_TRUSTED_BASE_URL`).
- Diverse groups honestly get low per-person overlap; we kept the scoring transparent instead of faking consensus.
- Devpost requires an externally hosted demo (not just a local CLI). We shipped a GitHub Pages page of the live sample plus clear clone-and-run steps; a key-backed public API proxy was out of scope for key safety.

## Accomplishments that we're proud of
- Real live Insights calls, not a mocked demo.
- Consensus math that is tested offline and readable in the README.
- Key never committed; harness-owned credentials only.
- Honest sample output (including low coverage and quirky place affinities).

## What we learned
- Qloo's resolution step is part of the product surface — agents must handle ambiguity, not assume unique names.
- Cultural intelligence shines when you show *why* a pick won (coverage / weakest-for), not just a ranked list.
- Hosted-demo rules push CLI tools to ship a public artifact judges can open in one click.

## What's next
- Interactive TUI / web UI that keeps the key server-side.
- Dietary, budget, and time constraints as hard filters on place results.
- Remembered resolution choices across runs (harness already supports session memory).
- Multi-stop itineraries (movie + dinner + dessert) with one shared taste graph.

---

## Required Devpost fields checklist (from https://qloo.devpost.com/ "What to Submit")

1. **Link to a functional demo application** — live, working, end-to-end.  
   → Use: `https://surajss11.github.io/grouptaste/`  
   Note: judges asked for something they can *use*; this page shows the live sample. Full interactivity needs cloning the CLI with a personal key (keys must not be public).

2. **URL to a public code repository** (GitHub/GitLab/Bitbucket) with source + run instructions.  
   → `https://github.com/Surajss11/grouptaste`

3. **Text description** of what the project does and what makes it Qloo-powered.  
   → Paste sections above (Inspiration / What it does / How we built it / …).

4. **External hosting / fully published** — live website, web app, hosted APK, or TestFlight. Local-only does **not** qualify.  
   → GitHub Pages demo satisfies "hosted externally"; strengthen later with a key-backed hosted API if allowed.

5. **Open-source license** visible in the About / repo root.  
   → MIT `LICENSE` already in repo.

**NOT required:** demo video (explicitly: "Demo videos are not required").

**Eligibility reminder:** working software that integrates Qloo and is agentic / agent-framework / wires Qloo into an agent; cultural intelligence must be the differentiator.

## Submission form paste helpers

**Project name:** GroupTaste

**Tagline / elevator pitch:** Plan a night out the whole group can live with — powered by Qloo Taste AI, not the loudest friend.

**About the project** (short):  
GroupTaste asks Qloo Taste AI once per person and once for the whole group, then ranks movies (or other types) by consensus — coverage across personal lists, not whoever shouts loudest. Optional city venue suggestions use the same combined taste. Built as a Python CLI on `qloo exec recommend` (Insights `/v2/insights`).

**Built with tags:** Python, Qloo, qloo-harness, GitHub Pages

**Try it out / Demo link:** https://surajss11.github.io/grouptaste/

**GitHub repo:** https://github.com/Surajss11/grouptaste
