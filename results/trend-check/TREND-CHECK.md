# Is the rise real? A check with the registry's own search

**Pre-registered result (2026-10-15, section 5).** The test fixed in advance in
[PREREG-v0.3.md](PREREG-v0.3.md), with 23 controls (12 never counted before), confirms section 4:
in no-phase trials the three disability families rose more than every control kept by the
pre-registered rule (p = 0.0045), and in the other trials they did not stand out (p = 0.45).

**Correction (2026-10-15, trend_check 0.2.0).** The first version of this check compared the
disability phrases with common control phrases (pregnancy is named by half of all trials,
allergy by a third). A phrase that common cannot triple, so a flat control proved less than
it said. Section 4 repeats the test with eight rare controls, which start as rare as the
disability phrases, and with every wording of each disability pooled. The result is narrower:
**in no-phase trials (behavioural, device and procedure studies, now 65% of starts) cognitive,
hearing and visual exclusions rose faster than most controls (exact rank test p = 0.019). In
the other trials, mostly drug trials, they did not stand out from the controls (p = 0.33).**
Sections 1 to 3 are the first version, unchanged; the sentences they get wrong are marked.

The census found that the share of trials with a disability exclusion rose from 11.5-14.1% for
2000-2008 starts to 24.9% for 2025 starts (v0.1.1 rules). Two other explanations could produce
such a rise without any change in who is excluded: eligibility criteria could simply have grown
longer, so every kind of exclusion is named more often, or the mix of trials could have shifted
toward no-phase studies (behavioural, device and procedure trials), which exclude more.

This check does not use the census rules at all. It asks the ClinicalTrials.gov search how many
interventional studies that started in a year name a phrase anywhere in their eligibility
criteria, for disability phrases and for control phrases that are not about disability.
If criteria had only grown longer, the controls would rise too.

All counts were taken from the API v2 on **2026-10-15**. Each is one query of this form, so
anyone can repeat it (`trend_check.py` runs them all):

```
https://clinicaltrials.gov/api/v2/studies?countTotal=true&pageSize=1&fields=NCTId&query.term=
  AREA[StudyType]INTERVENTIONAL AND AREA[StartDate]RANGE[2025-01-01,2025-12-31]
  AND AREA[EligibilityCriteria]"hearing loss"
```

## 1. Share of trials that name each phrase, by start year

| Start year | Trials | cognitive impairment | dementia | hearing loss | wheelchair | pregnant | hepatitis | allergy | informed consent |
|---|---|---|---|---|---|---|---|---|---|
| 2008 | 11,900 | 235 (1.97%) | 393 (3.30%) | 93 (0.78%) | 45 (0.38%) | 6,037 (50.7%) | 1,499 (12.6%) | 3,947 (33.2%) | 4,618 (38.8%) |
| 2012 | 15,027 | 392 (2.61%) | 590 (3.93%) | 143 (0.95%) | 52 (0.35%) | 7,565 (50.3%) | 1,958 (13.0%) | 4,849 (32.3%) | 6,193 (41.2%) |
| 2016 | 20,370 | 759 (3.73%) | 856 (4.20%) | 273 (1.34%) | 93 (0.46%) | 9,972 (49.0%) | 2,630 (12.9%) | 6,118 (30.0%) | 8,379 (41.1%) |
| 2020 | 23,595 | 937 (3.97%) | 1,004 (4.26%) | 387 (1.64%) | 93 (0.39%) | 11,816 (50.1%) | 3,406 (14.4%) | 7,623 (32.3%) | 10,281 (43.6%) |
| 2025 | 30,920 | 2,343 (7.58%) | 1,597 (5.17%) | 754 (2.44%) | 119 (0.38%) | 14,838 (48.0%) | 3,941 (12.7%) | 9,640 (31.2%) | 14,665 (47.4%) |
| **2025 / 2008** | | **3.84x** | **1.56x** | **3.12x** | **1.02x** | **0.95x** | **1.01x** | **0.94x** | **1.22x** |

The three control exclusions stayed flat from 2008 to 2025, while "cognitive impairment" became
3.8 times as common and "hearing loss" 3.1 times. "Informed consent" rose 1.2 times, so criteria
did become somewhat fuller. "Wheelchair" did not change, and "dementia" rose 1.6 times.
*(Corrected in section 4: these controls are too common to show a rise; rare controls rose 1.0
to 2.4 times. Since 0.2.0 "informed consent" is a reference, not a control, because consent
capacity is itself one of the census categories.)*

## 2. The shift to no-phase trials

No-phase trials were 29.2% of interventional starts in 2008 (3,474) and 64.7% in 2025 (20,003).
So each phrase was also counted within no-phase trials (`AREA[Phase]NA`) and within all other
trials (the total minus no-phase; this also holds the few trials with no phase recorded).

| Phrase | No-phase 2008 | No-phase 2025 | Ratio | Other 2008 | Other 2025 | Ratio |
|---|---|---|---|---|---|---|
| cognitive impairment | 123 of 3,474 (3.54%) | 1,959 of 20,003 (9.79%) | **2.77x** | 112 of 8,426 (1.33%) | 384 of 10,917 (3.52%) | **2.65x** |
| hearing loss | 45 (1.30%) | 644 (3.22%) | **2.49x** | 48 (0.57%) | 110 (1.01%) | **1.77x** |
| pregnant (control) | 1,287 (37.0%) | 7,791 (38.9%) | 1.05x | 4,750 (56.4%) | 7,047 (64.6%) | 1.15x |
| allergy (control) | 658 (18.9%) | 3,796 (19.0%) | 1.00x | 3,289 (39.0%) | 5,844 (53.5%) | 1.37x |

Part of the overall 3.8x rise of "cognitive impairment" comes from the move to no-phase trials,
but within each group it still rose about 2.7 times. In no-phase trials the controls did not
move. In phased and other trials the criteria did grow longer (allergy 1.37x, pregnancy 1.15x),
and "cognitive impairment" still rose about twice as fast as either. For "hearing loss" in those
trials the gap over the controls is small (1.77x against 1.37x), so that part is weak evidence.
*(Corrected in section 4: pooled over all its wordings, the cognitive rise is 1.7x in each
group, not 2.7x. In the other trials that is inside the range of the rare controls.)*

## 3. Without the trials that study the condition itself

A phrase in the criteria can name the population being studied ("adults with mild cognitive
impairment") rather than an exclusion. So the two phrases that rose most were counted again
without trials whose conditions match (`NOT AREA[ConditionSearch](...)`):

| Phrase | Left out | 2008 | 2025 | Ratio |
|---|---|---|---|---|
| cognitive impairment | cognitive OR dementia OR alzheimer | 187 of 11,900 (1.57%) | 1,969 of 30,920 (6.37%) | **4.05x** |
| hearing loss | hearing OR deafness OR tinnitus OR ear | 80 (0.67%) | 651 (2.11%) | **3.13x** |

The rise is at least as large outside the trials of those conditions, which is where a mention
is most likely an exclusion.

## 4. A harder test: rare controls and pooled wordings (added 2026-10-15)

Two flaws in sections 1 to 3. First, the disability phrases are rare (0.2% to 2% of 2008 starts)
and the controls common (13% to 51%), and a rare phrase has room to grow that a common one does
not. Second, one wording can replace another: the share naming "cognitive impairment" can rise
because fewer trials write "dementia" or "mental retardation", with nobody new excluded.

So eight **rare controls** were added: phrases not about disability that 0.2% to 1.4% of 2008
starts name (gout, psoriasis, tattoo, migraine, osteoporosis, claustrophobia, lactose
intolerance, sickle cell). They were chosen before any of their counts were fetched. Each
disability was also counted as a **family**: one OR query over its wordings, so a trial counts
once whichever words it uses. The visual family leaves out bare "blind", because the search
matches it in "double-blind" and "blind loop" (checked on 2025 records, e.g. NCT06800404,
NCT06486883).

The search also expands some terms by itself. "Intellectual disability" and "mental
retardation" return exactly the same counts (136 in 2008, 437 in 2025), so it treats them as one
concept. Shares here are of concepts as the registry search sees them, not literal strings.

### Rare controls, 2008 and 2025 starts

| Phrase | All 2008 | All 2025 | Ratio | No-phase 2008 | No-phase 2025 | Ratio | Other 2008 | Other 2025 | Ratio |
|---|---|---|---|---|---|---|---|---|---|
| gout | 63 (0.53%) | 160 (0.52%) | 0.98 | 14 (0.40%) | 92 (0.46%) | 1.14 | 49 (0.58%) | 68 (0.62%) | 1.07 |
| psoriasis | 159 (1.34%) | 604 (1.95%) | 1.46 | 25 (0.72%) | 161 (0.80%) | 1.12 | 134 (1.59%) | 443 (4.06%) | **2.55** |
| tattoo | 35 (0.29%) | 219 (0.71%) | **2.41** | 8 (0.23%) | 127 (0.63%) | **2.76** | 27 (0.32%) | 92 (0.84%) | **2.63** |
| migraine | 98 (0.82%) | 316 (1.02%) | 1.24 | 29 (0.83%) | 227 (1.13%) | 1.36 | 69 (0.82%) | 89 (0.82%) | 1.00 |
| osteoporosis | 123 (1.03%) | 370 (1.20%) | 1.16 | 50 (1.44%) | 284 (1.42%) | 0.99 | 73 (0.87%) | 86 (0.79%) | 0.91 |
| claustrophobia | 124 (1.04%) | 528 (1.71%) | 1.64 | 50 (1.44%) | 334 (1.67%) | 1.16 | 74 (0.88%) | 194 (1.78%) | 2.02 |
| lactose intolerance | 48 (0.40%) | 134 (0.43%) | 1.07 | 9 (0.26%) | 94 (0.47%) | 1.81 | 39 (0.46%) | 40 (0.37%) | 0.79 |
| sickle cell | 66 (0.55%) | 186 (0.60%) | 1.08 | 18 (0.52%) | 83 (0.41%) | 0.80 | 48 (0.57%) | 103 (0.94%) | 1.66 |

With the three common controls (pregnant 0.95 / 1.05 / 1.15, allergy 0.94 / 1.00 / 1.37, and
hepatitis 1.01 / 0.62 / 1.96: no-phase 129 (3.71%) to 464 (2.32%), other 1,370 (16.3%) to 3,477
(31.8%)) that makes 11 controls. Their ratios run from 0.94 to 2.41 over all trials (median
1.08), 0.62 to 2.76 in no-phase trials (median 1.12) and 0.79 to 2.63 in the other trials
(median 1.37). So a phrase that has nothing to do with disability can rise 2.5 times or more:
tattoo exclusions in every group, psoriasis and hepatitis in drug trials.

### Disability families, 2008 and 2025 starts

| Family | All 2008 | All 2025 | Ratio | No-phase 2008 | No-phase 2025 | Ratio | Other 2008 | Other 2025 | Ratio |
|---|---|---|---|---|---|---|---|---|---|
| cognitive (all wordings) | 726 (6.10%) | 4,040 (13.07%) | 2.14 | 311 (8.95%) | 3,110 (15.55%) | 1.74 | 415 (4.93%) | 930 (8.52%) | 1.73 |
| hearing (all wordings) | 98 (0.82%) | 778 (2.52%) | 3.06 | 49 (1.41%) | 666 (3.33%) | 2.36 | 49 (0.58%) | 112 (1.03%) | 1.76 |
| visual (all wordings) | 61 (0.51%) | 577 (1.87%) | 3.64 | 29 (0.83%) | 513 (2.56%) | 3.07 | 32 (0.38%) | 64 (0.59%) | 1.54 |

The wordings: cognitive = "cognitive impairment", "dementia", "mental retardation",
"intellectual disability", "cognitively impaired", "cognitive deficit", "cognitive
dysfunction"; hearing = "hearing loss", "deaf", "deafness", "hearing impairment", "hard of
hearing", "hearing impaired"; visual = "visual impairment", "low vision", "vision loss",
"visually impaired", "legally blind".

Single phrases counted on the same day, for reference: "visual impairment" 47 (0.39%) to 536
(1.73%), 4.39x (no-phase 3.96x, other 1.69x); "aphasia" 30 (0.25%) to 290 (0.94%), 3.72x
(no-phase 2.23x, other 4.99x from only 15 trials in 2008); "unable to read" 24 (0.20%) to 150
(0.49%), 2.41x; "intellectual disability" 136 (1.14%) to 437 (1.41%), 1.24x.

### Families against controls

An exact one-sided rank-sum test asks how often three of the 14 ratios picked at random would
rank as high as the three families do (`trend_check.rank_test`, all 364 ways counted):

| Trials | Families | Controls (11) | Rank sum of families | p |
|---|---|---|---|---|
| All | 2.14, 3.06, 3.64 | 0.94 to 2.41, median 1.08 | 38 of a possible 39 | 0.0055 |
| No-phase | 1.74, 2.36, 3.07 | 0.62 to 2.76, median 1.12 | 36 | **0.019** |
| Other | 1.54, 1.73, 1.76 | 0.79 to 2.63, median 1.37 | 26 (22.5 expected) | 0.33 |

## What this shows and what it does not

- **No-phase trials:** the evidence holds. Cognitive, hearing and visual exclusions rose 1.7 to
  3.1 times from 2008 to 2025 starts, above all but one or two of 11 non-disability controls.
- **Other (mostly drug) trials:** no evidence of a disability-specific rise. The families rose
  1.5 to 1.8 times, close to the controls' median (1.37) and below the four controls that rose
  most (hepatitis, claustrophobia, psoriasis, tattoo).
- **All trials together**, the families stand out most (p = 0.0055), but that test includes the
  shift to no-phase trials, which exclude more. The shift is a real change in which trials
  people can join, but it is a change in the kind of trial, not in how a given kind treats
  disabled people.
- **Wording change is real.** Pooling all cognitive wordings cuts the cognitive rise from 3.8x to
  2.1x overall, and from about 2.7x to 1.7x within each group of trials. The single phrase
  "cognitive impairment" overstated it.
- **The earlier claim was too strong.** Sections 1 and 2 said the rise was "not explained by
  criteria growing longer". With rare controls that holds only for no-phase trials.
- These are counts of mentions, not of exclusions. A phrase can sit in the inclusion criteria,
  in an exception ("except mild hearing loss"), or describe the study population. The census
  rules and their hand checks measure exclusion.
- Exploratory, not pre-registered: the families' wordings and the controls were chosen this
  run, with only two start years compared, and each phrase counts as one value whatever its
  size. The rank test treats the 14 ratios as exchangeable, which is an assumption. A larger,
  pre-registered set of controls and every start year would be a stronger test (section 5).
- The registry's search expands some terms (see above) and may match close variants. It is the
  same search for every year, so comparisons between years hold.
- 2025 trials are still being registered late, and the counts change daily. These are the
  numbers of 2026-10-15. Full counts, not a sample, so there is no sampling error; the
  uncertainty is in what a mention means.

## 5. The pre-registered test (added 2026-10-15)

[PREREG-v0.3.md](PREREG-v0.3.md) fixed the phrase lists, the 20-match rule and the hypotheses
before counting. All counts were then fetched in one run; those already in section 4 came back
the same. The full tables are in [PREREG-v0.3-RESULT.md](PREREG-v0.3-RESULT.md), the counts in
[prereg-v0.3-counts.json](prereg-v0.3-counts.json), and `prereg_v03.py` recomputes every test.

| Test | Controls | p | Section 4 (exploratory, 11 controls) |
|---|---|---|---|
| **H1: no-phase**, families rank above controls | 9 (14 left out by the 20-match rule) | **0.0045**: holds | 0.019 |
| **H2: other**, no disability-specific rise | 22 (hemorrhoids left out) | **0.45**: holds | 0.33 |
| All trials (reported) | 23 | 0.005 | 0.0055 |
| No-phase, every control kept (sensitivity, not pre-registered) | 23 | 0.020 | |
| VA-led against registry, no-phase only (secondary) | 23 | 0.0015 | none counted before |

- In no-phase trials the families rose 1.74, 2.36 and 3.07 times; the largest control kept rose
  1.63 times (hernia).
- The 20-match rule was written when the 2008 no-phase counts of the 11 old controls were
  already known, and it drops tattoo, the old test's top control. With every control kept H1
  still holds (p = 0.020), but three rare controls (tattoo, celiac, endometriosis) then rise
  as fast as the hearing family.
- In drug trials two new controls rose far more than any family: vitiligo 16 times and shingles 4
  times. Controls can move for reasons that have nothing to do with disability, which is why the
  test ranks the families against many controls rather than one.
- Still to come: the per-year secondary (every start year 2008-2025 and log-share slopes).

Counts by MV2 of Munim, Inc. with AI agents, through the public ClinicalTrials.gov API (data
from the US National Library of Medicine). Text and tables CC BY 4.0.
