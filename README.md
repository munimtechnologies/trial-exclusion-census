# trial-exclusion-census

How often do clinical trials exclude disabled people, and is it changing?

`trial-exclusion-census` reads the eligibility criteria of every interventional study on
[ClinicalTrials.gov](https://clinicaltrials.gov/) through its public API v2. It finds each trial's
exclusion criteria and flags items that exclude people by disability:

| Category | Examples of what it flags |
|---|---|
| cognitive | dementia, cognitive impairment, intellectual or developmental disability, MMSE/MoCA cut-offs |
| consent_capacity | "unable to provide informed consent", lack of decision-making capacity |
| visual | blindness, visual impairment, low vision, visual acuity limits (not "double-blind", and since 0.3.0 not eye findings that only matter to an eye exam) |
| hearing | deafness, hearing loss, hearing aids |
| communication | aphasia, dysarthria, illiteracy, "unable to speak/read/write" (but not "...English") |
| mobility | wheelchair use, non-ambulatory, "unable to walk", paralysis, amputation (since 0.3.0 not a planned amputation) |

It also counts the domains that earlier manual studies reported: psychiatric, substance use,
performance status (ECOG/Karnofsky), investigator discretion, English-only and general
"disability". Then it notes two things for each trial:

- **Accommodation**: whether the criteria mention any, such as an assistive device, a legally
  authorized representative, an interpreter, large print or a screen reader.
- **Condition-related**: whether a flagged exclusion matches the trial's own condition.
  Excluding vision loss from a glaucoma trial is not the same as excluding it from a diabetes trial.

### Ability requirements in the inclusion criteria (since 0.2.0)

People are also shut out by what the inclusion criteria *require*. Since 0.2.0 the census reads
the inclusion criteria too, for requirements in the same six categories:

| Category | Examples of what it flags |
|---|---|
| cognitive | "cognitively intact", "normal cognition", "MMSE of 24 or higher" |
| consent_capacity | "able to provide informed consent" when the item names no representative, guardian or parent; "able to understand the study" (but not "...English") |
| visual | "normal or corrected-to-normal vision", "able to see", "visual acuity of 20/40 or better" |
| hearing | "normal hearing", "able to hear" |
| communication | "able to read and write", "able to speak", "literate" (but not "...in English") |
| mobility | "able to walk 100 m", "ambulatory without assistance", "walks independently" |

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
- Only **7.0%** of the trials with a disability exclusion mention any accommodation anywhere in
  their criteria, such as a legally authorized representative, an interpreter or an assistive device.
- **The share rose over time.** Among trials that started from 2000 to 2008, 11.5% to 14.1% had a
  disability exclusion each year. The figure was 20.0% for 2016 starts and 24.9% for 2025 starts.
  Over the same years, substance-use exclusions fell from 18.7% to 15.8%, so not every kind of
  exclusion grew. Trials that start in 2026 are still being registered, and that year reads 27.5%.
- By lead sponsor class: other (mostly academic) 22.8%, industry 12.4%, NIH 14.7%, and other US
  federal agencies 38.3% (4,174 trials). NIH-led trials mention an accommodation most often (14.9%).
- By phase: trials with no phase (devices, behavioural studies, procedures) 25.7%; phase 1 10.7%,
  phase 2 14.1% and phase 3 13.5%.

**Precision.** 720 random flagged exclusion items were checked by hand, 60 per category, 360 of
them in the six disability categories ([PRECISION.md](results/v0.1.1/PRECISION.md)). Cognitive was 95% correct, consent capacity 100%,
hearing 95%, communication 97% (80% if literacy items are left out), mobility 90% and visual 75%.
The visual errors were eye findings in ophthalmology trials, and 0.3.0 removes them.

**What these numbers do not show yet.**

- Recall, meaning the exclusions the rules miss. The blind recall sample is drawn
  (`results/v0.1.1/recall/`) but not yet labelled.
- Whether the rise is real or comes from longer criteria and a growing share of unphased trials.
  0.3.0 adds both controls: items per trial and a phased/unphased split by year.
- Registry criteria are often a summary of the full protocol. On the four areas DeCormier Plosky
  et al. coded from full protocols, the registry text shows lower rates for vision (dementia
  trials 6.4% here against 34% there). Cognitive exclusions in dementia trials are close
  (50.7% against 42%).

## For study teams and IRB reviewers

- **Browser check** ([web/check.html](web/check.html), also at
  https://munimv2.github.io/inclusive-criteria/): paste a study's criteria and see each exclusion
  item that touches disability and each inclusion item that requires an ability, with an inclusive
  alternative to consider. It runs in the page, so nothing you paste is sent anywhere. It uses the
  same rules as the census, and `test_web_check.py` keeps the two identical.
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
check of the first run. They are reported next to the pre-registered numbers, never in place of
them, and checked on a fresh sample.

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
- `sample_items.csv`: up to 60 random flagged items per category (and per `required_<category>`),
  so the rules' precision can be checked by hand. `--seed` draws a fresh sample
- `trials.csv.gz`: one row per trial (NCT ID, year, sponsor class, phase, categories, required,
  number of exclusion items)

The cache keeps the fetched records, so revised rules can be re-run without fetching again.

`check` prints each flagged exclusion item and each inclusion item that requires an ability in one
trial's criteria, with an inclusive alternative to consider (for example, read-aloud or
large-print consent instead of excluding blind people).

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

## Limits

- A word list, not a reader. It flags what a criterion says, not whether that exclusion or
  requirement is justified for the study. It misses criteria worded in ways it does not know, and
  it can flag items that mention a word in passing. `sample_items.csv` and `recall_sample.py`
  exist to measure this.
- The hand checks so far were done by an AI agent working for MV2, one reader per item. Review by
  people with clinical and lived experience of disability is still to come.
- Illiteracy and "unable to read" count as communication exclusions. Reading is not a disability in
  itself, but these items shut out many people with intellectual, learning and print disabilities.
  `sample_items.csv` lets anyone count them separately.
- The inclusion-requirement rules are new in 0.2.0 and not yet validated. "Able to provide
  informed consent" is counted only when the same item names no representative, guardian or
  parent, but a representative allowed elsewhere in the criteria is not taken into account (the
  accommodation flag notes it).
- Inclusion sections are found only under an "Inclusion Criteria" heading. Criteria written as
  one unheaded list are read for exclusions only if they say "Exclusion criteria".
- "Condition-related" is a rough match between word lists and the trial's own condition and title.
- Registry text is what sponsors entered, which is often a summary of the full protocol.
- Information only. It is not medical, legal or IRB advice.

## Changes

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
