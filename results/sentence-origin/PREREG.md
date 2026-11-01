# Was the representative-consent sentence in registry text before CTEP's template had it? (pre-registration)

Written on 2026-11-01 (UTC), before any archived ClinicalTrials.gov page below was
opened, by AI agents working for MV2 of Munim, Inc. Text CC BY 4.0; code Apache-2.0. Not yet
checked by a person.

## Question
results/ctep-template dated the sentence

> Legally authorized representatives may sign and give informed consent on behalf of study
> participants.

into NCI CTEP's protocol templates: no archived template copy has it up to 2022-07-09, and the
first template version with it is dated August 4, 2023. results/ctep-spread then found 147 trials
carrying it in today's registry text, including 25 led by SWOG Cancer Research Network that do not
use CTEP's stock consent line at all, and 30 trials first submitted before August 4, 2023
(12 on or before 2022-07-09). Today's text cannot say whether those 30 trials carried the sentence
when they were registered or gained it later. results/washu-history set out to answer this for
three of them (the early WashU-led trials) but stopped at its time limit before reaching them and
graded nothing.

This test reads the Internet Archive's copies of the 30 trials' ClinicalTrials.gov study pages
from before August 4, 2023 and asks: was the sentence in registry text before CTEP's template
carried it, and did it enter SWOG's trials, NCI's other trials and WashU's early trials at
registration or in later edits?

## Why it is new
Web searches on 2026-10-30, 2026-10-31 and 2026-11-01 (the last for the exact sentence) found no page naming its source or dating it; the hits are IRB guidance on legally
authorized representatives in general (for example UCSF, Johns Hopkins, UVA). results/ctep-template
is the only dating found. No study found reads archived registry pages to date when a consent
route entered a sponsor's trials.

## Data
- The per-trial table results/ctep-spread/ctep-spread-trials.csv, read from this repository's main
  branch (147 rows). The **cohort** is its 30 trials with period pre or gap (first submitted on or
  before 2023-08-03): 3 WashU-led (NCT04462328, NCT04852328, NCT05521984), 10 led by SWOG Cancer
  Research Network and 17 other NCI-linked trials.
- Read in that order (WashU, then SWOG, then the rest, each by NCT id), so a time-out hits the
  least central trials last.
- For each trial, the Internet Archive's CDX index for the prefixes clinicaltrials.gov/ct2/show/<id>
  and clinicaltrials.gov/ct2/show/record/<id>, status 200 only, captures up to 2023-08-03.
  2 seconds between index queries, 4 seconds between downloads.
- Three page lists per trial, distinct pages by digest: **oldest** (each page at its first
  capture, oldest first), **newest-pre** (each page at its last capture on or before 2022-07-09,
  newest first) and **newest-early** (the same up to 2023-08-03). In each list the first usable
  page is kept, trying at most 3. A page already read (same digest) is not downloaded again.

## Measures (sentence_origin.py 0.1.0)
A page's text is its HTML with scripts, styles, comments and tags removed and entities decoded. A
page is **usable** if its text has at least 2,000 characters, names the trial's NCT id and has an
eligibility section ("Eligibility Criteria", "Inclusion Criteria", "Ages Eligible for Study" or
"Sexes Eligible for Study"). **Sentence**, **clause** and **stock line** are the patterns of
washu_switch.py 0.1.0 and ctep_template.py 0.1.0, unchanged.

## Gates (if any fails, nothing is graded)
- P0 this file, the ctep-spread table and the exact sentence_origin.py that runs are on main before
  anything is fetched (the script checks this itself).
- A1 the table has 147 distinct trials; the cohort has 30, starting with the three WashU-led
  trials above, with 10 SWOG-led and the rest NCI-linked.
- A2 at least 15 of the 30 trials have a usable page.
- A3 at least 27 of the 30 trials were read completely (both index queries answered in full, and
  all of the trial's page reading done within the 200-minute limit).
- A4 CTEP's stock consent line is found on at least one usable page (a check that eligibility text
  is being read at all).

## Predictions
- **S1 (main)** At least one cohort trial has a usable page captured on or before 2022-07-09 (its
  oldest or newest-pre page) that carries the sentence: the sentence was in registry text before
  any archived CTEP template had it. Graded only if at least 6 trials have such a page.
- **S2** Of the SWOG-led trials with a usable oldest page, at least half carry the sentence on it
  (SWOG wrote it in at registration). Graded only if at least 4 have one.
- **S3** Of the 17 other NCI-linked trials with a usable oldest page, at most half carry the
  sentence on it (most gained it in later edits). Graded only if at least 4 have one.
- **S4** results/washu-history's H2, with its page window narrowed to captures up to 2023-08-03:
  for each of NCT04462328, NCT04852328 and NCT05521984 that has a usable oldest page, that page does
  not carry the sentence. Graded only if at least 2 of the 3 have one; holds only if none of them
  shows it.

What we expect, and why: SWOG's trials carry the sentence without CTEP's stock line, and the
earliest of the 147 was first submitted in 2018, so SWOG's own template may have had it before
CTEP's did; NCI's own trials and WashU's early ones probably took it in amendments after 2023.
These are guesses written before any archived page was opened; they may fail.

## Also reported, not graded
Per trial: the three pages read (capture date and wording); the earliest page with the sentence
among all pages read; the trials whose oldest page lacks the sentence and whose newest-early page
has it (gained it before August 2023); the CDX row counts; every page read
(sentence-origin-pages.csv: trial, list, capture, digest match, marks, sha256, errors).

## Code
sentence_origin.py 0.1.0 and test_sentence_origin.py (19 tests, no network). The run happens once,
in a sealed container, and prints both files' sha256. Thresholds, paths, dates and the cohort's
shape are constants pinned by a test.

## Limits
- The Internet Archive captures some study pages and not others; trials without a usable page are
  left out, and those captured may not be typical.
- A capture date bounds when its text was live; the registry's own version history (not read
  here) would date edits exactly. An edit made and reverted between captures is missed.
- Up to 3 tries per list: a trial whose first three pages in a list are unusable counts as
  having no usable page in that list.
- The cohort is fixed by today's text: trials that carried the sentence once and later dropped it
  are not in it.
- Even if S1 holds, a sentence in registry text before mid-2022 shows it was in use earlier, not
  where it came from; NCI's internal template drafts are not public.
- Text matching, not reading.
