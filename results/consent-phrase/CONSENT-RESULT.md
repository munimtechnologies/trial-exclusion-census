# The stock consent line: how often is there another way to consent?

Read 2026-10-16. Labelled by AI agents working for MV2 of Munim, Inc.; not yet checked by a person.
Made by MV2 of Munim, Inc. with AI agents. Text and data CC BY 4.0, code Apache-2.0.

Many trials copy one inclusion item: "Ability to understand and the willingness to sign a written
informed consent document." Read alone, it keeps out adults who could take part with a legally
authorized representative (LAR), guardian or surrogate, which US rules allow when an IRB approves
it. This note counts how often that line comes with another path to consent, and reads a sample to
see how many of those mentions are real permissions. It was not pre-registered: it is a
description, not a test.

## What was counted

`consent_phrase_check.py` 0.2.0 downloaded the eligibility text of every study the
ClinicalTrials.gov search finds for the line (job consent-phrase-check-v1, 2026-10-16) and checked
the wording with a regular expression. Files: `CONSENT-PHRASE.md`, `consent-phrase.json`,
`consent-phrase-trials.csv` (one row per trial, with the snippets).

- The search found 5,473 trials; all were downloaded.
- 4,059 have the exact line; 1,377 only a near variant (the same line without "the"); 37 neither.
- Of the 4,059, 422 of 4,059 (10.4%) name a representative, guardian or surrogate anywhere in
  their eligibility text. That is a mention, not yet a permission.

## Reading the mentions

A seeded random sample of 50 of the 422 was read one by one (`consent-read.json`, rules written in
the file). A mention counts as an adult permission when the wording lets someone else consent for
the participant and the trial is adult-only (registry minimum age 18 or more).

| Mark | Trials |
|---|---|
| adult_permission | 30 |
| minor_only | 9 |
| unclear | 4 |
| not_a_permission | 6 |
| physical_only | 1 |

- Adult permission: 30 of 50, 60.0% (46.2-72.4, Wilson 95%).
- Applied to the 422: about 253 trials (195-305), 6.2% (4.8-7.5) of the 4,059 with the exact line.
- So in roughly 94% of trials that use the stock line, neither the patterns nor the reading found
  a written path for an adult who needs a representative to consent (see Limits).

The six that are not permissions: two hits are the drug octreotide LAR (NCT06663072,
NCT03057509); in two the participant is a parent or caregiver (NCT05361811, NCT05477784); one says
"consent may not be obtained by means of a legal guardian" (NCT01961063, City of Hope); and one
turns NCI's clause around, saying patients with impaired decision-making capacity who have a LAR
are not eligible (NCT06295367, ECOG-ACRIN). One NCI trial lets a LAR sign only "if the patient is
physically (not mentally) not capable of signing" (NCT06982222). These three were checked in the
registry on 2026-10-16.

## When the other path appears

| Start year | Trials with the line | Name another path | % |
|---|---|---|---|
| 2019 or earlier | 2,419 | 103 | 4.3 |
| 2020-2026 | 1,587 | 304 | 19.2 |

The rise coincides with NCI's clause for impaired decision-making capacity (IDMC). Its "will also be
eligible" wording is in 59 trials with the exact line, 53 of 59 started 2020-2023. The newer
template sentence "Legally authorized representatives may sign and give informed consent on behalf
of study participants" is in 54 trials with the exact line, 54 of 54 started 2023 or later. The
IDMC phrase appears in 139 trials with the exact line.

The newest template also drops "the" from the stock line ("willingness to sign an IRB approved
written informed consent document"), so the exact-line count misses it:
the LAR sentence is in 102 trials in all, 48 of them without the exact line.
Among the near-variant trials, 244 of 1,377 (17.7%) name a representative, guardian or
surrogate. They are read in [CONSENT-NEAR-VARIANT.md](CONSENT-NEAR-VARIANT.md): most use a
second template clause, from Washington University, and 197 of the 1,377 give an adult path.

## Limits

- One reading by AI agents, not yet checked by a person; 50 trials, so the interval is wide.
- The patterns find "representative", "guardian", "surrogate", "proxy", "next of kin" and similar.
  A path named only as "caregiver" or "family member" is missed, so the 422 is a floor for
  mentions.
- The registry keeps only the current eligibility text, and the start year is when a trial began,
  not when its wording was written.
- The sample was drawn from the exact-line trials only.

## What it means for a fix

The fix already exists and is short: one sentence after the stock line. NCI's template carries
it, and in this sample 30 of 50 trials that mention another path really do allow it. A study team
can add "Legally authorized representatives may sign and give informed consent on behalf of study
participants", where its IRB allows it, without changing anything else in the protocol.

`test_consent_read.py` recomputes every number above from the three result files and the reading.
