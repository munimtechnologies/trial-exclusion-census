# trial-exclusion-census

How often do clinical trials exclude disabled people, and is it changing?

`trial-exclusion-census` reads the eligibility criteria of every interventional study on
[ClinicalTrials.gov](https://clinicaltrials.gov/) through its public API v2. It finds each trial's
exclusion criteria and flags items that exclude people by disability:

| Category | Examples of what it flags |
|---|---|
| cognitive | dementia, cognitive impairment, intellectual or developmental disability, learning difficulties, MMSE/MoCA cut-offs |
| consent_capacity | "unable to provide informed consent", lack of decision-making capacity, decisionally impaired, adults under guardianship or curatorship |
| visual | blindness, visual impairment, low vision, visual acuity limits (not "double-blind", and since 0.3.0 not eye findings that only matter to an eye exam), and since 0.5.0 large print or braille named in an exclusion ("unable to read large print") |
| hearing | deafness, hearing loss, hearing aids, cochlear implants, and since 0.5.0 sign language use ("requires use of sign language interpreter", "primary use of American Sign Language") |
| communication | aphasia, dysarthria, illiteracy, "unable to speak/read/write" (but not "...English") |
| mobility | wheelchair use, non-ambulatory, "unable to walk", paralysis, amputation (since 0.3.0 not a planned amputation), motor deficits, spasticity |

Since 0.4.0 it also reads lists: "cognitive, visual or motor impairment" counts in all three
categories, and "unable to hear, read or comprehend" counts for each verb.

It also counts the domains that earlier manual studies reported: psychiatric, substance use,
performance status (ECOG/Karnofsky), investigator discretion, English-only and general
"disability". Then it notes two things for each trial:

- **Accommodation**: whether an item of the criteria offers one, such as consent by a legally
  authorized representative for an adult, "with or without an assistive device", an interpreter
  provided, or a nurse available to read. Since 0.5.0 a word alone is not enough (see below).
- **Condition-related**: whether a flagged exclusion matches the trial's own condition.
  Excluding vision loss from a glaucoma trial is not the same as excluding it from a diabetes trial.

### Ability requirements in the inclusion criteria (since 0.2.0)

People are also shut out by what the inclusion criteria *require*. Since 0.2.0 the census reads
the inclusion criteria too, for requirements in the same six categories:

| Category | Examples of what it flags |
|---|---|
| cognitive | "cognitively intact", "normal cognition", "sufficient cognitive ability", "MMSE of 24 or higher" |
| consent_capacity | "able to provide informed consent" when the item names no representative, guardian or parent; "able to understand the study" (but not "...English") |
| visual | "normal or corrected-to-normal vision", "able to see", "BCVA 20/40 or better", "20/20 vision", "no visual impairment" |
| hearing | "normal hearing", "able to hear", "no hearing or auditory impairment" |
| communication | "able to read and write", "able to speak", "able to converse", "literate" (but not "...in English"), "no communication problem" |
| mobility | "able to walk 100 m", "ambulatory without assistance", "walks independently", "able to perform the 6-minute walk test", "GMFCS I-III" |

An exclusion-only count cannot see these. In McDonald, Schwartz and Sabatello's hand-coded study
(2022), indirect criteria like these were a large part of how trials could exclude adults with
intellectual disability. The census reports, for every year, how many trials have such a
requirement and how many have one **only** there, with no disability exclusion at all.

Results come by start year, lead sponsor class and phase. There is also a replication check
against the four therapeutic areas that DeCormier Plosky et al. coded by hand.

## First results (v0.1.1 rules, pre-registered)

The full tables are in [results/v0.1.1/](results/v0.1.1/) (CC BY 4.0). The data was fetched on
2026-10-14 and covers **463,180 interventional studies**, of which **450,052** have an exclusion
section. The rules were published before any of these numbers were seen.

- **20.1%** of trials with an exclusion section exclude people in at least one of the six
  disability categories. The figure is **17.9%** when exclusions that match the trial's own
  condition are left out. By category: cognitive 9.7%, consent capacity 7.0%, mobility 2.6%,
  communication 1.9%, visual 1.9% and hearing 1.7%.
- **The share rose over time.** Among trials that started from 2000 to 2008, 11.5% to 14.1% had a
  disability exclusion each year. The figure was 20.0% for 2016 starts and 24.9% for 2025 starts.
  Over the same years, substance-use exclusions fell from 18.7% to 15.8%, so not every kind of
  exclusion grew. Trials that start in 2026 are still being registered, and that year reads 27.5%.
  How much of this rise is specific to disability is checked below; the short answer, now from a
  pre-registered test, is that it is clear in no-phase trials and not shown in the others.
- By lead sponsor class: other (mostly academic) 22.8%, industry 12.4%, NIH 14.7%, and other US
  federal agencies 38.3% (4,174 trials). Most of those are trials led by the Department of
  Veterans Affairs (see below).
- By phase: trials with no phase (devices, behavioural studies, procedures) 25.7%; phase 1 10.7%,
  phase 2 14.1% and phase 3 13.5%.

**Correction to the accommodation figure.** Earlier versions of this page said that only 7.0% of
the trials with a disability exclusion mention any accommodation, and that NIH-led trials mention
one most often (14.9%). That flag counted any accommodation *word* anywhere in the criteria. A
hand check of the 16 trials in the random recall sample that it flagged found only **5** that
offer an accommodation (31%; Wilson 95% interval 14% to 56%). The other 11 were a parent's or
guardian's consent for a child (7), an eye's "accommodation", a catheter sheath "to accommodate",
"communication without an interpreter", and an exclusion of "consent obtained through a surrogate"
([results/recall/ACCOMMODATION.md](results/recall/ACCOMMODATION.md)). So those two numbers are
not a measure of accommodation and should not be quoted. 0.5.0 counts only items that offer one;
its registry figure, with a fresh hand-checked sample, comes with the next full run.

**Precision.** 720 random flagged exclusion items were checked by hand, 60 per category, 360 of
them in the six disability categories ([PRECISION.md](results/v0.1.1/PRECISION.md)). Cognitive was 95% correct, consent capacity 100%,
hearing 95%, communication 97% (80% if literacy items are left out), mobility 90% and visual 75%.
The visual errors were eye findings in ophthalmology trials, and 0.3.0 removes them.

### Is the rise real? A check with the registry's own search

The rise could come from criteria simply growing longer, from a change of wording, or from the
shift toward no-phase trials, which exclude more.
[results/trend-check/TREND-CHECK.md](results/trend-check/TREND-CHECK.md) tests these without the
census rules: it asks the ClinicalTrials.gov search how many trials of each start year name a
phrase in their eligibility criteria (counts of 2026-10-15), for disability phrases and for
phrases that are not about disability.

**Correction (2026-10-15).** The first version of this check used only common controls
(pregnancy, hepatitis, allergy), which stayed flat, and said the rise was not explained by
longer criteria. Common phrases cannot triple, so that was too strong. Rare controls, which
start as rare as the disability phrases, can rise a lot: tattoo exclusions 2.4 times, psoriasis
2.6 times in drug trials. Pooling every wording of a disability (so that "dementia" becoming
"cognitive impairment" cancels out) also shrinks the cognitive rise. What holds:

- No-phase trials (behavioural, device and procedure studies) grew from 29% to 65% of starts.
  **Within them**, from 2008 to 2025 starts, the share naming any cognitive wording rose 1.7
  times, any hearing wording 2.4 times and any visual wording 3.1 times. Of 11 controls that are
  not about disability (median 1.1 times), only one or two rose as fast. Exact rank-sum test of
  the three families against the controls: p = 0.019.
- **Within the other trials**, mostly drug trials, the families rose 1.5 to 1.8 times, inside the
  range of the controls (0.8 to 2.6, median 1.4; p = 0.33). There is no evidence there of a
  disability-specific rise.
- The single phrase "cognitive impairment" rose 3.8 times overall, but all cognitive wordings
  together rose 2.1 times, so part of that was a change of wording.
- These are mentions anywhere in the criteria, not exclusions, and the choice of wordings and
  controls was made after the first results, so this is exploratory. The census rules and their
  hand checks are the measure of exclusion.

`trend_check.py` repeats every count and the test.

**The pre-registered test confirms it.** [PREREG-v0.3.md](results/trend-check/PREREG-v0.3.md)
fixed the phrase lists (23 controls, 12 of them never counted), a rule dropping controls with
fewer than 20 matches in 2008, the hypotheses and the tests before counting.
[PREREG-v0.3-RESULT.md](results/trend-check/PREREG-v0.3-RESULT.md) reports the result:

- **H1 holds:** in no-phase trials the three families rose more than all 9 controls the rule keeps
  (largest 1.63 times): p = 0.0045. With all 23 controls kept, which was not pre-registered,
  p = 0.020.
- **H2 holds:** in the other trials the families sit in the middle of 22 controls: p = 0.45.
- The rule was written when some 2008 counts were already known, and it drops tattoo, the old
  test's top control. Both results are reported.
- **By year** ([PREREG-v0.3-PERYEAR.md](results/trend-check/PREREG-v0.3-PERYEAR.md)): the
  pre-registered per-year secondary, counted for no-phase trials and the 9 kept controls, uses
  all 18 start years. The three families have the three steepest slopes of log share on year
  (visual +7.3%, hearing +6.2%, cognitive +3.2% a year; steepest control, eczema, +2.4%):
  p = 0.0045. The cognitive lead over the controls is small. The other strata were not counted
  by year.

`prereg_v03.py` and `peryear_v03.py` recompute every number from the saved counts.

### Which federal sponsors? The VA

[results/sponsor-check/VA-CHECK.md](results/sponsor-check/VA-CHECK.md) asks why "other federal"
trials exclude so often, again with the registry's own search (counts of 2026-10-15):

- Two-thirds of federal-led interventional trials (2,919 of 4,314) are led by the Department of
  Veterans Affairs. The other federal trials name a cognitive wording **less** often than the
  registry (4.2% against 9.2%).
- VA-led trials name a cognitive wording 3.3 times as often as the registry (30.7% of trials),
  and hearing and visual wordings 2.6 and 2.7 times as often. They name "informed consent" and 9
  of 11 non-disability controls **less** often (median 0.58 times). All three disability families
  rank above all 11 controls: exact rank-sum test p = 0.0027.
- Leaving out trials of the condition itself (dementia, hearing or eye trials), the ratios are
  2.3 to 3.2. **Within no-phase trials only**, they are 2.7 (cognitive) and about 2 (hearing,
  visual), and the pre-registered secondary test with all 23 controls there gives p = 0.0015:
  19 of 23 controls are named less often by VA trials, and only gout ranks among the families
  ([PREREG-v0.3-RESULT.md](results/trend-check/PREREG-v0.3-RESULT.md)).
- **Matched on condition (pre-registered).** Against other no-phase trials of the same five
  conditions (PTSD, substance use, depression, pain, cardiometabolic; trials of cognitive,
  brain-injury, stroke, hearing and eye conditions left out), VA-led trials name a cognitive
  wording **2.2 times** as often (Mantel-Haenszel, 95% interval 2.0 to 2.5) and a hearing wording
  1.8 times (1.2 to 2.5). Visual is 1.5 (0.9 to 2.6), not shown on its own. The families rank
  above all 5 kept controls, p = 0.018, and VA trials name "informed consent" less often (0.72).
  Matching explains part of the cognitive gap (2.81 unmatched in the same strata), not all of it
  ([PREREG-VA-MATCHED.md](results/sponsor-check/PREREG-VA-MATCHED.md),
  [VA-MATCHED-RESULT.md](results/sponsor-check/VA-MATCHED-RESULT.md)). Correction (2026-10-15):
  the unmatched figure was first given as 2.9, from a slip in adding the VA counts by hand (263
  instead of 255). The matched result is unchanged.
- **Why hearing?** The first 20 of the 30 VA hearing mentions in those strata, read one by one
  ([VA-HEARING-READ.md](results/sponsor-check/VA-HEARING-READ.md)), all shut out people with
  hearing loss, and at least 6 because the study runs by telephone or computer ("Hearing
  impairment that precludes completing telephone assessments"). None of their registry entries
  offers captioned telephone, relay or text contact instead.
- The first 12 such VA trials read by hand, outside cognitive or dementia trials, all use the
  wording as an exclusion, often a broad one ("significant cognitive impairment", "cognitive
  impairment that would interfere with study participation"), many in PTSD and other
  mental-health trials.
- This does not show that the exclusions are unjustified. VA patients and trial designs differ
  from the registry's, and the matched test matches on condition only, not on design, age or sex.

### Is it the telephone? Across all sponsors, yes (pre-registered)

[PREREG-PHONE-MATCHED.md](results/phone-check/PREREG-PHONE-MATCHED.md) asked whether the VA
pattern holds for every sponsor. Do no-phase trials whose interventions mention the telephone
name a hearing wording more often than other trials of the same condition (HP1)? Do they name it
more often than visual wordings or non-disability controls (HP2)? The design was fixed before
counting. The result, from 156 counts of 2026-10-15
([phone-matched-counts.json](results/phone-check/phone-matched-counts.json),
[PHONE-MATCHED-RESULT.md](results/phone-check/PHONE-MATCHED-RESULT.md)):

- Telephone-delivered trials name a hearing wording **2.45 times** as often as other no-phase
  trials of the same condition (Mantel-Haenszel, 95% interval 2.17 to 2.75). **HP1 holds.**
  Visual wordings: 2.13 (1.85 to 2.47). Cognitive wordings: 1.93 (1.84 to 2.02).
- They name all 8 non-disability controls **less** often (0.24 to 0.61 times), and "informed
  consent" too (0.78), so their criteria are not simply fuller. Hearing ranks first of 10
  (**HP2 holds**; by chance 1 in 10). The three families rank above all 8 controls, p = 0.0061.
- **Not a VA effect.** Leaving out VA-led trials (exploratory) gives 2.41 (2.14 to 2.72).
- **Hearing is first, not alone.** It leads visual by little, and the intervals overlap. The
  exposure also takes in mobile-phone apps and text messages, which need sight. So the finding is
  that telephone-delivered trials name sensory and cognitive disability much more often, with
  hearing first, not that the telephone singles out hearing alone.
- **Does the hearing item say it is the phone? Not often (pre-registered reading, S2).**
  [PHONE-HEARING-READ.md](results/phone-check/PHONE-HEARING-READ.md) read 20 hearing mentions in
  telephone trials and 20 in other trials, outside the VA. All 40 shut people with hearing loss
  out. The hearing item itself names the phone in 4 of 20 telephone trials ("Severe hearing
  impairment not allowing phone delivery") and 1 of 20 others. The prediction of at least 5
  failed by one, and the difference is not significant (one-sided Fisher p = 0.17). Exploratory:
  13 of the 20 telephone trials name a phone somewhere in their criteria, against 5 of 20, so a
  bare hearing exclusion often sits beside a requirement to use a phone.
- The known fixes are cheap: captioned telephone, relay services such as 711, text or chat, and
  video with captions.

**What these numbers do not show yet.**

- Recall of the pre-registered rules on the full registry. The 0.4.0 rules are now scored on the
  111 recall trials labelled after they were fixed (see the 0.4.0 section below). On the 78
  random trials among them, the exclusion rules of v0.1.1 (unchanged in 0.2.0) find 15 of the 22
  trials labelled as excluding someone, so the v0.1.1 figures above are likely undercounts too.
- How often trials offer an accommodation (see the correction above).
- Registry criteria are often a summary of the full protocol. On the four areas DeCormier Plosky
  et al. coded from full protocols, the registry text shows lower rates for vision (dementia
  trials 6.4% here against 34% there). Cognitive exclusions in dementia trials are close
  (50.7% against 42%).

### Sign language, large print and braille across the whole registry

On 2026-10-15 the ClinicalTrials.gov search found 51 of 463,180 interventional studies that name
sign language in their eligibility criteria, 5 that name large print and 3 that name braille.
Where these words appear in the **exclusion** criteria, they mostly describe who is shut out:
"Requires use of sign language interpreter" (NCT01109576), "Primary use of American Sign Language
(ASL)" (NCT00763243), "Adults who use sign language as a primary means of communication"
(NCT02684175), "hearing impaired (requires use of American Sign Language interpreter)"
(NCT07489144), "Significant sensory impairment (e.g., needing a British Sign Language
interpreter)" (NCT07246356). One exclusion item in this set instead offers ASL and Spanish
interpreters around the clock (NCT04374760). A word list that treats these words as
accommodations gets them backwards, which is why 0.5.0 counts them as exclusions there.
The counts come from the registry's own search, and the quotes were checked against each record.

## The 0.4.0 rules on the full registry (not pre-registered)

The tables are in [results/v0.4.0/](results/v0.4.0/) (CC BY 4.0), from a run of the 0.4.0 rules
(tag v0.4.0) on data fetched on 2026-10-15: 463,329 interventional studies, of which 450,201 have
an exclusion section. The 0.3.0 and 0.4.0 rules were written after the first results were seen,
so these numbers are **not pre-registered**. They are reported beside the v0.1.1 figures above,
not in place of them.

- **22.37%** of trials with an exclusion section exclude people in at least one of the six
  disability categories, and **20.18%** when exclusions that match the trial's own condition are
  left out. By category: cognitive 10.38%, consent capacity 8.67%, mobility 3.44%, hearing 2.63%,
  visual 2.25% and communication 2.01%. The 0.3.0 rules give 19.81% on the same records
  ([diff_summary.json](results/v0.4.0/diff_summary.json)), so the rise from 0.3.0 comes from the
  list and wording rules 0.4.0 added.
- **What the rules miss, on trials labelled after they were fixed**
  ([SCORES-0.4.0.md](results/recall/SCORES-0.4.0.md)). Of the 78 random trials in the held-out
  half of the recall sample, 22 were labelled as excluding someone by disability. 0.4.0 flags
  16 of the 22 (73%; Wilson 95% interval 52% to 87%), against 15 of 22 for 0.3.0, and every trial it
  flags is right. The inclusion-requirement rules find 13 of 19 (68%, 46% to 85%), and 13 of 14
  of their flags are right. So the registry figures are more likely too low than too high. The
  intervals are wide, and the labels were made by AI agents working for MV2, one reader per
  trial, not yet checked by a person.
- **Ability requirements.** 16.36% of trials require an ability in their inclusion criteria,
  most often the capacity to consent with no representative named (12.69%). **33.74%** have a
  disability barrier in either section, and **11.38%** have one only in the inclusion criteria,
  where an exclusion-only count cannot see it. In the held-out random sample the share with a
  barrier only there is 13 of 78 (17%, 10% to 26%).
- **The trend controls, run for the first time.** From 2008 to 2025 starts, the share with a
  disability exclusion rose from 15.16% to 27.83% (1.84 times). Criteria grew only a little
  longer (8.96 to 9.31 exclusion items per trial), while disability items per 100 exclusion items
  rose from 2.04 to 3.98. Within no-phase trials the share rose from 21.59% to 33.40%
  (1.55 times), and within phased trials from 12.48% to 17.66% (1.42 times). Each design rose less than
  the whole, so part of the overall rise is the shift toward no-phase trials, which exclude more.
  Unlike the registry-search check above, this census count has no non-disability controls, so it
  does not by itself show a rise specific to disability. Trials that start in 2026 are still
  being registered (30.91% so far).
- **Accommodation.** The 0.4.0 tables still carry the old accommodation flag (5.13%), which the
  hand check above showed is not a measure of accommodation. Do not quote those columns; 0.5.0
  replaces the flag.
- The precision sample of this run (`sample_items.csv`) has not been checked by hand yet.

`test_results_v040.py` checks that these tables agree with each other, recomputes every fraction
and Wilson interval in SCORES-0.4.0.md, and checks every number this section quotes against the
data.

## For study teams and IRB reviewers

- **Browser check** ([web/check.html](web/check.html): download the file and open it in any
  browser): paste a study's criteria and see each exclusion item that touches disability and
  each inclusion item that requires an ability, with an inclusive alternative to consider, and the
  items that already offer an accommodation. It runs in the page, so nothing you paste is sent
  anywhere. It uses the same rules as the census, and `test_web_check.py` keeps the two identical.
- **Guide** ([toolkit/inclusive-eligibility-guide.md](toolkit/inclusive-eligibility-guide.md),
  CC BY 4.0): for each category, when an exclusion may be needed, how to narrow it, which
  accommodations to offer instead, protocol wording to adapt, and a one-page accessibility plan.
  It is a draft. It has not yet been reviewed by people with lived experience of disability, and
  that review comes next.

## Why

People with disabilities are about a quarter of US adults. They are often left out of trials, by
explicit criteria and by vague ones. Earlier studies coded samples by hand:

- DeCormier Plosky et al., *Health Affairs* 2022 ([doi:10.1377/hlthaff.2022.00520](https://www.healthaffairs.org/doi/10.1377/hlthaff.2022.00520)):
  97 protocols in dementia, depression, diabetes and lung cancer. Exclusion rates were psychiatric 68%,
  cognitive or intellectual 42%, visual 34%, hearing 10%, mobility 9% and communication 3%. Only 18%
  permitted accommodations, and 85% allowed broad investigator discretion.
- McDonald, Schwartz and Sabatello, *Disability and Health Journal* 2022
  ([doi:10.1016/j.dhjo.2022.101368](https://doi.org/10.1016/j.dhjo.2022.101368)): 74.6% of recent
  NIH-funded Phase 2-4 trials of working-age US adults had criteria that could exclude adults with
  intellectual disability. About a third excluded them directly; others did so indirectly,
  through requirements such as reading and writing or functional capacity.
- "'Being disabled' as an exclusion criterion for clinical trials: a scoping review" (2023,
  [PMC10626873](https://pmc.ncbi.nlm.nih.gov/articles/PMC10626873/)): 2,710 completed trials from
  2010-2020 for the leading causes of disability-adjusted life-years. 35.3% had explicit and 44.5%
  had implicit disability exclusions.

No open, registry-wide and repeatable count existed, and none showed a trend by year. This tool
does both, and its rules are open for anyone to check, re-run and argue with. NIH's Strategic Plan
for Disability Health Research FY26-FY30 makes inclusion in clinical research an objective, so a
yearly count is useful.

The exclusion rules in v0.1.0 and the inclusion-requirement rules in v0.2.0 were each written and
published **before any registry result was seen**. The 0.3.0 changes were made after the hand
check of the first run, the 0.4.0 changes after half of the recall sample was labelled, and the
0.5.0 changes after reading every registry trial that names sign language, large print or
braille. They are reported next to the pre-registered numbers, never in place of them, and
checked on fresh samples: 0.4.0 on the 111 recall trials labelled after its rules were fixed.

### Related work

- The National Council on Disability's report
  [*The Implicit and Explicit Exclusion of People with Disabilities in Clinical Trials*](https://www.ncd.gov/report/the-implicit-and-explicit-exclusion-of-people-with-disabilities-in-clinical-trials/)
  (2024) found that eligibility criteria often exclude disabled people without scientific
  justification. It recommends guidance that bases exclusions on science and writes permissible
  accommodations into the criteria.
- The MRCT Center's [Accessibility by Design in Clinical Research Toolkit](https://mrctcenter.org/wp-content/uploads/2023/12/12-11-2023-AbD-Toolkit.pdf)
  (v1.2, 2023, CC BY-NC-SA 4.0) covers the whole study lifecycle. Its Tool A.2.i sets problematic
  eligibility wording beside preferred wording. The guide here is written separately and quotes none
  of it. This repository adds automatic detection and registry-wide numbers.

## Use

```
python exclusion_census.py census --out-dir out --cache ctgov.jsonl.gz
python exclusion_census.py census --out-dir out2 --cache ctgov.jsonl.gz --seed 2027   # fresh precision sample
python exclusion_census.py check criteria.txt     # one trial's criteria, with alternatives to consider
python diff_rules.py --old old/exclusion_census.py --new exclusion_census.py --cache ctgov.jsonl.gz
python trend_check.py --json trend.json           # the registry-search trend check (215 small requests)
python sponsor_check.py --sponsor va --json va.json   # one sponsor group against the registry
python prereg_v03.py                              # the pre-registered trend test, from saved counts
python peryear_v03.py                             # its per-year secondary, from saved counts
python va_matched.py                              # the pre-registered condition-matched VA test, from saved counts
python va_matched.py --fetch --json va-matched.json   # the same, counted again
python phone_matched.py                           # the pre-registered telephone test, from saved counts
python phone_matched.py --fetch --json phone-matched.json   # the same, counted again (156 small requests)
python -m unittest -v
```

`census` pages through the API with a pause between requests. It writes:

- `summary.json` and `results.md` (including the inclusion-requirement tables, overall and by
  year, and since 0.3.0 the trend controls)
- `by_year.csv`, `by_year_design.csv` (each start year split into phased and no-phase trials),
  `by_sponsor.csv`, `by_phase.csv` and `plosky_areas.csv`. Each row also has
  `<category>_required_pct`, `any_required_pct`, `required_only_pct` and `any_barrier_pct`, and,
  since 0.3.0, `exclusion_items_mean` and `core_items_per_100` (disability items per 100 exclusion
  items)
- `sample_items.csv`: up to 60 random flagged items per category (and per `required_<category>`,
  and since 0.5.0 per `accommodation`), so the rules' precision can be checked by hand. `--seed`
  draws a fresh sample
- `trials.csv.gz`: one row per trial (NCT ID, year, sponsor class, phase, categories, required,
  number of exclusion items)

The cache keeps the fetched records, so revised rules can be re-run without fetching again.

`check` prints each flagged exclusion item and each inclusion item that requires an ability in one
trial's criteria, with an inclusive alternative to consider (for example, read-aloud or
large-print consent instead of excluding blind people), and then the items that offer an
accommodation.

`diff_rules.py` (new in 0.4.0) runs two versions of the rules over the cache and samples the items
one flags and the other does not, so the precision of just the new rules can be checked by hand.

`trend_check.py` asks the registry's own search, for each start year, how many trials name each of
a few disability phrases, pooled disability families (every wording at once), common and rare
control phrases, overall, in no-phase and other trials, and for some phrases without the trials
that study that condition. It then tests the families against the controls with an exact rank-sum
test. `--years` and `--phrases` take other lists.

`sponsor_check.py` does the same for one sponsor group against the whole registry, over all
start years: the share of the group's trials naming each family and control, the ratio to the
registry's share, each family within no-phase trials and without trials of its own condition,
and the same rank-sum test. `--sponsor` takes `va`, `fed`, `nih`, `industry` or any search
fragment.

`prereg_v03.py` reads the counts fetched for the pre-registered test
(`results/trend-check/prereg-v0.3-counts.json`), applies its 20-match rule and runs H1, H2, the
VA secondary test and the sensitivity checks. `--json` writes the ratios and tests.
`peryear_v03.py` reads `results/trend-check/prereg-v0.3-peryear-counts.json` and gives each
phrase's slope of log share on start year and the same test on the slopes.

`va_matched.py` compares VA-led no-phase trials with other no-phase trials of the same condition
in five disjoint strata, with a Mantel-Haenszel ratio for each phrase and the families against the
controls, as fixed in [PREREG-VA-MATCHED.md](results/sponsor-check/PREREG-VA-MATCHED.md).
`--fetch` makes the counts (about 130 small requests); without it, it reads the saved counts in
`results/sponsor-check/va-matched-counts.json`.

`phone_matched.py` makes the same comparison for telephone-delivered trials of every sponsor
against other trials, in the same five strata plus one for every other condition, and gives HP1
and HP2 of [PREREG-PHONE-MATCHED.md](results/phone-check/PREREG-PHONE-MATCHED.md). It reuses the
ratios and the test of `va_matched.py`. Without `--fetch`, it reads the saved counts in
`results/phone-check/phone-matched-counts.json`. The exploratory
`phone-matched-nonva-counts.json` holds the hearing family only, in the same layout, so
`phone_matched.rows()` applies to it (`test_phone_matched.py` does this). The S2 reading is in
`results/phone-check/phone-hearing-read.json`; `test_phone_hearing_read.py` checks its queries
against the pre-registration and recomputes its counts and Fisher test.

Standard library only (Python 3.9+). No API key.

## Measuring what the rules miss

`sample_items.csv` measures precision: of the items flagged, how many really exclude by
disability. It cannot show what the rules miss. `recall_sample.py` does that:

```
python recall_sample.py draw --cache ctgov.jsonl.gz --out-dir recall
#   label recall/labels.csv by hand while reading recall/blind.md
python recall_sample.py score --sample recall/sample.jsonl --labels recall/labels.csv
```

`draw` takes two seeded random samples of trials with an exclusion section, without looking at
the flags. The first (150 trials) is any trial. The second (75) is trials the rules did not flag
whose criteria still use a loose word such as "walk", "hearing" or "understand". It is only used
to find misses quickly, never as an estimate. `blind.md` shows each trial's full criteria in
shuffled order with no flags, so the labeller cannot see what the rules said.

Each trial gets one mark per category: `x` if the exclusion criteria shut people out for that
kind of disability, `i` if the inclusion criteria require an ability that does (for example
"able to walk 100 m unaided"), or both. `score` reports per-category precision and recall on the
random sample, with Wilson 95% intervals: the exclusion rules against the `x` marks and, since
0.2.0, the inclusion-requirement rules against the `i` marks. It lists every miss. It re-runs the
current rules on the same trials, so a revised rule set can be compared on the same sample.

The labels for the first sample are in [results/recall/](results/recall/), in two halves: the
first 114 trials, whose misses shaped 0.4.0, and the other 111, labelled after 0.4.0 was fixed.
The scores of 0.4.0 on the second half are in [SCORES-0.4.0.md](results/recall/SCORES-0.4.0.md).

## Limits

- A word list, not a reader. It flags what a criterion says, not whether that exclusion or
  requirement is justified for the study. It misses criteria worded in ways it does not know, and
  it can flag items that mention a word in passing. `sample_items.csv`, `recall_sample.py` and
  `diff_rules.py` exist to measure this.
- The hand checks so far were done by AI agents working for MV2, one reader per item. Review by
  people with clinical and lived experience of disability is still to come.
- Illiteracy and "unable to read" count as communication exclusions. Reading is not a disability in
  itself, but these items shut out many people with intellectual, learning and print disabilities.
  `sample_items.csv` lets anyone count them separately.
- "Able to provide informed consent" is counted only when the same item names no representative,
  guardian or parent, but a representative allowed elsewhere in the criteria is not taken into
  account (the accommodation flag notes it).
- The accommodation flag (0.5.0) leaves out every item that mentions a parent, a child or an age
  under 18, so a pediatric trial that offers, say, AAC through a parent is not counted. It was
  written from the same 16 trials it was checked on; its precision on fresh data comes from the
  `accommodation` rows of the next `sample_items.csv`.
- Guardianship and curatorship count as consent capacity. In a few pediatric trials "under
  guardianship" can mean a ward of the state rather than an adult under a protection measure.
- Inclusion sections are found only under an "Inclusion Criteria" heading. Criteria written as
  one unheaded list are read for exclusions only if they say "Exclusion criteria".
- "Condition-related" is a rough match between word lists and the trial's own condition and title.
- Registry text is what sponsors entered, which is often a summary of the full protocol.
- Information only. It is not medical, legal or IRB advice.

## Changes

- After 0.5.0 (on main): the 0.4.0 rules' full-registry run of 2026-10-15
  ([results/v0.4.0/](results/v0.4.0/)) and their scores on the held-out half of the recall sample
  ([SCORES-0.4.0.md](results/recall/SCORES-0.4.0.md)): 22.37% of 450,201 trials (not
  pre-registered), recall 16 of 22 on held-out random trials, and the first run of the trend
  controls. `test_results_v040.py` checks every number quoted. The census rules are unchanged.
- After 0.5.0 (on main): the pre-registered S2 reading of the telephone test.
  [PHONE-HEARING-READ.md](results/phone-check/PHONE-HEARING-READ.md) and
  [phone-hearing-read.json](results/phone-check/phone-hearing-read.json): 20 hearing mentions in
  non-VA telephone trials and 20 in other non-VA trials, each quote checked against its record.
  All 40 shut people out. The hearing item names the phone in 4 of 20 against 1 of 20; the
  prediction of at least 5 failed by one (Fisher p = 0.17). `test_phone_hearing_read.py` checks
  the queries, the marks and every number. The census rules are unchanged.
- After 0.5.0 (on main): the pre-registered telephone test, counted.
  [phone-matched-counts.json](results/phone-check/phone-matched-counts.json) (156 counts of
  2026-10-15) and [PHONE-MATCHED-RESULT.md](results/phone-check/PHONE-MATCHED-RESULT.md):
  matched on condition, telephone-delivered no-phase trials of every sponsor name a hearing
  wording 2.45 times (2.17 to 2.75) as often as other trials, visual 2.13 and cognitive 1.93,
  while all 8 controls are named less often. HP1 and HP2 hold; S1 p = 0.0061. Exploratory:
  without VA-led trials, hearing 2.41 (2.14 to 2.72)
  ([phone-matched-nonva-counts.json](results/phone-check/phone-matched-nonva-counts.json)).
  `test_phone_matched.py` checks the published numbers against the code. The census rules are
  unchanged.
- After 0.5.0 (on main): a correction and a new pre-registration.
  [VA-MATCHED-RESULT.md](results/sponsor-check/VA-MATCHED-RESULT.md) and VA-CHECK.md gave 263 VA
  cognitive matches and an unmatched ratio of 2.90; the saved counts give 255 and 2.81 (a slip in
  adding by hand). The matched result is unchanged, and `test_va_matched.py` now checks the
  published numbers against the code.
  [PREREG-PHONE-MATCHED.md](results/phone-check/PREREG-PHONE-MATCHED.md) and
  `phone_matched.py` 0.1.0 fix a test of telephone-delivered trials against other trials of the
  same condition, all sponsors, before it is counted. The census rules are unchanged.
- After 0.5.0 (on main): the pre-registered condition-matched VA test, counted.
  [va-matched-counts.json](results/sponsor-check/va-matched-counts.json) (130 counts of
  2026-10-15) and [VA-MATCHED-RESULT.md](results/sponsor-check/VA-MATCHED-RESULT.md): matched on
  condition, VA-led no-phase trials name a cognitive wording 2.21 times (1.99 to 2.45) and a
  hearing wording 1.77 times (1.24 to 2.52) as often as other trials; HV1 holds (p = 0.018) and
  HV2 holds. [VA-HEARING-READ.md](results/sponsor-check/VA-HEARING-READ.md) reads 20 of the VA
  hearing mentions: all 20 shut people out, many over telephone contact. VA-CHECK.md gains the
  matched section. The census rules are unchanged.
- After 0.5.0 (on main): `peryear_v03.py` 0.1.0,
  [PREREG-v0.3-PERYEAR.md](results/trend-check/PREREG-v0.3-PERYEAR.md) and
  [prereg-v0.3-peryear-counts.json](results/trend-check/prereg-v0.3-peryear-counts.json): the
  pre-registered per-year secondary, reduced to no-phase trials and the 9 kept controls (208 new
  counts). The families have the three steepest slopes, p = 0.0045. `va_matched.py` 0.1.0 and
  [PREREG-VA-MATCHED.md](results/sponsor-check/PREREG-VA-MATCHED.md) fix a condition-matched VA
  test before it is counted. The census rules are unchanged.
- After 0.5.0 (on main): `prereg_v03.py` 0.1.0,
  [PREREG-v0.3-RESULT.md](results/trend-check/PREREG-v0.3-RESULT.md) and
  [prereg-v0.3-counts.json](results/trend-check/prereg-v0.3-counts.json): the pre-registered
  trend test. H1 (a disability-specific rise in no-phase trials) holds, p = 0.0045, and H2 (none
  in the other trials) holds, p = 0.45. The VA no-phase secondary test gives p = 0.0015.
  TREND-CHECK.md gains section 5. The census rules are unchanged.
- After 0.5.0 (on main): `sponsor_check.py` 0.1.0 and
  [results/sponsor-check/VA-CHECK.md](results/sponsor-check/VA-CHECK.md): the high "other
  federal" rate comes from VA-led trials, whose criteria name disability 2.6 to 3.3 times as often
  as the registry while naming controls less often. [PREREG-v0.3.md](results/trend-check/PREREG-v0.3.md)
  and [prereg-v0.3.json](results/trend-check/prereg-v0.3.json) fix the next trend check before
  it is counted. The census rules are unchanged.
- After 0.5.0 (on main): `trend_check.py` 0.2.0 adds eight rare controls, pooled disability
  families and an exact rank-sum test, and
  [results/trend-check/TREND-CHECK.md](results/trend-check/TREND-CHECK.md) section 4 corrects the
  first version: the disability-specific rise is shown in no-phase trials, not in the others.
  "Informed consent" is now a reference phrase, not a control. The census rules are unchanged.
- After 0.5.0 (on main): `trend_check.py` 0.1.0 and
  [results/trend-check/TREND-CHECK.md](results/trend-check/TREND-CHECK.md), a check of the
  trend with the registry's own search and control phrases. The census rules are unchanged.
- 0.5.0: the accommodation flag counts an item only when it offers an accommodation. The bare
  words "accommodate" and "guardian" no longer count, nor does an item that mentions a parent, a
  child or an age under 18, says "without an interpreter" (or assistance, or a representative),
  or is unable to use large print, braille or sign language. In the exclusion criteria an item
  that requires, needs, uses or relies on one does not count either. New exclusion rules: sign
  language use (hearing) and large print or braille (visual), from every registry trial that
  names them. `sample_items.csv` samples accommodation items, and `check` and the browser page
  list them. The accommodation figures of v0.1.1 are withdrawn (see the correction above).
- 0.4.0: from the first 114 hand-labelled trials of the blind recall sample. Coordinated lists
  ("cognitive, visual or motor impairment", "visual or auditory impairment") and lists of verbs
  after "unable to" ("unable to hear, read, visualize or comprehend") are read for every member.
  New wordings: dementing, learning difficulties, limited cognitive ability, mental disability,
  decisionally impaired, mentally incapacitated, a condition that limits the ability to consent,
  guardianship, curatorship and safeguard of justice, cochlear implants, auditory impairment, motor
  deficits, spasticity, and conditions affecting ambulation. Literacy next to a negated language
  ("unable to read, not English speaking") now counts. New requirement rules: 20/20 vision, BCVA or
  better, no visual or auditory impairment, sufficient or adequate cognition, able to converse or to
  consent verbally, no communication problem, the 6-minute walk test and GMFCS I-III. New tool:
  `diff_rules.py`. The browser page uses the same rules.
- 0.3.0: from the hand check of the first full run ([PRECISION.md](results/v0.1.1/PRECISION.md)).
  Exception clauses ("except for hearing loss", "may be included (e.g. ...)", "other than ...")
  are read out before an item is classified. A visual veto drops eye findings that would only
  confound an eye exam, and a mobility veto drops a planned or required amputation. "Hemiplegic
  migraine", disability pensions and disability insurance no longer count. New trend controls:
  exclusion items per trial, disability items per 100 exclusion items, and each start year split
  into phased and no-phase trials (`by_year_design.csv`). `--seed` draws a fresh precision sample.
  The browser page uses the same rules.
- 0.2.0: reads the inclusion criteria for ability requirements in the six disability categories
  (census tables, `check`, the browser page and `recall_sample.py score`). The exclusion rules are
  unchanged from 0.1.0. The browser page now announces each result to screen readers even when it
  repeats the last one.
- 0.1.1: browser check, guide and blind recall sample.
- 0.1.0: first release.

## Licence

Code: Apache-2.0. Guide and result tables: CC BY 4.0. ClinicalTrials.gov data comes from the US
National Library of Medicine.

Made by MV2 of Munim, Inc. with AI agents. Questions and corrections are welcome as issues.
