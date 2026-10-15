# Pre-registration: trend check v0.3

Written 2026-10-15 and committed **before** any of the counts it describes. CC BY 4.0.
Made by MV2 of Munim, Inc. with AI agents.

## Why

The trend check of 0.2.0 ([TREND-CHECK.md](TREND-CHECK.md), section 4) found that disability
wordings rose faster than non-disability controls in no-phase trials from 2008 to 2025 starts
(p = 0.019), and not in the other trials (p = 0.33). Its wordings and rare controls were chosen
after the first results were seen, so that result is exploratory. This file fixes the next test
in advance, so that its result cannot be shaped by what it finds.

## What is fixed

The machine-readable list is [prereg-v0.3.json](prereg-v0.3.json). In short:

- **Years:** every start year from 2008 to 2025. **Strata:** all trials, no-phase trials and
  the other trials.
- **Families:** the same three pooled families as 0.2.0 (cognitive 7 wordings, hearing 6,
  visual 5; no bare "blind").
- **Controls:** 23 phrases that are not about disability. That is the 3 common and 8 rare
  controls of 0.2.0 and **12 new rare controls that have never been counted**: celiac, eczema,
  kidney stones, rosacea, shingles, endometriosis, vitiligo, gallstones, hernia, acne,
  hemorrhoids and varicose veins.
- **Reference:** "informed consent", reported but not a control.

## Hypotheses and tests

1. **H1 (primary).** In no-phase trials, the 2025/2008 share ratios of the three families rank
   above those of the controls. Exact one-sided rank-sum test, alpha 0.05.
2. **H2 (primary).** In the other trials the same test gives p of 0.05 or more.
3. **Secondary.** For each phrase and stratum, the share in every year and the least-squares
   slope of log(share) on year, with the families' slopes ranked among the controls' by the same
   test. And VA-led trials against the registry within no-phase trials, with all 23 controls
   ([VA-CHECK.md](../sponsor-check/VA-CHECK.md) had no controls there).

## Rules

- A control with fewer than 20 matches in 2008 in a stratum is left out of that stratum's tests
  and listed as left out.
- Every result is reported, whichever way it goes, next to the 0.2.0 numbers.
- The lists in this file and in prereg-v0.3.json are not edited after this commit. Anything
  added later is labelled exploratory.
