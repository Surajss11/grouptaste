# GroupTaste

Plan one night out that a whole group will actually enjoy, grounded in
[Qloo](https://qloo.com) taste data.

Group plans usually go to whoever argues hardest. GroupTaste asks Qloo once per
person and once for the whole group, then picks what is acceptable to
*everyone*. Each pick shows how many people's personal lists it came from and
who it is weakest for, plus the exact Qloo requests behind it.

Status: early build for the [Qloo Agentic Hackathon](https://qloo.devpost.com/).
The scoring core is tested offline; live runs need an event-issued Qloo key.

## How it works

1. `recommend` (Qloo Insights `/v2/insights`) for each person's likes.
2. `recommend` once more with everyone's likes combined.
3. Consensus score per candidate: mean rank score across people, plus half the
   group-list score, scaled by the share of people who got that item. That last
   factor stops one person's niche favourite from winning.
4. Optional: `recommend` a `place` in `--city` for the same combined taste.
5. Print a Markdown plan (or `--json`) with coverage, weakest-for and evidence.

All Qloo calls go through the official `qloo exec` CLI from
`@qloo/qloo-harness`, so the key never touches this code or the repo.

## Run

```sh
npm install --global @qloo/qloo-harness   # needs Node 22.19+
qloo setup --qloo                          # paste the event key here, not in the repo
python -m grouptaste \
  --person "Asha: Arijit Singh, 3 Idiots" \
  --person "Ravi: Interstellar, Hans Zimmer" \
  --person "Meera: Taylor Swift, Little Women" \
  --type movie --city "Pune"
```

Set `GROUPTASTE_QLOO_CMD` if `qloo` is not on your `PATH`.

## Test

```sh
python -m pytest -q
```

Tests use a fake Qloo executor, so they run with no key and no network.

## Limits

Qloo results describe aggregate taste affinities. They are not evidence of any
person's real preferences, identity or future behaviour, and GroupTaste does not
claim they are.
