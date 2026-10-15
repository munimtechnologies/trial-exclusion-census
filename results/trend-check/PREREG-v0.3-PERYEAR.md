# Pre-registered trend check v0.3: the per-year secondary (reduced)

Counts of 2026-10-15 from the ClinicalTrials.gov API v2 search. CC BY 4.0.
Made by MV2 of Munim, Inc. with AI agents.

## What was fixed in advance

[prereg-v0.3.json](prereg-v0.3.json) named, as a secondary analysis: "For every phrase and
stratum: the share in each start year 2008-2025 and the least-squares slope of log(share) on
year; the families' slopes ranked among the controls' slopes with the same exact test." The
primary result ([PREREG-v0.3-RESULT.md](PREREG-v0.3-RESULT.md)) used only the 2008 and 2025
shares. A slope uses all 18 years, so an unusual first or last year moves it less.

## What was counted

A reduced set, because each count is a separate request: **no-phase trials only** (the stratum of
H1), the three disability families and the **9 controls that the 20-match rule keeps** there. That
is 13 counts per year, 208 for 2009-2024. The 2008 and 2025 counts are the ones already
published. Before counting, the 2008 no-phase total (3,474) and hearing count (49) were fetched
again and matched exactly. The all-trials and other-trials strata, the 14 left-out controls and
the reference phrase were **not** counted by year. All counts are in
[prereg-v0.3-peryear-counts.json](prereg-v0.3-peryear-counts.json).

## Result

Slope of log(share of no-phase trials naming the phrase) on start year, 2008-2025, steepest first:

| Phrase | Kind | Slope | Change per year |
|---|---|---|---|
| visual (all wordings) | family | 0.0703 | +7.3% |
| hearing (all wordings) | family | 0.0604 | +6.2% |
| cognitive (all wordings) | family | 0.0319 | +3.2% |
| eczema | control | 0.0237 | +2.4% |
| migraine | control | 0.0214 | +2.2% |
| psoriasis | control | 0.0204 | +2.1% |
| hernia | control | 0.0158 | +1.6% |
| claustrophobia | control | 0.0016 | +0.2% |
| pregnant | control | -0.0001 | 0.0% |
| osteoporosis | control | -0.0004 | 0.0% |
| allergy | control | -0.0043 | -0.4% |
| hepatitis | control | -0.0211 | -2.1% |

- **The three families have the three steepest slopes.** Exact one-sided rank-sum test of the 3
  families against the 9 controls: rank sum 33, **p = 1/220 = 0.0045**, the same as H1.
- The per-year view agrees with the 2025/2008 ratios, with one difference in size. Visual and
  hearing wordings rose about 6 to 7% a year, far above any control. The cognitive family rose
  3.2% a year, above every control but only 0.8 points above the steepest one (eczema, 2.4%).
  Hernia, the top control by the 2025/2008 ratio (1.63 times), is fourth among the controls by
  slope, because its 2008 count was unusually low.
- Every count dips in 2020 starts (COVID-19), as does the number of no-phase trials (14,201 to
  13,365). The slopes use shares, so only the part of a dip beyond that 6% fall counts.

## Limits

- Mentions anywhere in the criteria, not hand-checked exclusions, as in every trend-check result.
- Reduced: no-phase trials and the kept controls only. This is the stratum and the control set of
  H1, so it adds a check of H1's robustness, not a new test of H2.
- The 20-match rule that picks the 9 controls was written when some 2008 counts were known (see
  PREREG-v0.3-RESULT.md). Of the controls it leaves out, tattoo, celiac and endometriosis had
  large 2025/2008 ratios, and their slopes were not counted.
- The slopes and the test were first worked out by hand. `peryear_v03.py` recomputes them from
  the counts file, and its test checks the hand values.

## Repeat it

```
python peryear_v03.py --json peryear.json
python trend_check.py --years 2008,2009,...,2025 --phrases "cognitive (all wordings),..."   # re-fetch
```
