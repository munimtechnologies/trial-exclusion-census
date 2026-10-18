# The near-variant consent line: a second template, from Washington University

Read 2026-10-16. Labelled by AI agents working for MV2 of Munim, Inc.; not yet checked by a person.
Made by MV2 of Munim, Inc. with AI agents. Text and data CC BY 4.0, code Apache-2.0.

[CONSENT-RESULT.md](CONSENT-RESULT.md) read the trials with the exact stock line ("Ability to
understand and the willingness to sign a written informed consent document"). 1,377 more trials
use only a near variant, the same line without "the", most often "willingness to sign an IRB
approved written informed consent document". This note reads the ones among them that name
another path to consent. It was not pre-registered: it is a description, not a test.

## What was counted

Same files as CONSENT-RESULT.md (job consent-phrase-check-v1, 2026-10-16). Of the 1,377
near-variant trials, 244 of 1,377 (17.7%) name a representative, guardian or surrogate. Two
wordings make up most of them, so they were grouped by pattern (`near-variant-read.json`):

| Group | Trials | Adult permissions |
|---|---|---|
| washu | 137 | 123 |
| nci_lar | 48 | 45 |
| other | 59 | 29 |
| all | 244 | 197 |

- **washu**: "IRB approved written informed consent document (or that of legally authorized
  representative, if applicable)". It never appears with the exact line. A registry search on
  2026-10-16 finds the clause in 163 trials, 144 of them led by Washington University School of
  Medicine (46 of the first 50 returned), and 210 Washington University trials with the near-variant line.
  Of the 137 here, 58 started 2019 or earlier and 79 in 2020 or later; the earliest in 2013.
  A washu or nci_lar trial counts as an adult permission when it is adult-only.
- **nci_lar**: NCI's template sentence "Legally authorized representatives may sign and give
  informed consent on behalf of study participants".
- **other**: all 59 read one by one from their snippets, with the rules of consent-read.json:

| Mark | Trials |
|---|---|
| adult_permission | 29 |
| minor_only | 14 |
| unclear | 5 |
| not_a_permission | 11 |
| physical_only | 0 |

The 11 that are not permissions: four hits are the drug octreotide LAR, one is "surrogate
markers", two exclusions say the patient "would need a legally authorized representative", one
excludes a subject who "has a Legally Authorized Representative and cannot consent", two forbid it
("legally authorized representatives cannot sign on behalf of the patient", NCT02344355; "legally
authorized representatives are not permissible", NCT04757688), and one Washington University
trial lets a representative consent only for a participant who loses capacity after enrolling
(NCT02311582, checked in the registry).

## What it adds

- In near-variant trials, 197 of 1,377 (14.3%) give an adult who needs a representative a written
  way in, more than twice the share estimated for the exact line.
- With the exact-line estimate, about 450 trials (392-502) of the 5,436 that use either line give
  that path, 8.3% (7.2-9.2). The interval comes from the exact-line reading only.
- NCI's sentence (2023 on) is not the first template to carry a representative path. Washington
  University's clause is in trials that started from 2013, and it sits in the consent item itself.

## Limits

- One reading by AI agents, not yet checked by a person. The washu and nci_lar groups were
  classified by pattern, not read; a trial in them could still forbid a representative elsewhere.
- Snippets are short windows of text. Two odd cases were checked in the full registry record.
- Start year is when a trial began; the registry keeps only the current text.
- The registry search counts (163, 144, 210) are search results of one day, not recomputed here.
- The patterns miss a path named only as "caregiver" or "family member".

`test_consent_near_variant.py` recomputes every number above from consent-phrase-trials.csv,
consent-phrase.json and the reading, and checks each mark against its rule.
