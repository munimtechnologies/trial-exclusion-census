# Paths the patterns miss: none found

[CONSENT-RESULT.md](CONSENT-RESULT.md) counts a trial with the stock consent line as having a
representative path only if its criteria name a representative, guardian or surrogate. A path
written another way ("a family member may sign") would be missed. `consent_missed.py` 0.1.0
(run 2026-10-16) looked for that: among the 3,637 trials with the exact stock line and none of
those words, 32 name a caregiver, family member, relative, spouse or partner in a sentence about
consent or signing (30 of them adult-only). All 32 were read by eye
([consent-missed-read.json](consent-missed-read.json); snippets in
[consent-missed.json](consent-missed.json)).

| What the sentence does | Trials |
|---|---|
| Names a partner in a contraception item that runs from the time of consent | 26 |
| Enrols a caregiver or care-partner, who signs consent for themself | 4 |
| Has a family member meet the team before the participant signs | 2 |
| Lets another person consent for the participant | 0 |

So none of the 32 is a missed path, and the estimate in CONSENT-RESULT.md stands: the patterns
did not undercount adult representative paths through other wording for family or caregivers.

Limits: this only finds wordings that name one of those people near "consent" or "sign"; a
path written with none of them (for example "consent may be obtained per institutional policy")
would still be missed. Not pre-registered. Read by AI agents working for MV2; not yet checked by a
person. `test_consent_missed_read.py` recomputes the table and checks each label against its
snippets. CC BY 4.0. Made by MV2 of Munim, Inc. with AI agents.
