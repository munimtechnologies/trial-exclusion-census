# Pre-registration: VA-led against other trials of the same condition

Written 2026-10-15, before any phrase was counted in the strata below. CC BY 4.0.
Made by MV2 of Munim, Inc. with AI agents.

## Why

[VA-CHECK.md](VA-CHECK.md) and the secondary test of
[PREREG-v0.3-RESULT.md](../trend-check/PREREG-v0.3-RESULT.md) found that, within no-phase
(behavioural, device and procedure) trials, VA-led trials name cognitive, hearing and visual
disability in their eligibility criteria 2.0 to 2.7 times as often as the registry, while naming
19 of 23 non-disability controls less often (p = 0.0015). The main open limit is that VA trials
study different conditions: many are PTSD, substance-use and pain trials, and behavioural trials
in those conditions often exclude by a broad cognitive term. This test compares VA-led trials with
other trials **of the same condition**.

## What is fixed

Everything is in [va_matched.py](../../va_matched.py) 0.1.0 and
[prereg-va-matched.json](prereg-va-matched.json), committed with this file.

- **Trials:** interventional, no phase (Phase NA), all start years, counted with the
  ClinicalTrials.gov API v2 search.
- **VA-led:** `AREA[LeadSponsorClass]FED AND AREA[LeadSponsorName](VA OR Veteran OR Veterans)`,
  as in `sponsor_check.SPONSORS["va"]`. **Other trials** = all trials in the stratum minus VA-led.
- **Five condition strata, disjoint**, in priority order (a trial goes to the first it matches;
  each stratum leaves out the earlier ones):
  1. PTSD
  2. substance use: "substance use" OR alcohol OR opioid OR smoking OR tobacco
  3. depression
  4. pain
  5. cardiometabolic: diabetes OR "heart failure" OR hypertension OR coronary
- **Own conditions left out of every stratum:** trials whose condition matches cognitive,
  dementia, alzheimer, "brain injury", stroke, hearing, deafness, tinnitus, ear, vision, visual,
  eye, blindness, retina, retinal, macular or glaucoma. So a cognitive mention cannot come from a
  trial that studies cognition, brain injury or stroke.
- **Families:** the three pooled families of `trend_check.py` (cognitive 7 wordings, hearing 6,
  visual 5; no bare "blind").
- **Controls:** the trend-check controls named in at least 2,000 no-phase registry trials (all
  years, in [prereg-v0.3-counts.json](../trend-check/prereg-v0.3-counts.json)): pregnant,
  hepatitis, allergy, migraine, osteoporosis, claustrophobia, celiac and hernia. Each is counted
  without the trials that study that condition (pregnancy, hepatitis, allergy, migraine,
  osteoporosis, claustrophobia, celiac, hernia), as the families are.
- **Reference:** "informed consent", reported, not a control.
- **Measure:** for each phrase, the Mantel-Haenszel ratio of shares (VA-led share over other
  trials' share) across the five strata, with the Greenland-Robins 95% interval. The unmatched
  ratio (strata pooled) is reported beside it, as is each stratum's own ratio.
- **Floor:** a control is left out of the test if fewer than 5 VA matches are expected under no
  difference (the sum over strata of VA trials times the other trials' share). This uses only
  the other trials' counts. Families are always kept.

## Hypotheses

- **HV1 (primary):** the three families' matched ratios rank above the kept controls' (exact
  one-sided rank-sum test of `trend_check.rank_test`, alpha 0.05). It is tested only if at least
  4 controls are kept; with fewer, p cannot go below 0.05 and HV1 is reported as not testable.
- **HV2 (secondary):** the cognitive family's matched ratio has a 95% interval above 1.
- **Described, not tested:** each family's ratio in each stratum; the unmatched against the
  matched ratios (how much of the VA gap the condition mix explains); the reference phrase.

## How it will be read

- If HV1 holds, the VA's higher rate of disability mentions is not explained by its mix of these
  five conditions.
- If HV1 does not hold, the earlier VA finding may reflect the VA's mix of conditions, and
  VA-CHECK.md and the README will say so.
- Every number is reported whichever way it goes, next to the earlier VA numbers and never in
  place of them.

## What was known before this file

- The size of each stratum (no-phase trials, all years, counted on 2026-10-15 to check that the
  strata are big enough): PTSD 189 VA-led of 1,274; substance use 118 of 6,291; depression 75 of
  5,494; pain 98 of 19,189; cardiometabolic 230 of 24,793. No phrase was counted in any stratum.
- The unmatched VA no-phase ratios of all three families (1.97 to 2.73) and of the eight controls
  (0.20 to 1.35, claustrophobia highest) are public in PREREG-v0.3-RESULT.md. The controls were
  picked by how often the whole registry names them, not by their VA ratios.
- The 12 VA trials read by hand in VA-CHECK.md (several PTSD and substance-use trials).

## Limits stated in advance

- Mentions anywhere in the criteria, not hand-checked exclusions.
- The condition search expands synonyms, and strata are matched on condition only, not on
  design, age or sex. VA patients are older and mostly men.
- VA sites without VA, Veteran or Veterans in the sponsor name count as other trials.
- A control can be named as an inclusion (a hernia-repair pain trial) even after its own
  condition is left out.

## Repeat it

```
python va_matched.py --fetch --json va-matched.json   # about 130 small requests
python va_matched.py                                   # from the saved counts
```

The counts will be fetched in one run, after this file is committed, into
`results/sponsor-check/va-matched-counts.json`.
