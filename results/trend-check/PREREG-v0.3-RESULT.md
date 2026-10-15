# Result of the pre-registered trend check v0.3

Counts of 2026-10-15 from the ClinicalTrials.gov API v2 search, fetched after
[PREREG-v0.3.md](PREREG-v0.3.md) and [prereg-v0.3.json](prereg-v0.3.json) were committed. CC BY 4.0.
Made by MV2 of Munim, Inc. with AI agents.

## Short answer

- **H1 holds.** In no-phase trials (behavioural, device and procedure studies), the share of
  trials naming any cognitive, hearing or visual wording rose 1.7, 2.4 and 3.1 times from 2008 to
  2025 starts. That is more than every one of the 9 controls that pass the pre-registered
  20-match rule (largest 1.63). Exact rank-sum test: **p = 1/220 = 0.0045**.
- **H2 holds.** In the other trials, mostly drug trials, the families rose 1.5 to 1.8 times, in the
  middle of the 22 controls (0.39 to 16.3, median 1.6). **p = 0.45**: no disability-specific rise.
- **VA, no-phase trials only (secondary):** VA-led trials name the three families 2.0 to 2.7 times
  as often as the registry's no-phase trials. They name 19 of 23 controls less often, and
  "informed consent" too (0.71). Only gout (2.70) ranks among the families. **p = 4/2600 = 0.0015.**
- Every count of 2008 and 2025 that the exploratory check of 0.2.0 had made was fetched again and
  came back the same, to the trial.

## What was fixed in advance

Three pooled families (cognitive 7 wordings, hearing 6, visual 5), 23 controls that are not about
disability (12 of them never counted before) and "informed consent" as a reference. The 2025/2008
share ratio of each, in all trials, in no-phase trials and in the others (all minus no-phase). A
control with fewer than 20 matches in 2008 in a stratum is left out of that stratum's test. The
test is the exact one-sided rank-sum test of `trend_check.rank_test`. `prereg_v03.py` reads
[prereg-v0.3-counts.json](prereg-v0.3-counts.json) and recomputes every number on this page.

Denominators: 11,900 interventional trials started in 2008 (3,474 no-phase) and 30,920 in 2025
(20,003 no-phase).

## Ratios, 2025 against 2008

\* = left out of that stratum's test (fewer than 20 matches in 2008).

| Phrase | Kind | 2008 (all / no-phase) | 2025 (all / no-phase) | All trials | No-phase | Other |
|---|---|---|---|---|---|---|
| cognitive (all wordings) | family | 726 / 311 | 4,040 / 3,110 | 2.14 | **1.74** | 1.73 |
| hearing (all wordings) | family | 98 / 49 | 778 / 666 | 3.06 | **2.36** | 1.76 |
| visual (all wordings) | family | 61 / 29 | 577 / 513 | 3.64 | **3.07** | 1.54 |
| pregnant | control | 6,037 / 1,287 | 14,838 / 7,791 | 0.95 | 1.05 | 1.15 |
| hepatitis | control | 1,499 / 129 | 3,941 / 464 | 1.01 | 0.62 | 1.96 |
| allergy | control | 3,947 / 658 | 9,640 / 3,796 | 0.94 | 1.00 | 1.37 |
| gout | control | 63 / 14 | 160 / 92 | 0.98 | 1.14* | 1.07 |
| psoriasis | control | 159 / 25 | 604 / 161 | 1.46 | 1.12 | 2.55 |
| tattoo | control | 35 / 8 | 219 / 127 | 2.41 | 2.76* | 2.63 |
| migraine | control | 98 / 29 | 316 / 227 | 1.24 | 1.36 | 1.00 |
| osteoporosis | control | 123 / 50 | 370 / 284 | 1.16 | 0.99 | 0.91 |
| claustrophobia | control | 124 / 50 | 528 / 334 | 1.64 | 1.16 | 2.02 |
| lactose intolerance | control | 48 / 9 | 134 / 94 | 1.07 | 1.81* | 0.79 |
| sickle cell | control | 66 / 18 | 186 / 83 | 1.08 | 0.80* | 1.66 |
| celiac (new) | control | 69 / 17 | 384 / 242 | 2.14 | 2.47* | 2.11 |
| eczema (new) | control | 119 / 24 | 419 / 168 | 1.36 | 1.22 | 2.04 |
| kidney stones (new) | control | 81 / 19 | 122 / 91 | 0.58 | 0.83* | 0.39 |
| rosacea (new) | control | 25 / 3 | 50 / 34 | 0.77 | 1.97* | 0.56 |
| shingles (new) | control | 43 / 9 | 224 / 47 | 2.00 | 0.91* | 4.02 |
| endometriosis (new) | control | 50 / 10 | 182 / 138 | 1.40 | 2.40* | 0.85 |
| vitiligo (new) | control | 24 / 3 | 479 / 36 | 7.68 | 2.08* | 16.28 |
| gallstones (new) | control | 53 / 7 | 122 / 32 | 0.89 | 0.79* | 1.51 |
| hernia (new) | control | 84 / 34 | 465 / 319 | 2.13 | 1.63 | 2.25 |
| acne (new) | control | 52 / 13 | 125 / 86 | 0.93 | 1.15* | 0.77 |
| hemorrhoids (new) | control | 20 / 6 | 49 / 30 | 0.94 | 0.87* | 1.05* |
| varicose veins (new) | control | 88 / 13 | 337 / 115 | 1.47 | 1.54* | 2.28 |
| informed consent | reference | 4,618 / 986 | 14,665 / 7,846 | 1.22 | 1.38 | 1.45 |

## Tests

| Test | Families | Controls | Largest control | Rank sum | p | Pre-registered |
|---|---|---|---|---|---|---|
| **H1: no-phase** | 1.74, 2.36, 3.07 | 9 | 1.63 (hernia) | 33 of 33 possible | **0.0045** | primary |
| **H2: other** | 1.54, 1.73, 1.76 | 22 | 16.28 (vitiligo) | 41 (39 expected) | **0.45** | primary |
| All trials | 2.14, 3.06, 3.64 | 23 | 7.68 (vitiligo) | 70.5 | 0.005 | reported |
| No-phase, every control kept | | 23 | 2.76 (tattoo) | 66 | 0.020 | not (sensitivity) |
| Other, every control kept | | 23 | 16.28 | 44 | 0.41 | not (sensitivity) |
| VA against registry, no-phase | 2.73, 1.99, 1.97 | 23 | 2.70 (gout) | 73 | **0.0015** | secondary |

Next to the exploratory 0.2.0 result (11 controls, no 20-match rule): no-phase p = 0.019, other
p = 0.33, all trials p = 0.0055. The direction and the split between no-phase and other trials
are the same.

### VA-led against all no-phase trials (all start years)

2,057 VA-led no-phase trials against 238,806 in the registry. Families: cognitive 688 against
29,301 (2.73 times), hearing 95 against 5,529 (1.99), visual 74 against 4,362 (1.97). Controls:
gout 2.70, varicose veins 1.15, claustrophobia 1.35, kidney stones 1.11, and every other one below
1: migraine 0.80, sickle cell 0.65, pregnant 0.57, eczema 0.50, hepatitis 0.45, osteoporosis 0.44,
hernia 0.44, hemorrhoids 0.33, psoriasis 0.32, allergy 0.27, lactose intolerance 0.24, celiac
0.20, tattoo 0.17, and none at all for rosacea, shingles, endometriosis, vitiligo, gallstones and
acne. "Informed consent" 0.71. This closes the gap noted in
[VA-CHECK.md](../sponsor-check/VA-CHECK.md), which had no controls within no-phase trials.

## Honest limits

- **The 20-match rule was written knowing some 2008 counts.** When the pre-registration was
  written, the 2008 no-phase counts of the 11 old controls were already public, so it was known
  that the rule would drop tattoo (8), the control that rose most in 0.2.0's no-phase test, along
  with gout, lactose intolerance and sickle cell. The 12 new controls were not known. Keeping every
  control, H1 still holds (p = 0.020), but by less: tattoo, celiac and endometriosis, all with 17 or
  fewer no-phase trials in 2008, rise as fast as the hearing family. The rule cut the no-phase
  test to 9 controls, because 10 of the 12 new ones were too rare in 2008 no-phase trials. A
  stronger test would choose controls by their 2008 counts in each stratum.
- **Controls can move a lot for reasons unrelated to disability.** In drug trials vitiligo rose 16
  times and shingles 4 times. A likely reason is the arrival of new drug classes (for example JAK
  inhibitors, whose trials often exclude people with recent shingles and include people with
  vitiligo), but this was not checked. That is why a single control proves little and the test
  ranks the families against many.
- **Mentions, not exclusions.** The search counts a phrase anywhere in the eligibility criteria,
  including inclusion criteria and exceptions. The census rules and their hand checks measure
  exclusion.
- **The registry search expands synonyms** (TREND-CHECK.md section 4). It is the same search for
  every year and stratum, so comparisons hold.
- **Not yet done:** the per-year secondary analysis (every start year 2008-2025 and the slope of
  log share on year). It needs about 1,000 counts and runs as a separate job. Its result will be
  added here, whichever way it goes.
- 2025 trials are still being registered. These are the counts of 2026-10-15.

## Repeat it

```
python prereg_v03.py                   # recompute every ratio and test from the saved counts
python prereg_v03.py --json out.json
```

Each count is one query that anyone can run (see the `source` fields in the counts file).
`trend_check.py --years 2008,2025 --phrases ...` refetches them.
