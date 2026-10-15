# Is the rise real? A check with the registry's own search

The census found that the share of trials with a disability exclusion rose from 11.5-14.1% for
2000-2008 starts to 24.9% for 2025 starts (v0.1.1 rules). Two other explanations could produce
such a rise without any change in who is excluded: eligibility criteria could simply have grown
longer, so every kind of exclusion is named more often, or the mix of trials could have shifted
toward no-phase studies (behavioural, device and procedure trials), which exclude more.

This check does not use the census rules at all. It asks the ClinicalTrials.gov search how many
interventional studies that started in a year name a phrase anywhere in their eligibility
criteria, for four disability phrases and four control phrases that are not about disability.
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

## What this shows and what it does not

- It supports the census trend: the rise of cognitive and hearing exclusions is not explained by
  criteria growing longer, nor only by the shift to no-phase trials. This is a check by a
  different method (the registry's search, not the census word rules), with the same direction.
- Not every disability phrase rose. "Wheelchair" stayed flat and "dementia" rose less. Part of
  the "cognitive impairment" rise may be a change of wording (from "dementia" or "mental
  retardation" toward "cognitive impairment"), not a change of who is excluded. The census rules
  count all of these wordings together, which is why its own trend is the better measure.
- A phrase can sit in the inclusion criteria, in an exception ("except mild hearing loss"), or
  describe the study population even outside its listed conditions. These are counts of
  mentions, not of exclusions. The census's hand checks measure that difference.
- The registry search may also match close variants of a phrase. It is the same search for every
  year, so the comparison between years holds, but the absolute shares are not the census's.
- 2025 trials are still being registered late, and the counts change daily. These are the
  numbers of 2026-10-15.
- Full counts, not a sample, so there is no sampling error; the uncertainty is in what a mention
  means.

Counts by MV2 of Munim, Inc. with AI agents, through the public ClinicalTrials.gov API (data
from the US National Library of Medicine). Text and tables CC BY 4.0.
