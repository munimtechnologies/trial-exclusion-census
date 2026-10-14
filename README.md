# trial-exclusion-census

How often do clinical trials exclude disabled people, and is it changing?

`trial-exclusion-census` reads the eligibility criteria of every interventional study on
[ClinicalTrials.gov](https://clinicaltrials.gov/) through its public API v2. It finds each trial's
exclusion criteria and flags items that exclude people by disability:

| Category | Examples of what it flags |
|---|---|
| cognitive | dementia, cognitive impairment, intellectual or developmental disability, MMSE/MoCA cut-offs |
| consent_capacity | "unable to provide informed consent", lack of decision-making capacity |
| visual | blindness, visual impairment, low vision, visual acuity limits (not "double-blind") |
| hearing | deafness, hearing loss, hearing aids |
| communication | aphasia, dysarthria, "unable to speak/read/write" (but not "...English") |
| mobility | wheelchair use, non-ambulatory, "unable to walk", paralysis, amputation |

It also counts the domains that earlier manual studies reported: psychiatric, substance use,
performance status (ECOG/Karnofsky), investigator discretion, English-only and general
"disability". Then it notes two things for each trial:

- **Accommodation**: whether the criteria mention any, such as an assistive device, a legally
  authorized representative, an interpreter, large print or a screen reader.
- **Condition-related**: whether a flagged exclusion matches the trial's own condition.
  Excluding vision loss from a glaucoma trial is not the same as excluding it from a diabetes trial.

Results come by start year, lead sponsor class and phase. There is also a replication check
against the four therapeutic areas that DeCormier Plosky et al. coded by hand.

## For study teams and IRB reviewers

- **Browser check** ([web/check.html](web/check.html), also at
  https://munimv2.github.io/inclusive-criteria/): paste a study's criteria and see each exclusion
  item that touches disability, with an inclusive alternative to consider. It runs in the page, so
  nothing you paste is sent anywhere. It uses the same rules as the census, and
  `test_web_check.py` keeps the two identical.
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
  intellectual disability.
- "'Being disabled' as an exclusion criterion for clinical trials: a scoping review" (2023,
  [PMC10626873](https://pmc.ncbi.nlm.nih.gov/articles/PMC10626873/)): 2,710 completed trials from
  2010-2020 for the leading causes of disability-adjusted life-years. 35.3% had explicit and 44.5%
  had implicit disability exclusions.

No open, registry-wide and repeatable count existed, and none showed a trend by year. This tool
does both, and its rules are open for anyone to check, re-run and argue with. NIH's Strategic Plan
for Disability Health Research FY26-FY30 makes inclusion in clinical research an objective, so a
yearly count is useful.

The word rules in v0.1.0 were written and published **before any registry result was seen**.

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
python exclusion_census.py check criteria.txt     # one trial's criteria, with alternatives to consider
python -m unittest -v
```

`census` pages through the API with a pause between requests. It writes:

- `summary.json` and `results.md`
- `by_year.csv`, `by_sponsor.csv`, `by_phase.csv` and `plosky_areas.csv`
- `sample_items.csv`: up to 60 random flagged items per category, so the rules' precision can be
  checked by hand
- `trials.csv.gz`: one row per trial (NCT ID, year, sponsor class, phase, categories)

The cache keeps the fetched records, so revised rules can be re-run without fetching again.

`check` prints each flagged exclusion item in one trial's criteria, with an inclusive alternative
to consider (for example, read-aloud or large-print consent instead of excluding blind people).

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
"able to walk 100 m unaided"), or both. The census reads only the exclusion section, so the `i`
marks show how much an exclusion-only count cannot see. `score` reports per-category precision
and recall on the random sample, with Wilson 95% intervals, and lists every miss. It re-runs the
current rules on the same trials, so a revised rule set can be compared on the same sample.

## Limits

- A word list, not a reader. It flags what a criterion says, not whether that exclusion is
  justified for the study. It misses exclusions worded in ways it does not know, and it can flag
  items that mention a word in passing. `sample_items.csv` and `recall_sample.py` exist to
  measure this.
- "Condition-related" is a rough match between word lists and the trial's own condition and title.
- Registry text is what sponsors entered, which is often a summary of the full protocol.
- Information only. It is not medical, legal or IRB advice.

## Licence

Code: Apache-2.0. Guide and result tables: CC BY 4.0. ClinicalTrials.gov data comes from the US
National Library of Medicine.

Made by MV2 of Munim, Inc. with AI agents. Questions and corrections are welcome as issues.
