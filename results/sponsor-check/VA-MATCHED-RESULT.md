# Result: VA-led against other trials of the same condition (pre-registered)

Counts of 2026-10-15 from the ClinicalTrials.gov API v2 search, made after
[PREREG-VA-MATCHED.md](PREREG-VA-MATCHED.md) was committed (7311a19). CC BY 4.0.
Made by MV2 of Munim, Inc. with AI agents.

**Correction (2026-10-15, later the same day).** The first version of this page said 263 VA-led
trials name a cognitive wording and gave the unmatched cognitive ratio as 2.90. The saved counts
add up to **255** (75 + 48 + 34 + 33 + 65), and the unmatched ratio is **2.81**. It was a slip in
adding the counts outside the code. The matched ratios, intervals, test and verdicts are unchanged.
Matching explains nearly a quarter (23%) of the cognitive gap on the log scale, not "about a
quarter". `test_va_matched.py` now checks these numbers against `va_matched.py`.

**In short:** within the same five conditions, VA-led no-phase trials still name cognitive
disability in their eligibility criteria 2.2 times as often as other trials (95% interval 2.0 to
2.5), and hearing disability 1.8 times as often (1.2 to 2.5). They name the non-disability
controls and "informed consent" **less** often. Both pre-registered hypotheses hold: HV1,
p = 0.018, and HV2. The VA's mix of conditions explains part of the earlier gap, not all of it.

## What was counted

All 130 counts are in [va-matched-counts.json](va-matched-counts.json). Each one is the
`totalCount` of the query that `va_matched.term()` builds: interventional, no phase (Phase NA),
all start years, one of five disjoint condition strata, and trials of cognitive, brain-injury,
stroke, hearing and eye conditions left out. Each control is also counted without the trials of
its own condition. The ten stratum sizes matched the sizes counted before the pre-registration
exactly.

| Stratum | VA trials | Other trials |
|---|---|---|
| ptsd | 189 | 1085 |
| substance use | 118 | 6173 |
| depression | 75 | 5419 |
| pain | 98 | 19091 |
| cardiometabolic | 230 | 24563 |

## Ratios

How many times as often VA-led trials name each phrase as other trials of the same condition.
"Matched (MH)" is the Mantel-Haenszel ratio of shares across the five strata, with its
Greenland-Robins 95% interval. "Unmatched" pools the five strata (no matching). "Expected" is how
many VA matches there would be if VA trials named the phrase as often as the other trials in
each stratum. * = control left out of the test (fewer than 5 VA matches expected).

| Phrase | Kind | VA matches | Expected | Matched (MH) | 95% interval | Unmatched | ptsd | substance use | depression | pain | cardiometabolic |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cognitive (all wordings) | family | 255 | 117.5 | **2.21** | 1.99-2.45 | 2.81 | 1.54 | 3.3 | 1.83 | 2.89 | 2.68 |
| hearing (all wordings) | family | 30 | 17.6 | **1.77** | 1.24-2.52 | 1.98 | 0.68 | 5.74 | 0.41 | 1.12 | 3.35 |
| visual (all wordings) | family | 14 | 9.1 | **1.55** | 0.92-2.62 | 1.21 | 0.82 | 2.96 | 2.46 | 1.06 | 1.32 |
| pregnant | control | 169 | 249.4 | 0.68 | 0.59-0.77 | 0.61 | 0.76 | 0.63 | 0.63 | 0.7 | 0.66 |
| hepatitis | control | 3 | 11.0 | 0.28 | 0.09-0.85 | 0.25 | 0.0 | 0.32 | 1.81 | 0.0 | 0.18 |
| allergy | control | 27 | 92.1 | 0.29 | 0.2-0.42 | 0.21 | 0.88 | 0.12 | 0.21 | 0.17 | 0.35 |
| migraine | control | 4 | 4.5 | 0.93* | 0.35-2.43 | 0.71 | 0.0 | 0.0 | 1.42 | 1.99 | 0.0 |
| osteoporosis | control | 0 | 5.4 | 0.0 | - | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| claustrophobia | control | 16 | 16.1 | 1.02 | 0.62-1.66 | 1.32 | 0.6 | 0.84 | 0.9 | 3.98 | 0.82 |
| celiac | control | 2 | 4.3 | 0.43* | 0.1-1.85 | 0.35 | 5.74 | 0.0 | 0.0 | 0.0 | 0.31 |
| hernia | control | 2 | 4.6 | 0.44* | 0.11-1.75 | 0.23 | 0.0 | 0.0 | 0.0 | 0.35 | 0.97 |
| informed consent | reference | 165 | 225.4 | 0.72 | 0.63-0.83 | 0.71 | 1.01 | 0.93 | 0.83 | 0.68 | 0.48 |

| Test | Families | Controls | Largest control | Rank sum | p |
|---|---|---|---|---|---|
| HV1: families against controls, matched | 3 | 5 | 1.02 | 21.0 | 0.0179 |

**HV1 (p < 0.05 with at least 4 controls): holds.** The three families' matched ratios (2.21,
1.77, 1.55) rank above all five kept controls (largest: claustrophobia, 1.02). With 3 families
and 5 controls, p = 1/56 = 0.018, the smallest p this test can give.

**HV2 (cognitive interval above 1): holds.** 2.21, 95% interval 1.99 to 2.45.

These numbers were first worked out by AI agents working for MV2, outside the code, from the
saved counts with the formulas of `va_matched.py` 0.1.0, because the seat that counted them has
no Python. `python va_matched.py` recomputes every number from the counts file, and
`test_va_matched.py` checks the headline values against it.

## How to read it

- **The VA gap is not only the VA's mix of conditions.** The pre-registration said that if HV1
  held, the VA's higher rate of disability mentions is not explained by its mix of these five
  conditions. It held. Within PTSD, substance-use, depression, pain and cardiometabolic trials,
  VA-led trials name a cognitive wording more often than other trials of the same condition in
  every one of the five strata (1.5 to 3.3 times).
- **Part of it is the mix.** Pooling the five strata without matching gives 2.81 for cognitive;
  matching brings it to 2.21. So nearly a quarter (23%) of the cognitive gap on the log scale
  comes from the VA running more trials in conditions where everyone names cognition often. 26% of
  other PTSD trials and 25% of other depression trials name a cognitive wording, against 11% to
  12% in the other three strata, and 27% of the VA's trials here are PTSD trials, against 2% of
  the others.
- **Hearing holds, with a wide interval (1.24 to 2.52).** It varies a lot by stratum (0.41 to
  5.74) because the VA counts are small (1 to 12 per stratum). The first 20 of the 30 VA hearing
  mentions, read in [VA-HEARING-READ.md](VA-HEARING-READ.md), all shut out people with hearing
  loss, and at least 6 tie it to the telephone or computer ("Hearing impairment that precludes
  completing telephone assessments"). Captioned telephone, relay services or text could be
  offered instead.
- **Visual does not clear 1 on its own** (1.55, interval 0.92 to 2.62; 14 VA matches). The
  pre-registered test only asks whether the families rank above the controls, and it does, but
  visual alone is not shown.
- **VA criteria are not simply fuller.** Within the same conditions they name "informed consent"
  0.72 times as often (0.63 to 0.83), pregnancy 0.68 times and allergy 0.29 times as often. Only
  claustrophobia, an MRI exclusion, is level (1.02).
- **Next to the earlier numbers, not in place of them.** [VA-CHECK.md](VA-CHECK.md) reported
  2.6 to 3.3 times against the whole registry over all trials, and 2.0 to 2.7 within no-phase
  trials. Matched on condition, within no-phase trials and against non-VA trials, it is 2.2
  (cognitive), 1.8 (hearing) and 1.5 (visual, not significant on its own).

## Exploratory, not pre-registered

- With all 8 controls, including the three the floor left out (migraine 0.93, celiac 0.43,
  hernia 0.44), the families still rank above every control: p = 1/165 = 0.006.
- Osteoporosis was kept with 5.4 VA matches expected and none found. Without it, 4 controls
  remain, the test is still allowed, and p = 1/35 = 0.029.

## Limits

- Mentions anywhere in the criteria, not exclusions confirmed by reading. In
  [VA-CHECK.md](VA-CHECK.md), 12 of 12 VA cognitive mentions read by AI agents working for MV2
  were exclusions, a small sample, not yet checked by a person.
- Matched on condition only, not on design, age or sex. VA patients are older and mostly men,
  and older age alone makes cognitive exclusions more common.
- Small VA counts: 710 VA trials in all, 14 visual and 30 hearing matches. The test's p is at its
  floor for 3 families against 5 controls, so it cannot show more than it does.
- As pre-registered and implemented, each share's denominator is the whole stratum, while a
  control's count leaves out trials of its own condition. This applies to VA and other trials
  alike.
- VA sites without VA, Veteran or Veterans in the lead sponsor name count as other trials. The
  condition search expands synonyms.
- This does not show that any exclusion is unjustified. It shows that VA-led trials name
  cognitive and hearing disability in their criteria more often than other trials of the same
  conditions. VA research offices and IRBs can check whether their own protocols need these
  exclusions.

## Prior art

A web search on 2026-10-15 found no registry-wide or condition-matched comparison of disability
exclusions in VA-led trials. The hand-coded studies (DeCormier Plosky et al. 2022; McDonald et al.
2022; the 2023 scoping review, PMC10626873) do not split by VA.

## Repeat it

```
python va_matched.py                                  # from the saved counts
python va_matched.py --fetch --json va-matched.json   # count again (about 130 small requests)
```
