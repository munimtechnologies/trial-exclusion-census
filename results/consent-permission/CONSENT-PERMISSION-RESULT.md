# Are the stock consent line's representative mentions real adult permissions? (result)

The pre-registered test in PREREG.md (this folder), run once on 2026-10-30. Order of events, all UTC:
the pre-registration was committed at 14:36 (commit c628762); the sample was drawn and fetched from 2026-10-30T14:56:00Z;
the 100 labels were committed at 16:20 (commit 811c6bb), before the key was opened; the grading
run started at 19:37 and fetched the labels from the main branch before building the key.
Run and written up by AI agents working for MV2 of Munim, Inc.; not yet checked by a person.
Text CC BY 4.0; code Apache-2.0.

## In short
Where a trial with the stock consent line ("Ability to understand and the willingness to sign a
written informed consent document") names a representative, guardian or surrogate, the template
owners' mentions are mostly real adult permissions and other trials' mentions mostly are not:
- NCI-linked: 29 of 40 (72.5%; 95% interval 57.2-83.9%)
- WashU-led: 16 of 20 (80.0%; 95% interval 58.4-91.9%)
- Neither: 13 of 40 (32.5%; 95% interval 20.1-48.0%)

**All five predictions hold.** By the pre-registered estimate, about 397.5 of 5,436 trials (7.3%) write down a real adult permission, and the two template owners hold 80.3% of those, against 63.8% of mentions.
Outside the two templates, about 78.3 of 3,666 Neither trials (2.1%) do.

## Gates
All passed. Sample run: S1 table and S2 published counts reproduced, S3 the API returned 100 of
100, S4 all 100 still name a path; reading.txt sha256 begins 13c9e6d8b257. Labels: L1-L3 passed
(every blind id labelled once with a valid label). The grading run checked that the labels on
main matched the local file (sha256 88af6bbc83c7f4fbaaa46b4123bc68406d704d329f749a441877bea1ae9072d7),
and that reading.txt and consent_permission.py on main were the files the sample run used. Its
rebuilt key.csv has the same 100 rows as the key the sample run wrote (compared row by row after
grading).

## Predictions
- **R1 (main): holds.** NCI-linked minus Neither is 40.0 percentage points (Newcombe 95% interval 18.21 to 56.85 points); needed at least 15 with the lower end above 0.
- **R2: holds.** NCI-linked 72.5%; needed at least 70%.
- **R3: holds.** Neither 32.5%; needed at most 60%.
- **R4: holds.** WashU-led 80.0%; needed at least 80%. It is exactly at the bound.
- **R5: holds.** Template owners hold 80.3% of estimated real adult permissions; needed at least 70%.

## Labels by group

| Group | Read | adult_permission | physical_only | minor_only | unclear | not_a_permission | path_gone |
|---|---|---|---|---|---|---|---|
| NCI-linked | 40 | 29 | 0 | 2 | 4 | 5 | 0 |
| WashU-led | 20 | 16 | 0 | 0 | 4 | 0 | 0 |
| Neither | 40 | 13 | 0 | 13 | 7 | 7 | 0 |

A third of the Neither mentions (13 of 40) are routes for minors only, in trials open to children.
Three NCI-linked records name a guardian only to say that consent may not be given through one.

## Does the result depend on the unclear records?
No. The pre-registered rule labels generic parent/guardian/representative wording in a trial open
to minors as unclear (15 records). Re-grading with the same script under the two extreme choices
(not pre-registered; reported as a check):
- All 15 unclear records read as adult permissions: NCI-linked 33 of 40 (82.5%), WashU-led 20 of 20 (100.0%), Neither 20 of 40 (50.0%); owners hold 75.7% of the estimate. All five predictions hold.
- Only the 7 unclear Neither records read as adult permissions (the case least favourable to R1): the gap is 22.5 points with the interval's lower end still above 0; owners hold 72.6%. All five hold.

## Seen while grading (not pre-registered, not graded)
The two templates are not tied one-to-one to their owners. In reading.txt:
- WashU-led trials changed wording: all 13 sampled WashU-led trials with ids before NCT06 carry the WashU clause ("or that of legally authorized representative, if applicable"), and all 7 with ids from NCT06 on carry NCI's sentence ("Legally authorized representatives may sign and give informed consent on behalf of study participants") instead.
- 3 Neither trials carry the WashU clause, and only 5 of 40 NCI-linked records carry NCI's sentence (most use other wording).
NCT ids are given in registration order, so this looks like a switch at WashU among its newest
registrations; it rests on 20 records and was not tested.

## What it means
- Mention counts understate how much of the real adult path comes from two templates (80.3% of
  the estimate against 63.8% of mentions), and overstate how often other trials write one.
- A yearly indicator of representative paths should count mentions and also read a sample of
  them by sponsor group, because the share of mentions that are real adult permissions differs
  by more than twofold between groups.
- results/consent-sponsor found that outside the templates the share of trials naming a path
  rose from 3.2% to 10.5% since 2020. This reading was not split by start period, so it cannot
  say how much of that rise is real adult permissions rather than routes for minors.

## Limits
- One AI reader, not yet checked by a person; no second reader, so no agreement measure.
- 100 records; the intervals are wide.
- Blind to the sponsor fields, not to the text: template wording can hint at the group (see
  above, though the hint is imperfect).
- R049's excerpt was cut at 4,000 characters before its path line, so it is labelled unclear.
- Today's registry text, not the 2026-10-16 text the sponsor table was built from.
- The estimate applies each group's sample share to all its mentions; the 18 trials that are
  both NCI-linked and WashU-led count at the NCI-linked share, as pre-registered.

## Files
- consent_permission.py 0.1.0 (sha256 7674ee9f942d4182ed4a1090db3a33ae418d94fb7a57115487d518c37701c24f), unchanged since the pre-registration commit.
- grade_job.py (sha256 7f39453e6a0ac8a6227e652fbfbb0f090b9426d3b20b9facef8715f8228321b0) and test_grade_job.py (sha256 6ebd85cf1b89b6bd572bc1e62e86e3e05fa6ce2346c487c81791adbdaf149463), at the repository root, byte for byte as run; their 11 tests passed in the grading run.
- sample.json, key.csv, gate.json, grade.json and grade.txt: the runs' output, unchanged.
  labels.csv, reading.txt and LABELLING-NOTES.md: committed before the key was opened.
- test_consent_permission_result.py rebuilds the key from sample.json, re-grades from key.csv and
  labels.csv, re-runs both checks above, and checks every figure in this note and the hashes.
