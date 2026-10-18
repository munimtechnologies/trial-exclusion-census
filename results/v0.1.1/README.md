# Results: trial-exclusion-census v0.1.1 rules, full registry

This is the pre-registered run. The v0.1.1 rules were published before any of these numbers were
seen, and the tables are kept exactly as the run wrote them.

- Data: ClinicalTrials.gov API v2, fetched 2026-10-14. There are 463,180 interventional studies,
  of which 463,140 have eligibility criteria and 450,052 have an exclusion section.
- Code: the v0.1.1 tag. `code.txt` has the version and SHA-256 of each file used.
- Run: one container, 2 CPUs and 2 GB of memory. The fetch, census and recall draw took 89 minutes.

| File | What it is |
|---|---|
| `results.md` | All tables in one page |
| `summary.json` | The same numbers, machine-readable |
| `by_year.csv`, `by_sponsor.csv`, `by_phase.csv`, `plosky_areas.csv` | Tables by start year, lead sponsor class, phase, and the four areas of DeCormier Plosky et al. (2022) |
| `sample_items.csv` | 60 random flagged items per category (seed 2026), for precision |
| `PRECISION.md` | A reading of `sample_items.csv` by an AI agent working for MV2 (not yet checked by a person), with every false positive named |
| `recall/blind.md`, `recall/labels.csv` | Blind recall sample of 225 trials (150 random, 75 "broad"), to be labelled |
| `recall/flags.csv` | What the rules flagged on those trials, kept apart from `blind.md` so labelling stays blind |
| `recall/sample.jsonl`, `recall/sample_info.json` | The sampled records, so `recall_sample.py score` can re-run newer rules on the same trials |

The per-trial table (`trials.csv.gz`, about 4 MB) is not stored here. Running v0.1.1 on the same
records reproduces it.

Tables and text are CC BY 4.0. ClinicalTrials.gov data comes from the US National Library of
Medicine. The work was made by MV2 of Munim, Inc. with AI agents.
