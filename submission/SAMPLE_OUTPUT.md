# Live sample run

Captured against the real Qloo hackathon Taste AI API on **31 Oct 2026, ~7:56 AM IST**
(Asia/Calcutta) via `qloo exec recommend` (Insights `/v2/insights`).

Command:

```sh
python -m grouptaste \
  --person "Asha: Arijit Singh, 3 Idiots" \
  --person "Ravi: Interstellar, Hans Zimmer" \
  --person "Meera: Taylor Swift, Little Women" \
  --type movie --city "Pune" --top 5
```

Notes:
- Ambiguous names (e.g. Interstellar movie vs album) are auto-resolved to the
  top-popularity candidate (preferring the target type for signal fields) and
  the call is retried once with entity IDs.
- Coverage of 1/3 on every pick is honest: this group's likes barely overlap, so
  the consensus score leans on the combined-group Qloo list. That is a feature
  of the scoring rule, not a bug.
- Venue suggestions are Qloo `place` insights for the same combined taste in
  Pune; they are affinity-ranked, not hand-picked.

API key is never written into this repo.

---

# Group night plan (movie)

**Group:** Asha (Arijit Singh, 3 Idiots); Ravi (Interstellar, Hans Zimmer); Meera (Taylor Swift, Little Women)

## Picks everyone can live with

1. **PK** - in 1/3 personal lists, score 0.3708 - weakest for Ravi, Meera
2. **The Imitation Game** - in 1/3 personal lists, score 0.3125 - weakest for Asha, Meera
3. **Whiplash** - in 1/3 personal lists, score 0.3125 - weakest for Asha, Meera
4. **A Beautiful Mind** - in 1/3 personal lists, score 0.3042 - weakest for Asha, Meera
5. **The Shawshank Redemption** - in 1/3 personal lists, score 0.2458 - weakest for Asha, Meera

## Where to go

- **Symbiosis Centre for Media & Communication (SCMC Pune)** - Symbiosis Campus off, Symbiosis Rd, Viman Nagar Pune, Maharashtra 411014 India
- **Shambhala - by the lake** - Plot no. 67, Village Bhajgaon, Kamshet - Kundali Road, Taluka Maval Kamshet, Maharashtra 410405 India
- **Godaam Speciality Coffee Co.** - 1120, Model Colony Rd Model Colony, Shivajinagar Pune, Maharashtra 411016 India

## Evidence

5 Qloo Insights requests (`/v2/insights`), one per person plus one for the group.
Qloo results describe aggregate taste affinities, not any person's actual preferences.

