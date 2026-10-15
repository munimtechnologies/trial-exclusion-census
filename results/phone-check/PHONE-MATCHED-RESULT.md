# Result: telephone-delivered trials name hearing loss about 2.4 times as often

The pre-registered test of [PREREG-PHONE-MATCHED.md](PREREG-PHONE-MATCHED.md), counted on
2026-10-15 after the pre-registration was on main. The 156 counts are in
[phone-matched-counts.json](phone-matched-counts.json), and `python phone_matched.py` recomputes
every number below from them. The ratios were first worked out by hand, then checked by
`test_phone_matched.py`. CC BY 4.0.
Made by MV2 of Munim, Inc. with AI agents.

## In one paragraph

Across all sponsors, no-phase interventional trials whose interventions mention the telephone
name a hearing wording ("hearing loss", "deaf", "hard of hearing" and others) in their
eligibility criteria **2.45 times** as often as other no-phase trials of the same condition
(Mantel-Haenszel, 95% interval 2.17 to 2.75). This is more than for visual wordings (2.13) and
cognitive wordings (1.93). All 8 non-disability controls go the other way: telephone trials name
them **less** often (0.24 to 0.61 times), and "informed consent" too (0.78). Both primary
hypotheses hold. Visual wordings are close behind hearing, though, and their intervals overlap. So
the data show that telephone-delivered trials name sensory and cognitive disability far more
often than other trials, with hearing first. They do not show that the telephone singles out
hearing alone.

## The strata

| Stratum | Telephone trials | Other trials |
|---|---|---|
| ptsd | 96 | 1,178 |
| substance use | 649 | 5,642 |
| depression | 405 | 5,089 |
| pain | 385 | 18,804 |
| cardiometabolic | 1,363 | 23,430 |
| other | 4,722 | 148,586 |
| **all six** | **7,620** | **202,729** |

All twelve trial counts equal the stratum sizes fixed in the pre-registration.

## The ratios

Times as often in telephone trials as in other trials of the same condition. "Expected" is the
number of telephone trials that would name the phrase if they named it as often as the other
trials of their stratum. Every control has at least 5 expected, so none is left out.

| Phrase | Kind | Telephone matches | Expected | Matched (MH) | 95% interval | Unmatched |
|---|---|---|---|---|---|---|
| hearing (all wordings) | family | 294 | 120.4 | **2.45** | 2.17-2.75 | 2.44 |
| visual (all wordings) | family | 195 | 91.7 | 2.13 | 1.85-2.47 | 2.12 |
| cognitive (all wordings) | family | 1,531 | 796.7 | 1.93 | 1.84-2.02 | 2.07 |
| pregnant | control | 1,662 | 2,737.8 | 0.61 | 0.58-0.63 | 0.61 |
| migraine | control | 21 | 38.0 | 0.56 | 0.37-0.86 | 0.53 |
| hernia | control | 33 | 67.8 | 0.49 | 0.35-0.69 | 0.40 |
| osteoporosis | control | 34 | 78.7 | 0.43 | 0.31-0.60 | 0.34 |
| celiac | control | 31 | 77.4 | 0.40 | 0.28-0.57 | 0.39 |
| hepatitis | control | 66 | 194.8 | 0.34 | 0.27-0.43 | 0.34 |
| allergy | control | 321 | 1,278.5 | 0.25 | 0.22-0.28 | 0.24 |
| claustrophobia | control | 31 | 128.5 | 0.24 | 0.17-0.34 | 0.26 |
| informed consent | reference | 2,009 | 2,584.9 | 0.78 | 0.75-0.81 | 0.79 |

By stratum (telephone share over other share):

| Family | ptsd | substance use | depression | pain | cardiometabolic | other |
|---|---|---|---|---|---|---|
| hearing | 1.46 | 1.85 | 2.07 | 2.14 | 3.26 | 2.45 |
| visual | 1.75 | 0.67 | 1.91 | 2.51 | 2.18 | 2.25 |
| cognitive | 0.70 | 1.22 | 1.18 | 2.10 | 2.54 | 2.10 |

Hearing is above 1 in all six strata. In the two smallest, the counts are small (5 and 16
telephone matches).

## The hypotheses

- **HP1 holds.** The hearing family's interval, 2.17 to 2.75, lies above 1.
- **HP2 holds.** Hearing's matched ratio (2.45) is larger than visual's (2.13) and than every
  control's (largest: pregnant, 0.61). There are 9 rivals, so by chance hearing would come first
  1 time in 10. This is a ranking, as pre-registered, not a p-value. Hearing's lead over visual
  is small, and the two intervals overlap (2.17-2.75 and 1.85-2.47).
- **S1.** The three families rank above all 8 controls: rank sum 30 of a possible 30, exact
  one-sided p = 1/165 = 0.0061.
- **S2** (reading 40 hearing mentions outside the VA) is not done yet. It will be reported in
  PHONE-HEARING-READ.md whichever way it goes.

## What it means, and what it does not

- **Not a VA effect.** Leaving out trials led by the VA (exploratory, not pre-registered; counts
  in [phone-matched-nonva-counts.json](phone-matched-nonva-counts.json)) removes 200 telephone
  trials and 15 of their hearing matches. The hearing ratio barely moves: **2.41** (2.14 to 2.72;
  unmatched 2.40).
- **Not fuller criteria.** Telephone trials name every control and "informed consent" less often
  than other trials of their condition, so their criteria are, if anything, shorter. The
  disability families rise against that.
- **Hearing is first, not alone.** The pre-registration reasoned that the telephone needs
  hearing, not sight, so visual should not rise. It did rise, to 2.13. One likely reason, known in
  advance: the registry's search treats "phone" as "telephone", so the exposure also takes in
  mobile-phone apps and text messages, which need sight. The S2 reading checks how often the
  hearing items themselves name the telephone.
- **Mentions, not hand-checked exclusions.** A hearing wording can appear in an inclusion
  criterion or a list of accommodations. The 20 VA hearing mentions read so far
  ([VA-HEARING-READ.md](../sponsor-check/VA-HEARING-READ.md)) all shut people out, and S2 reads
  40 more.
- **Matched on condition only.** Telephone trials may differ from other trials in age, design or
  setting. The "other" stratum is large and mixed. Nothing here says whether any exclusion is
  justified for its study.

## Why it matters

The fixes for telephone-delivered studies are well known and cheap: captioned telephone, relay
services such as 711, text or chat, video with captions, and sign language interpreters. If a
study's procedures can be adapted, people with hearing loss do not need to be excluded. These
results say where to look first: telephone-delivered trials name hearing loss in their criteria
about 2.4 times as often as other trials of the same condition, across sponsors.

## Prior art

A web search on 2026-10-15 found single protocols that exclude people with hearing loss because
the study runs by telephone (NCT03609658: "due to phone interventions"). It found no
registry-wide comparison of telephone-delivered trials with other trials, and no matched or
pre-registered one.

## Repeat it

```
python phone_matched.py                                     # from the saved counts
python phone_matched.py --fetch --json phone-matched.json   # counted again (156 small requests)
```

Counts change as records are added to the registry, so a later count will differ a little.
