# Was the representative-consent sentence in registry text before CTEP's template had it? (result)

The pre-registered test in PREREG.md (this folder), run once on 2026-11-01. Order of events, all UTC:
the pre-registration and sentence_origin.py were committed at 12:38:06 on 2026-11-01 (commit 0500b7c);
the run found both on main at the first poll and began reading the archive at 2026-11-01T15:29:26Z.
Run and written up by AI agents working for MV2 of Munim, Inc.; not yet checked by a person.
Text CC BY 4.0; code Apache-2.0.

## In short
results/ctep-template found that NCI CTEP's public protocol templates lack the sentence

> Legally authorized representatives may sign and give informed consent on behalf of study
> participants.

in every archived copy up to 2022-07-09, and that the first template version with it is dated
August 4, 2023. The Internet Archive's copies of ClinicalTrials.gov study pages show the sentence in
registry text well before either date.
- The earliest archived page with the sentence is NCT04625647, a SWOG-led trial, captured on 2020-11-13, a week after it was first submitted on 2020-11-06.
- 6 of the 11 trials with a usable page captured on or before 2022-07-09 already carry it there.
- SWOG-led trials carried it from registration (4 of 5 on their oldest page); NCI-led trials mostly gained it later (3 of 9 on their oldest page).
- 3 NCI-led trials that lacked it on their oldest page show it on pages captured between 2022-06-16 and 2022-07-01, before any archived CTEP template has it.
- Neither early WashU-led trial with an archived page shows it before August 2023.

**All 4 predictions hold.**

## Gates
All passed. P0: the pre-registration, the ctep-spread table and the exact script were on main at the first poll.
A1: the ctep-spread table has 147 trials; the cohort is its 30 trials first submitted on or before 2023-08-03 (3 WashU-led, 10 SWOG-led, 17 other NCI-linked).
A2: 16 of the 30 trials have a usable page (at least 15 needed).
A3: 27 of the 30 were read completely (at least 27 needed); index queries for NCT05642572, NCT05929768 and NCT05886036 were answered with HTTP 503.
A4: CTEP's stock consent line is on at least one usable page.
Archive reading: 60 index queries (4 errors), 42 pages downloaded (0 errors), 2,561 seconds.

## Predictions
- **S1 (main): holds.** 6 of the 11 trials with a usable page captured on or before 2022-07-09 carry the sentence on such a page: NCT04625647, NCT03907488, NCT04548752, NCT04840602, NCT04989283 and NCT05411081 (at least 1 predicted; graded only with at least 6 trials).
- **S2: holds.** 4 of the 5 SWOG-led trials with a usable oldest page carry the sentence on it (at least half predicted). The fifth, NCT03418961 (first submitted 2018-01-02), lacks it on every page read, the last captured 2023-06-03.
- **S3: holds.** 3 of the 9 other NCI-linked trials with a usable oldest page carry the sentence on it (at most half predicted): NCT04989283, NCT05411081 and NCT05807126.
- **S4: holds.** Neither of the 2 early WashU-led trials with a usable oldest page carries the sentence on it (it holds only if none does). NCT05521984 has no archived page before 2023-08-04.

## Per trial (not graded)
Each trial's usable pages: capture date and wording, for its oldest page, its last page by 2022-07-09 and its last page by 2023-08-03.
- NCT04462328 (WashU-led, first submitted 2020-07-02): 2020-10-27 neither (oldest); 2021-04-10 neither (last by 2022-07-09); 2022-08-22 neither (last by 2023-08-03).
- NCT04852328 (WashU-led, first submitted 2021-04-15): 2021-11-29 WashU clause (oldest); 2022-01-22 WashU clause (last by 2022-07-09); 2023-03-30 WashU clause (last by 2023-08-03).
- NCT03418961 (SWOG-led, first submitted 2018-01-02): 2019-08-20 neither (oldest); 2022-06-28 neither (last by 2022-07-09); 2023-06-03 neither (last by 2023-08-03).
- NCT04625647 (SWOG-led, first submitted 2020-11-06): 2020-11-13 sentence (oldest); 2022-05-26 sentence (last by 2022-07-09); 2023-06-05 sentence (last by 2023-08-03).
- NCT05455606 (SWOG-led, first submitted 2022-07-06): 2022-08-23 sentence (oldest); none (last by 2022-07-09); 2022-12-10 sentence (last by 2023-08-03).
- NCT05561387 (SWOG-led, first submitted 2022-09-27): 2022-09-30 sentence (oldest); none (last by 2022-07-09); 2022-09-30 sentence (last by 2023-08-03).
- NCT05633615 (SWOG-led, first submitted 2022-11-21): 2023-04-05 sentence (oldest); none (last by 2022-07-09); 2023-04-05 sentence (last by 2023-08-03).
- NCT03598244 (NCI-led, first submitted 2018-07-24): 2019-08-24 neither (oldest); 2022-05-16 neither (last by 2022-07-09); 2023-06-08 sentence (last by 2023-08-03).
- NCT03816319 (NCI-led, first submitted 2019-01-24): 2020-11-02 neither (oldest); 2022-03-13 neither (last by 2022-07-09); 2022-08-02 neither (last by 2023-08-03).
- NCT03907488 (NCI-led, first submitted 2019-04-08): 2019-09-19 neither (oldest); 2022-07-01 sentence (last by 2022-07-09); 2023-06-11 sentence (last by 2023-08-03).
- NCT04548752 (NCI-led, first submitted 2020-09-12): 2020-11-02 neither (oldest); 2022-06-16 sentence (last by 2022-07-09); 2023-03-29 sentence (last by 2023-08-03).
- NCT04840602 (NCI-led, first submitted 2021-04-09): 2021-06-25 neither (oldest); 2022-06-29 sentence (last by 2022-07-09); 2023-06-09 sentence (last by 2023-08-03).
- NCT04989283 (NCI-led, first submitted 2021-08-03): 2021-08-04 sentence (oldest); 2021-11-09 sentence (last by 2022-07-09); 2022-12-22 sentence (last by 2023-08-03).
- NCT05411081 (NCI-led, first submitted 2022-06-07): 2022-06-09 sentence (oldest); 2022-06-09 sentence (last by 2022-07-09); 2023-03-22 sentence (last by 2023-08-03).
- NCT05554406 (NCI-led, first submitted 2022-09-22): 2022-09-26 neither (oldest); none (last by 2022-07-09); 2022-09-26 neither (last by 2023-08-03).
- NCT05807126 (NCI-led, first submitted 2023-04-08): 2023-06-15 sentence (oldest); none (last by 2022-07-09); 2023-06-15 sentence (last by 2023-08-03).
- The other 14 trials have no archived study page up to 2023-08-03: NCT05521984 (WashU-led), 5 SWOG-led and 8 NCI-linked, all first submitted on or after 2022-08-26.
- 4 trials lack the sentence on their oldest page and carry it on their last page by 2023-08-03: NCT03598244, NCT03907488, NCT04548752 and NCT04840602.
- Every trial with an archived study page had a usable one. "WashU clause" is WashU's older wording ("or that of legally authorized representative"); "neither" means neither wording.

## What it means
- The sentence was in ClinicalTrials.gov text by November 2020: about a year and a half before the
  last archived CTEP template copy without it (2022-07-09), and nearly three years before the first
  template version dated with it (August 4, 2023). CTEP's public template is not where it started.
- SWOG-led trials carried it from registration, and none of the 25 SWOG-led trials that carry it
  today has CTEP's stock consent line (results/ctep-spread). An NCI-led trial (NCT04989283) carried
  it the day after its first submission in August 2021, and three older NCI-led trials were edited
  to carry it by mid-2022. So the wording circulated in cooperative-group and NCI protocols before
  the public template showed it. Where it was first written is not something registry pages can
  show; NCI's internal template drafts and SWOG's own protocol template are not public.
- WashU's early trials did not have it before August 2023: they changed later, as
  results/washu-switch found for WashU's trials as a whole.

## The consent-wording chain (closed)
This is the last planned test in the chain on how registry text words consent through a legally
authorized representative. Graded tests and predictions held: consent-sponsor 2 of 5,
consent-permission 5 of 5, washu-switch 3 of 5, ctep-template 4 of 4, ctep-spread 3 of 5 and
sentence-origin 4 of 4: 21 of 28 predictions held. washu-history was not graded (a gate failed).
No further test is planned. A next step, if anyone takes it: ClinicalTrials.gov's own record
history for the four trials that gained the sentence would date each edit exactly.

## Limits
- The Internet Archive captured 16 of the 30 trials' pages before August 2023; the 14 without a page were all first submitted on or after 2022-08-26, so every trial first submitted before that date was read.
- A capture date bounds when its text was live; it does not date an edit. The registry's own record history was not read.
- Up to 3 tries per page list; text matching, not reading.
- The cohort is fixed by today's text: trials that carried the sentence once and later dropped it are not in it.
- One run by AI agents, not yet checked by a person.

## Files
- sentence_origin.py 0.1.0 (sha256 489fec512f157f44b9283ea24757060b620fbf8f960611a7f80f0007d34a2607) and test_sentence_origin.py (sha256 56ea8d78278e86f0ba08903ccec799279da3b2d152f908d8260fd32c974d99cc), unchanged since the pre-registration commit; their 19 tests passed in the run.
- result.json, result.txt and sentence-origin-pages.csv (every page read, with its capture time, archive digest and sha256): the run's output, unchanged.
- test_sentence_origin_result.py re-grades every prediction from the page table and the ctep-spread table with sentence_origin 0.1.0, rebuilds the printed result, and checks every figure in this note and the hashes.
