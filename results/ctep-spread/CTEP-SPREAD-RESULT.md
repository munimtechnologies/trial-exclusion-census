# Who uses CTEP's representative-consent sentence, registry-wide? (result)

The pre-registered test in PREREG.md (this folder), run once on 2026-11-01. Order of events, all UTC:
the pre-registration and ctep_spread.py were committed at 16:32:17 on 2026-10-31 (commit 9ee0ec0);
the run found both on main at its first poll and started searching at 2026-11-01T06:23:27Z. (The
dated note in PREREG.md says it was written at about 16:45 UTC; the commit shows it was earlier.)
Run and written up by AI agents working for MV2 of Munim, Inc.; not yet checked by a person. Text
CC BY 4.0; code Apache-2.0.

## In short
The sentence "Legally authorized representatives may sign and give informed consent on behalf of
study participants" is in the eligibility text of 147 ClinicalTrials.gov trials today. It has
barely left the trials of its owners and NCI's own network.
- 132 of the 147 are linked to the National Cancer Institute (NCI) or led by Washington University School of Medicine (WashU): 86 NCI-linked, 39 WashU-led, 7 both.
- Only 15 trials (Neither) carry it without listing NCI or WashU, and every one of them was first submitted on or after 2025-06-02.
- Of the 117 trials first submitted on or after 2023-08-04, 15 are Neither (12.82%, 95% CI 7.93% to 20.08%), about half the 25% predicted.

**3 of 5 predictions hold; the main one (R1) does not.**

## Gates
All passed. P0: the pre-registration and the exact script were on main at the first poll. A1: the consent-phrase table (commit c4c0ded) has 5,473 rows and 102 anchors.
A2: the three searches returned 147, 143 and 34 studies, each read in full (147, 143 and 34 received).
A3: all 102 anchors still carry the sentence today and all 102 were found by the searches (recall 1.0).
Of the studies each search returned, 147, 142 and 4 carry the sentence.

## Predictions
- **R1 (main): fails.** 15 of 117 post-period trials are Neither (12.82%); at least 25% was predicted.
- **R2: holds.** 0 of 15 dated Neither trials were first submitted on or before 2022-07-09 (at most 10% predicted).
- **R3: holds.** 1 of 147 trials has an industry lead sponsor (0.68%; at most 5% predicted).
- **R4: fails.** 11 of 15 Neither trials also carry CTEP's stock consent line (73.33%, 95% CI 48.05% to 89.10%); at least 80% was predicted.
- **R5: holds.** The 15 Neither trials have 11 distinct lead sponsors (at least 10 predicted).

## Who the Neither trials are (not graded)
- Lead sponsors: Fred Hutchinson Cancer Center 3, Montefiore Medical Center 2, SWOG Cancer Research Network 2, and one each for Curis, Inc., University of Cincinnati, University of Florida, University of Kentucky and Virginia Commonwealth University.
- 3 Neither trials name an individual investigator as lead sponsor (not listed here).
- By first-submitted year: 11 in 2025 and 4 in 2026.

So the sentence reached other sponsors late: the first Neither trial was submitted nearly two years
after the first CTEP template version with the sentence (August 4, 2023), and most of their lead
sponsors are academic medical centres or cancer centres.

## A second route: SWOG (not pre-registered, not graded)
The PREREG framed the sentence as CTEP's. The table shows a second large user that does not use
CTEP's stock consent line at all.
- 25 trials led by SWOG Cancer Research Network carry the sentence, and none of the 25 carries CTEP's stock consent line.
- 43 of the 147 trials lack the stock line: 25 SWOG-led, 13 others linked to NCI, 3 WashU-led and 2 other Neither trials.
- The earliest first-submitted date among the 147 is 2018-01-02, a SWOG-led trial.

So the sentence travels with NCI's network, not only with CTEP's template. It sits in SWOG trials'
own consent wording.

## Before the template (not graded)
- 12 trials first submitted on or before 2022-07-09 carry the sentence today: 10 NCI-linked (3 of them SWOG-led) and 2 WashU-led.
- 18 more were first submitted between 2022-07-10 and 2023-08-03: 17 NCI-linked (7 SWOG-led) and 1 WashU-led.

The registry holds only current text, so these 30 trials may have gained the sentence in later
edits, or the sentence may have been in use before CTEP's posted template had it. Archived copies
of their registry pages can tell these apart; that is the next pre-registered test
(results/sentence-origin).

## Also reported
- 42 of the 147 trials lie outside the 2026-10-16 stock-line frame that the consent-phrase count used.
- None of the 147 carries WashU's older clause ("or that of legally authorized representative, if applicable").
- Lead-sponsor class: NIH 60, OTHER 60, NETWORK 26, INDUSTRY 1.

## What it means
- A plain route for a representative to consent, in one fixed sentence, is now standard in NCI's
  and WashU's cancer trials and in SWOG's, but uncommon elsewhere: 15 trials outside NCI and WashU
  in the whole registry.
- The R1 guess, that cancer centres copying CTEP's template would carry the sentence widely, was
  wrong: copying the stock consent line (3,666 frame trials outside the two owners) has not
  brought the sentence with it, at least not yet.

## Limits
- Current text only; the first-submitted date bounds when a trial began, not when its wording was written.
- "Neither" means the trial lists neither NCI nor WashU; some Neither trials are NCI-funded.
- Three text searches; recall was checked only against the 102 anchors.
- Text matching, not reading: a trial with the sentence may still limit representative consent elsewhere.
- One run by AI agents, not yet checked by a person.

## Files
- ctep_spread.py 0.1.0 (sha256 38234e4c87b44ff89fc51726fcbf12e740163e67475d9a4a247d3a7bd94e5651) and test_ctep_spread.py (sha256 03cdb356cea67b719535a3a35569ce0428c51c2f6c437e7edd0fd1cfa7a4ddd4), unchanged since the pre-registration commit; their 21 tests passed in the run.
- result.json, result.txt and ctep-spread-trials.csv: the run's output, unchanged.
- test_ctep_spread_result.py re-grades from the saved per-trial table with ctep_spread.py, rebuilds the
  printed result, and checks every figure in this note and the hashes.
