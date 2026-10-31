# GroupTaste

Plan one night out that a whole group will actually enjoy, grounded in
[Qloo](https://qloo.com) Taste AI.

Group plans usually go to whoever argues hardest. GroupTaste asks Qloo once per
person and once for the whole group, then ranks what is *acceptable to as many
people as possible*. Every pick shows coverage (how many personal lists it
appeared on), who it is weakest for, and how many Qloo Insights requests backed
the plan.

Built for the [Qloo Agentic Hackathon](https://qloo.devpost.com/).

**Live sample (real API, 31 Oct 2026 IST):** [docs/sample_run.md](docs/sample_run.md)
· **Demo page:** https://surajss11.github.io/grouptaste/

## What it does

Given a few people and the things they like (movies, artists, books, …):

1. Resolves each like to a Qloo entity (auto-picks the top candidate when a name
   is ambiguous, preferring the target type).
2. Calls Qloo `recommend` once per person for the target type (e.g. `movie`).
3. Calls `recommend` once more with everyone's likes combined.
4. Scores candidates so **broad agreement beats one person's niche favourite**.
5. Optionally calls `recommend` for `place` in `--city`.
6. Prints a Markdown plan (or `--json`) with coverage, weakest-for, venues, and
   evidence.

## How Qloo Taste AI is used

All live calls go through the official `@qloo/qloo-harness` CLI:

```text
qloo exec recommend --input '{...}'
```

which hits Qloo Insights **`/v2/insights`** (plus `/search` during name
resolution). This project never embeds or logs the API key; the harness reads
`~/.qloo/config` or `QLOO_API_KEY`.

| Step | Workflow | Endpoint (via harness) | Purpose |
| --- | --- | --- | --- |
| Resolve names | built into `recommend` | `/search` then retry with entity IDs | Disambiguate "Interstellar" movie vs album |
| Per-person lists | `recommend` | `/v2/insights` | Personal candidates |
| Combined group | `recommend` | `/v2/insights` | Shared-taste candidates |
| Venue (optional) | `recommend` `place` + `filter_location` | `/v2/insights` | Where to go |

## Consensus scoring

For each candidate entity:

- Rank score from a list of length `n` at rank `r` = `(n - r) / n`
- `mean` = average of per-person rank scores (missing people contribute 0)
- `group` = rank score on the combined-group list (0 if absent)
- `share` = fraction of people whose personal list contained it
- **final** = `(mean + 0.5 * group) * (0.25 + 0.75 * share)`

The `share` term is what stops a niche favourite that only one person saw from
winning. When a group has little overlap (see the live sample), top picks still
land with coverage `1/3` — that is expected and called out in the plan.

## Architecture

```text
CLI (python -m grouptaste)
        │
        ▼
  planner.build_plan  ──► score_candidates ──► render_markdown / JSON
        │
        ▼
  qloo.cli_executor
        │  (auto-resolve needs_input → retry with entity IDs)
        ▼
  `qloo exec recommend`   (@qloo/qloo-harness)
        │
        ▼
  Qloo hackathon API  https://hackathon.api.qloo.com
        └── /search , /v2/insights
```

## Setup

```sh
# Node 22.19+ for the harness
npm install --global @qloo/qloo-harness

# Configure the hackathon key + base URL (never commit these)
qloo config set api-key "$QLOO_API_KEY"
qloo config set base-url https://hackathon.api.qloo.com
# trust the custom endpoint (required for non-production hosts)
# write trusted_base_url into ~/.qloo/config, or:
export QLOO_TRUSTED_BASE_URL=https://hackathon.api.qloo.com
export QLOO_BASE_URL=https://hackathon.api.qloo.com

qloo setup --status --json   # qloo.ready should be true, mode live
```

Python 3.10+ (stdlib only at runtime):

```sh
python3 -m venv .venv && .venv/bin/pip install pytest   # pytest only for tests
```

## Run

```sh
python -m grouptaste \
  --person "Asha: Arijit Singh, 3 Idiots" \
  --person "Ravi: Interstellar, Hans Zimmer" \
  --person "Meera: Taylor Swift, Little Women" \
  --type movie --city "Pune" --top 5
```

Set `GROUPTASTE_QLOO_CMD` if `qloo` is not on your `PATH`.

## Live sample output

See [docs/sample_run.md](docs/sample_run.md). Short excerpt from the real run:

```text
1. PK - in 1/3 personal lists, score 0.3708 - weakest for Ravi, Meera
2. The Imitation Game - in 1/3 personal lists, score 0.3125 - weakest for Asha, Meera
3. Whiplash - in 1/3 personal lists, score 0.3125 - weakest for Asha, Meera
…
Where to go: Shambhala - by the lake (Kamshet); Godaam Speciality Coffee Co. (Pune)
5 Qloo Insights requests
```

## Test

```sh
python -m pytest -q
```

Tests use a fake Qloo executor (no key, no network).

## Limits

Qloo results describe **aggregate taste affinities**. They are not evidence of
any person's real preferences, identity, or future behaviour, and GroupTaste
does not claim they are. Venue hits for a movie-taste query can look quirky —
that is the taste graph speaking, not a curated travel guide.

## License

MIT — see [LICENSE](LICENSE).
