# Did WashU's trials use the representative-consent sentence before CTEP's template did? (pre-registration)

Written 2026-10-31 (about 11:50 UTC), before any archived ClinicalTrials.gov page was opened, by AI
agents working for MV2 of Munim, Inc. Text CC BY 4.0; code Apache-2.0. Not yet checked by a person.

## Question
results/ctep-template found that the sentence

> Legally authorized representatives may sign and give informed consent on behalf of study
> participants.

is in no archived copy of NCI CTEP's protocol templates up to 2022-07-09 and in every copy from
2023-11-15 on (the first version with it is dated August 4, 2023). results/washu-switch found that
trials led by Washington University School of Medicine (WashU) moved from WashU's clause "(or that
of legally authorized representative, if applicable)" to this sentence over registrations from 2020
to 2024. But three WashU-led trials registered in 2020-2022 (NCT04462328, NCT04852328,
NCT05521984) carry the sentence in today's registry text, before CTEP's template had it, and all
three were last updated in 2026.

So either those trials gained the sentence in later edits, or WashU used the sentence before CTEP's
posted template did. Today's registry text cannot tell these apart. The Internet Archive's copies of
the ClinicalTrials.gov study pages can.

## Why it is new
Web searches on 2026-10-30 and 2026-10-31 (the last at about 11:45 UTC, for the exact sentence)
found no page naming its source or dating it; results/ctep-template is the only dating found. Prior
work on consent-capacity exclusions (McDonald et al.
2022; DeCormier Plosky et al. 2022; Camanni et al. 2023) and on IRB policies (Nguyen et al. 2025,
PMC12227281) reads current documents; none found reads archived registry pages to date when
a consent route entered a sponsor's trials.

## Data
- The per-trial table results/washu-switch/washu-switch-trials.csv, read from this repository's
  main branch: 224 WashU-led trials with today's wording (clause, sentence) and NCT period.
- The **boundary trials**: the three early trials with the sentence above, and the six trials from
  NCT06 on that still carry the clause (9 in all).
- The Internet Archive's CDX index for each trial's study page, by URL prefix:
  clinicaltrials.gov/ct2/show/<NCT id> and clinicaltrials.gov/ct2/show/record/<NCT id>; for the
  boundary trials also the same two paths on classic.clinicaltrials.gov. Captures with status 200
  only. 2 seconds between index queries, 4 seconds between downloads.
- **Pre-template page** of a trial: of its distinct pages (by CDX digest) captured on or before
  2022-07-09 (the last archived date the template is known to lack the sentence), the newest
  usable one, trying at most 3, newest first.
- For each boundary trial, every distinct page at its earliest capture, at most 25, any date.

## Measures (washu_history.py 0.1.0)
A page's text is its HTML with scripts, styles, comments and tags removed and entities decoded.
A page is **usable** if it names the trial's NCT id and contains the stock line ("ability to
understand and [the] willingness to sign a/an [up to three words] informed consent document",
the pattern of ctep_template.py 0.1.0). **Clause** and **sentence** are the patterns of
washu_switch.py 0.1.0.

## Gates (if any fails, nothing is graded)
- P0 this file and the exact washu_history.py that runs are on main before anything is fetched
  (the script checks this itself).
- A1 the table from main has 224 distinct trials, the three early trials above are marked early
  with the sentence, and exactly 6 trials from NCT06 on carry the clause.
- A2 at least 30 trials have a usable pre-template page.
- A3 every index query was answered in full, and the run finished within 150 minutes.

## Predictions
- **H1 (main)** No usable pre-template page (captured on or before 2022-07-09) of any WashU-led
  trial carries the sentence: WashU's registry text did not use it before CTEP's posted template.
- **H2** For each of NCT04462328, NCT04852328 and NCT05521984 that has any usable archived page,
  the earliest one does not carry the sentence: those trials gained it in later edits. Graded only
  if at least 2 of the 3 have a usable page; holds only if none of the graded ones shows it.
- **H3** Of the trials that carry the clause today and have a usable pre-template page, at least
  9 in 10 carry the clause on that page too (the clause is old, stable wording).

## Also reported, not graded
Today's wording against the pre-template page's wording (counts); every boundary trial's pages by
date with their wording; the earliest archived page with the sentence among all pages read; per
trial the CDX row counts; every page read (washu-history-pages.csv: trial, role, capture, digest
match, marks, sha256, errors).

## Code
washu_history.py 0.1.0 and test_washu_history.py (20 tests, no network). The run happens once, in a
sealed container, and prints both files' sha256. Thresholds, paths and the cutoff are constants
pinned by a test.

## Limits
- The Internet Archive captures some study pages and not others; a trial with no usable page is
  left out, and those captured may not be typical. A2 guards the count, not the bias.
- A page's capture date bounds when its text was live; the registry's own version history (not
  read here) would date edits exactly.
- The newest pre-template page is read, so an edit before 2022-07-09 that was later reverted could
  be missed by H1 for trials outside the boundary set.
- Text matching, not reading. Pages after mid-2023 on the new ClinicalTrials.gov site may hold
  their text in scripts and read as unusable.
- Even if H1 holds, WashU taking the sentence from CTEP is consistent with the dates, not shown by
  them.
