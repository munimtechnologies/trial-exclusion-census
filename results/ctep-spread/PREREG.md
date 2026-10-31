# Who uses CTEP's representative-consent sentence, registry-wide? (pre-registration)

Written 2026-10-31 (about 16:45 UTC), before any search below was run, by AI agents working for
MV2 of Munim, Inc. Text CC BY 4.0; code Apache-2.0. Not yet checked by a person.

## Question
results/ctep-template found that NCI CTEP's protocol templates added the sentence

> Legally authorized representatives may sign and give informed consent on behalf of study
> participants.

in a version dated after June 13, 2022 and no later than August 4, 2023. results/consent-sponsor
found that trials linked to the National Cancer Institute (NCI) or led by Washington University
School of Medicine (WashU), the two template owners, hold 63.8% of trials naming a consent
representative among 5,436 trials with CTEP's stock consent line. results/consent-phrase counted
102 trials with the sentence in that frame on 2026-10-16, but no one has asked who sponsors them,
or looked outside the frame.

This test finds every ClinicalTrials.gov trial whose eligibility text carries the sentence today,
whoever sponsors it, and asks whether the sentence has spread beyond the template owners' trials:
to cancer centres and other sponsors that copy CTEP's template without listing NCI.

## Why it is new
Web searches on 2026-10-30 and 2026-10-31 (the last at about 16:40 UTC, for the exact sentence)
found no page naming the sentence's source, dating it or counting its users; regulatory guidance
(FDA, 45 CFR 46.116) describes consent by a legally authorized representative in general terms.
Prior work on consent-capacity exclusions (McDonald et al. 2022; DeCormier Plosky et al. 2022;
Camanni et al. 2023) and on IRB policies (Nguyen et al. 2025, PMC12227281) does not trace one
template sentence across a registry by sponsor and registration date.

## Data
- **Recall anchors:** results/consent-phrase/consent-phrase-trials.csv at commit c4c0ded (5,473
  rows, registry data of 2026-10-16): the trials with nci_lar_may_sign = True.
- **Search:** three eligibility-text searches on the ClinicalTrials.gov API v2 (query.term), each
  read in full: `AREA[EligibilityCriteria]("may sign and give informed consent")`,
  `AREA[EligibilityCriteria]("legally authorized representatives may sign")` and
  `AREA[EligibilityCriteria]("legally authorized representative" AND "sign and give")`. Fields:
  NCT id, eligibility text, first-submitted date, lead sponsor and class, collaborators.
- The anchors are also fetched by id, to check recall against their current text.

## Measures (ctep_spread.py 0.1.0)
- A trial **carries the sentence** if its current eligibility text (backslash escapes removed,
  spaces collapsed) matches the SENTENCE pattern of washu_switch.py 0.1.0 (it allows "legal"
  for "legally", an "(LAR)" after "representatives" and "written" before "informed").
- **Stock line** and **WashU clause** are the STOCK and CLAUSE patterns of ctep_template.py 0.1.0.
- **Groups**, as in consent_sponsor.py 0.1.0: **NCI-linked** if the lead sponsor or any
  collaborator is exactly "National Cancer Institute (NCI)" (case and outer spaces ignored);
  **WashU-led** if the lead sponsor is "Washington University School of Medicine"; **Neither**
  otherwise. An NCI-funded trial that does not list NCI counts as Neither.
- **Period** by the registry's first-submitted date: **pre** on or before 2022-07-09 (the last
  archived date CTEP's template is known to lack the sentence), **post** on or after 2023-08-04
  (the first template version date with it), **gap** between, **none** if no full date.

## Gates (if any fails, nothing is graded)
- P0 this file and the exact ctep_spread.py that runs are on main before anything is searched
  (the script checks this itself).
- A1 the anchor table has 5,473 rows, an nci_lar_may_sign column, and at least 90 anchors.
- A2 every search was read in full (studies received = the API's totalCount).
- A3 at least 80 anchors still carry the sentence today, and at least 95% of those are among the
  trials found by the searches.

## Predictions
- **R1 (main)** Of trials carrying the sentence and first submitted in the post period, at least
  25% are Neither: the sentence has spread beyond the template owners' trials. Graded only if at
  least 40 post-period trials carry it.
- **R2** Of Neither trials carrying the sentence that have a first-submitted date, at most 10% were
  first submitted in the pre period.
- **R3** At most 5% of all trials carrying the sentence have an industry lead sponsor.
- **R4** At least 80% of Neither trials carrying the sentence also carry CTEP's stock consent line
  (the sentence travels with the template, not on its own).
- **R5** Neither trials carrying the sentence have at least 10 distinct lead sponsors (case
  ignored).
- R2, R4 and R5 are graded only if at least 15 Neither trials with a first-submitted date carry
  the sentence.

What we expect, and why: the stock consent line is used well beyond NCI's own trials (3,666 of
5,436 frame trials are Neither), so trials written from a 2023-or-later CTEP template by cancer
centres that do not list NCI should carry the sentence too. These are guesses written before any
count; they may fail.

## Also reported, not graded
Counts by group and period, and by first-submitted year; each search's total and how many of its
trials carry the sentence; the anchors missed; the 15 commonest Neither lead sponsors
(organisations only); the earliest first-submitted date per group; how many sentence trials lie
outside the 2026-10-16 frame; how many carry the WashU clause; counts by lead-sponsor class; a
per-trial table (ctep-spread-trials.csv: NCT id, first-submitted date, period, group, lead sponsor
and class, stock line, clause, in frame, anchor, which searches found it).

## Code
ctep_spread.py 0.1.0 and test_ctep_spread.py (21 tests, no network). The run happens once, in a
sealed container, and prints both files' sha256. Thresholds, searches, dates and the anchor commit
are constants pinned by a test.

## Limits
- The registry holds only current text: a trial first submitted before 2023 may have gained the
  sentence in a later edit (results/washu-history tests this for WashU's trials). The
  first-submitted date bounds when the trial began, not when its wording was written.
- NCI-linked counts only trials that list NCI; Neither includes NCI-funded trials that do not, so
  R1 measures spread beyond trials that name the owners, not beyond NCI funding.
- Search recall is checked only against the anchors, which all come from the stock-line frame;
  trials outside it with unusual wording could be missed.
- Text matching, not reading: a trial carrying the sentence might still restrict or forbid
  representative consent elsewhere in its text (results/consent-permission found such cases).
