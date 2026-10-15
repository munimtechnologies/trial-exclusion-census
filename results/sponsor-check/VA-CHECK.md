# Why do "other federal" trials exclude so often? A check of VA-led trials

Counts of 2026-10-15 from the ClinicalTrials.gov API v2 search. CC BY 4.0.
Made by MV2 of Munim, Inc. with AI agents.

## The question

The first census run found that trials led by US federal agencies other than NIH have a
disability exclusion far more often than any other sponsor class: 38.3% of 4,174 trials, against
22.8% for other (mostly academic) sponsors, 14.7% for NIH and 12.4% for industry. This check asks
which agencies those are and whether their criteria name disability more often than the
registry does or simply name everything more often.

As in [TREND-CHECK.md](../trend-check/TREND-CHECK.md), it uses the registry's own search, not
the census rules: it counts trials whose eligibility criteria name a phrase anywhere. A mention
is not always an exclusion (see the hand check below).

## 1. Most of them are VA trials

| Lead sponsor group | Interventional trials | No-phase share | Names a cognitive wording |
|---|---|---|---|
| Federal (class FED), all | 4,314 | 67.0% | 954 (22.1%) |
| Federal, name has VA, Veteran or Veterans | 2,919 | 70.5% | 895 (30.7%) |
| Federal, all others (Army, Navy, CDC, USDA, ...) | 1,395 | 59.9% | 59 (4.2%) |
| Whole registry | 463,180 | 51.6% | 42,654 (9.2%) |

Two-thirds of the federal trials are led by the Department of Veterans Affairs: its Office of
Research and Development, the Department itself and individual VA medical centers. In the first
200 federal records the API returns, 132 have a VA lead sponsor (131 of them have VA, Veteran or
Veterans in the name; the other is a VISN center). The non-VA federal trials name
a cognitive wording **less** often than the registry. So the high federal figure is a VA figure.

"Cognitive wording" is the pooled family of `trend_check.py`: cognitive impairment, dementia,
mental retardation, intellectual disability, cognitively impaired, cognitive deficit and cognitive
dysfunction.

## 2. VA criteria name disability about three times as often, and controls less often

Share of trials whose eligibility criteria name the phrase, VA-led against the whole registry:

| Phrase | Kind | VA (2,919) | Registry (463,180) | Times larger |
|---|---|---|---|---|
| cognitive (all wordings) | family | 30.7% (895) | 9.21% (42,654) | **3.33** |
| hearing (all wordings) | family | 4.21% (123) | 1.62% (7,508) | **2.60** |
| visual (all wordings) | family | 3.25% (95) | 1.22% (5,638) | **2.67** |
| pregnant | control | 28.6% (835) | 48.9% (226,630) | 0.58 |
| hepatitis | control | 3.12% (91) | 13.0% (60,230) | 0.24 |
| allergy | control | 12.2% (357) | 31.0% (143,719) | 0.39 |
| migraine | rare control | 0.69% (20) | 0.87% (4,050) | 0.78 |
| psoriasis | rare control | 0.38% (11) | 1.76% (8,131) | 0.21 |
| gout | rare control | 1.06% (31) | 0.48% (2,213) | 2.22 |
| osteoporosis | rare control | 0.99% (29) | 1.09% (5,043) | 0.91 |
| claustrophobia | rare control | 2.60% (76) | 1.50% (6,966) | 1.73 |
| tattoo | rare control | 0.17% (5) | 0.65% (3,003) | 0.26 |
| sickle cell | rare control | 0.41% (12) | 0.65% (2,993) | 0.64 |
| lactose intolerance | rare control | 0.14% (4) | 0.42% (1,966) | 0.32 |
| informed consent | reference | 27.8% (812) | 41.9% (194,104) | 0.66 |

- VA criteria are not simply longer or fuller. They name "informed consent" and 9 of the 11
  controls **less** often than the registry. Median control ratio: 0.58.
- The two controls above 1 make sense for VA patients: gout (2.22) is common in older men, and
  claustrophobia (1.73) is a usual exclusion from MRI studies.
- All three disability families rank above all 11 controls. Exact one-sided rank-sum test of the
  three families against the 11 controls: rank sum 39, **p = 1/364 = 0.0027**.

### Not explained by the VA's trial mix

| Family | No-phase trials only: VA (2,057) | Registry (238,806) | Times larger | Without trials of that condition: VA | Registry | Times larger |
|---|---|---|---|---|---|---|
| cognitive | 33.4% (688) | 12.3% (29,301) | 2.73 | 24.0% (702) | 7.61% (35,230) | 3.16 |
| hearing | 4.62% (95) | 2.32% (5,529) | 1.99 | 3.19% (93) | 1.39% (6,420) | 2.30 |
| visual | 3.60% (74) | 1.83% (4,362) | 1.97 | 2.84% (83) | 0.99% (4,599) | 2.86 |

- The VA runs more no-phase (behavioural, device and procedure) trials, which name disability more
  often. Within no-phase trials alone, VA trials still name cognitive wordings 2.7 times and
  hearing and visual wordings about 2 times as often. The controls were not counted within
  no-phase trials, so there is no test for this row yet.
- Leaving out the trials that study that condition (dementia, hearing or eye trials) leaves the
  ratios at 2.3 to 3.2. So the VA is not just running more dementia or hearing trials.
  Condition terms used: cognitive OR dementia OR alzheimer; hearing OR deafness OR tinnitus OR
  ear; vision OR visual OR eye OR blindness OR retina OR retinal OR macular OR glaucoma.

## 3. The mentions are exclusions

A hand check read the 12 VA trials the API returned first that name a cognitive wording outside a
cognitive or dementia trial. **All 12 use it in the exclusion criteria.** The quotes below were
copied from the records by the API reader.

| Trial | Condition | Exclusion item (quoted) |
|---|---|---|
| NCT03429166 | PTSD | "Cognitive impairment indicated by chart diagnoses or observable cognitive difficulties" |
| NCT06746727 | Alcohol problems; PTSD | "Cognitive impairment that would interfere with study participation" |
| NCT06746740 | Sexual violence | "significant cognitive impairment" |
| NCT01544127 | Suicidal ideation; treatment engagement | "dementia," |
| NCT01900561 | Prostate cancer | "Dementia or other significant mental impairment" |
| NCT06288438 | Multimorbidity; physical deconditioning | "Moderate to severe dementia (<11 on telephone Montreal Cognitive Assessment(T-MoCA))" |
| NCT05226130 | Alcohol use disorder | "History of neurological disorder that might be associated with cognitive dysfunction." |
| NCT03191760 | PTSD | "...moderate-severe Traumatic Brain Injury, uncontrolled psychosis, dementia, communication flag..." |
| NCT02211274 | Aged; frail elderly | "CLC residents will be excluded if they are too cognitively impaired..." |
| NCT04563741 | PTSD; overweight; obesity | "...moderate to severe chronic, progressive neurologic conditions such as Dementia" |
| NCT07050862 | Tobacco use disorder; rTMS | "...such as bipolar affective disorder, schizophrenia, dementia, or major depression" |
| NCT00310362 | Colorectal cancer | "...had Type 1 diabetes, dementia or Alzheimer's or multiple GI procedures on the same day..." |

Many of these are mental-health and behavioural trials. They often exclude by a broad cognitive
term ("significant cognitive impairment", "would interfere with study participation") with no
cut-off or accommodation. Two are narrower: one sets a test cut-off (T-MoCA below 11) and one
looks for a recorded diagnosis.

## What this shows and what it does not

- **Shown:** the high federal rate of disability exclusions comes from VA-led trials. Their
  criteria name cognitive, hearing and visual disability 2.6 to 3.3 times as often as the
  registry overall, while they name non-disability controls less often (p = 0.0027 against 11
  controls). This holds without the trials of those conditions and, at about 2 to 2.7 times,
  within no-phase trials.
- **Not shown:** that these exclusions are unjustified. Many VA trials are psychotherapy and
  behavioural studies, where a broad cognitive exclusion is common practice. Veterans are older
  and mostly men, so the VA's patients differ from the registry's. A fair comparison would match
  trials by condition and design. That has not been done.
- **Why it matters:** veterans have high rates of TBI, hearing loss and other disabilities, so
  broad exclusions in VA research may leave out many of the people that research is meant to serve.
  That is a hypothesis for VA research offices to check against their own protocols, not a
  finding.
- **Limits:** mentions anywhere in the criteria, not hand-checked exclusions (12 of 12 read were
  exclusions, a small sample). The VA group is matched by name, so VA sites without VA, Veteran or
  Veterans in the name (for example a "VISN 17 Center of Excellence") are counted as non-VA. VA
  trials classed as other than FED are not included. The search expands synonyms, as noted in
  TREND-CHECK.md. The controls are the same 11 used in the trend check; they were not chosen
  for this question, but they were chosen before it was asked.
- **Prior art:** a web search on 2026-10-15 found no registry-wide count of disability exclusions
  in VA-led trials. Earlier hand-coded studies (DeCormier Plosky et al. 2022, McDonald et al.
  2022) did not split by VA.

## Repeat it

```
python sponsor_check.py --sponsor va --json va.json     # about 50 small requests
python sponsor_check.py --sponsor fed
```

`sponsor_check.py` makes every count in sections 1 and 2 (the no-phase and the
not-own-condition columns too) and the rank test. Section 3 was read by hand.
