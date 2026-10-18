# Result: within telephone trials, naming a phone goes with naming hearing loss, mostly in the same item

Counted 2026-10-16 as fixed in [PREREG-PHONE-REQUIREMENT.md](PREREG-PHONE-REQUIREMENT.md), which
was committed before any phrase was counted. Counts: [phone-requirement-counts.json](phone-requirement-counts.json)
(156 counts plus the 4 wording checks); ratios and verdicts: [phone-requirement.json](phone-requirement.json);
S2 reading list: [s2-reading-list.json](s2-reading-list.json); pattern marks: [s2-marks.json](s2-marks.json);
the reading: [phone-requirement-read.json](phone-requirement-read.json).
`test_phone_requirement_result.py` recomputes every number below from those files. CC BY 4.0.
Made by MV2 of Munim, Inc. with AI agents. Labelled by AI agents working for MV2; not yet checked by a person.

## In short

Among non-VA telephone-delivered no-phase trials, those whose criteria name a phone name a hearing
wording 2.58 times (2.04-3.24) as often as those whose criteria don't, matched on condition. Hearing
is singled out: visual wording rises 1.62 times and no kept control more than 1.08 times. But the
reading rule fixed in advance applies: in 12 of 20 trials read, the hearing item itself names the
phone or calls ("hearing impairments that preclude use of the telephone"). So the link is mostly the
hearing exclusion being written as a phone exclusion, not a separate phone requirement that brings a
hearing item with it.

For practice the reading points one way: in these trials the barrier written down is the channel.
A person who "cannot hear on the telephone" can often take part by captioned telephone, 711 relay,
text or captioned video, so these items are where an alternative could be offered instead of an
exclusion.

## Counts

On the counting day the base had 7,421 trials (7,420 when the stratum sizes were fixed; one trial
was added to "other"), and 1,890 name a phone (25.5%).

| Stratum | Phone named | Not named |
|---|---|---|
| ptsd | 10 | 64 |
| substance use | 232 | 383 |
| depression | 94 | 295 |
| pain | 76 | 296 |
| cardiometabolic | 382 | 949 |
| other | 1,096 | 3,544 |

| Phrase | Kind | Phone-arm matches | Expected | Matched (MH), 95% interval |
|---|---|---|---|---|
| hearing (all wordings) | family | 128 | 49.7 | 2.58 (2.04-3.24) |
| visual (all wordings) | family | 64 | 39.8 | 1.62 (1.20-2.18) |
| cognitive (all wordings) | family | 405 | 354.5 | 1.14 (1.03-1.27) |
| hernia | control | 8 | 7.4 | 1.08 (0.49-2.40) |
| pregnant | control | 434 | 420.9 | 1.03 (0.93-1.13) |
| osteoporosis | control | 7 | 8.1 | 0.85 (0.37-1.97) |
| allergy | control | 69 | 87.3 | 0.77 (0.59-1.01) |
| hepatitis | control | 11 | 17.9 | 0.62 (0.33-1.18) |
| claustrophobia | control | 5 | 9.6 | 0.59 (0.24-1.42) |
| celiac | control | 5 | 8.9 | 0.56 (0.22-1.46) |
| informed consent | reference | 505 | 506.7 | 0.99 (0.91-1.08) |

Migraine was left out of HP2 and S1 as fixed in advance (4.9 phone-arm matches expected, fewer than 5).
Per-stratum and unmatched ratios are in phone-requirement.json.

## Hypotheses

- **HP1 (primary): holds.** The hearing family's matched interval, 2.04-3.24, lies above 1.
- **HP2 (primary): holds.** Hearing's ratio is above visual's and every kept control's (8 rivals;
  if nothing set hearing apart it would come first 1 time in 9).
- **S1 (secondary):** the three families against 7 kept controls, rank sum 27.0, p = 0.0083.
- **S2 (secondary, reading):** (a) an inclusion item names a phone in 13 of 20 (predicted at least
  12: met). (b) the hearing item itself names a phone or calls in 12 of 20. The pre-registration said
  that at least 11 of 20 would make HP1 "mostly the hearing items' own wording, not a separate
  requirement", and that is how it is described here.

The 20 were read one by one against the two rules, and every mark agrees with phone_marks 0.1.0's
pattern marks (40 of 40). NCT03060096 was also read for PHONE-HEARING-READ.

| Trial | (a) requirement | (b) phone-tied |
|---|---|---|
| NCT06732141 | yes | yes |
| NCT04692519 | yes | no |
| NCT00901277 | no | yes |
| NCT05685251 | no | no |
| NCT00371969 | no | yes |
| NCT03060096 | yes | yes |
| NCT05242575 | yes | no |
| NCT00006253 | no | yes |
| NCT03308071 | yes | yes |
| NCT05285163 | yes | yes |
| NCT03801174 | yes | no |
| NCT02129569 | no | yes |
| NCT02692560 | yes | yes |
| NCT04492527 | yes | no |
| NCT05562037 | no | yes |
| NCT04275830 | yes | no |
| NCT03053245 | yes | no |
| NCT07823257 | yes | no |
| NCT02953080 | yes | yes |
| NCT03890471 | no | yes |

Both marks in 6, a separate phone requirement with a hearing item that doesn't name the phone in 7,
a phone-tied hearing item only in 6, neither in 1.

## Exploratory (not pre-registered)

- In 6 of 20 the hearing item is the only item that names a phone: the trial is in the phone arm
  because of how its hearing item is worded.
- 3 of the 7 trials without an inclusion phone item shut out people without a phone in an exclusion
  item instead ("does not have access to a telephone"). Counting those, a written phone-access
  condition appears in 16 of 20.
- One more hearing item is tied to the study's device in other words (NCT05242575: hearing audio on a
  mobile device), so 13 of 20 tie hearing to the delivery channel.
- In PHONE-HEARING-READ the hearing item named the phone in 4 of 20 telephone trials. The two
  readings sample different groups: this one only takes trials whose criteria name a phone, which
  phone-worded hearing items put there by construction.

## Limits

- One counting day, one reader (AI agents working for MV2); no person has checked the reading.
- Mentions anywhere in the criteria; S2 reads 20 of the 128 phone-arm hearing trials, in API order,
  not a random sample.
- Matching is on condition only. The comparison is within telephone trials, so it says nothing about
  why telephone trials differ from other trials.
- The registry search expands synonyms, and its counts change as records are added.

## Repeat it

```
python phone_requirement.py --fetch --json phone-requirement.json   # 160 small requests
python phone_marks.py s2-reading-list.json --json s2-marks.json
python -m unittest -v test_phone_requirement_result
```
