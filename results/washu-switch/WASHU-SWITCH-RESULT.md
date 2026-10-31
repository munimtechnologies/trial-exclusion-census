# Did Washington University's trials switch consent wording? (result)

The pre-registered test in PREREG.md (this folder), run once on 2026-10-31. Order of events, all UTC:
the pre-registration and washu_switch.py were committed at 21:36 on 2026-10-30 (commit f7944ec);
the run found both on main at its first poll and fetched the registry text at 2026-10-31T05:53:44Z.
Run and written up by AI agents working for MV2 of Munim, Inc.; not yet checked by a person.
Text CC BY 4.0; code Apache-2.0.

## In short
Trials led by Washington University School of Medicine (WashU) did move from WashU's clause on the
stock consent line ("or that of legally authorized representative, if applicable") to the separate
sentence "Legally authorized representatives may sign and give informed consent on behalf of study
participants". But the move was gradual over about four years of registrations, not a single date.
Among the 204 WashU-led trials not read before:
- Before NCT06 (149 trials): the WashU clause in 100 (67.1%; 95% interval 59.22-74.14%), the sentence in 3 (2.0%; 95% interval 0.69-5.75%).
- From NCT06 on (55 trials): the sentence in 32 (58.2%; 95% interval 45.03-70.26%), the clause in 6 (10.9%; 95% interval 5.10-21.83%).

No trial carries both wordings.

**Three of five predictions hold.** The main one (W1) holds. W2 and W3, the two bounds on the newest
registrations, each miss their bound by one trial.

## Gates
All passed. P0: the pre-registration and the exact script were on main at the first poll. S1: the
sponsor table (commit dfa8206; sha256 begins d56316c74fcf) has its 5,436 rows. S2: WashU-led counts reproduce 165 naming a path of 224. S3: the 20 seen trials are WashU-led, not NCI-linked, and
named a path. S4: the API returned 224 of 224. S5: 149 early and 55 late unseen trials.

## Predictions
- **W1 (main): holds.** The clause share before NCT06 minus the share from NCT06 on is 56.2 percentage points (Newcombe 95% interval 42.74 to 65.33 points); needed at least 40 with the lower end above 0.
- **W2: fails.** The sentence is in 32 of 55 late trials (58.2%); needed at least 60% (33 of 55).
- **W3: fails.** The clause is in 6 of 55 late trials (10.9%); needed at most 10% (5 of 55).
- **W4: holds.** The sentence is in 3 of 149 early trials (2.0%); needed at most 10%.
- **W5: holds.** The clause is in 100 of 149 early trials (67.1%); needed at least 50%.

## Why W2 and W3 missed (not pre-registered; reported as a check)
As pre-registered, every fetched unseen trial counts in the denominators. 15 of the 55 late trials and 44 of the 149 early trials named no representative, guardian or surrogate in the census reading of 2026-10-16, and carry neither wording today.
Among the unseen trials that did name one:
- Before NCT06: the clause in 100 of 105 (95.2%), the sentence in 3 of 105 (2.9%).
- From NCT06 on: the sentence in 32 of 40 (80.0%), the clause in 6 of 40 (15.0%).

So W2 missed because of trials with no representative route at all, and W3 missed because the
clause stayed in use in six newer registrations.

## When did it switch? (not pre-registered, not graded)
- The first trial with the sentence is NCT04462328 and the last with the clause is NCT06648434; 52 fetched WashU-led trials from one to the other (the 20 read before included) carry one wording or the other.
- Among unseen trials from NCT06 on that name a representative, the 13 up to NCT06648434 split 6 clause, 6 sentence and 1 neither; of the 27 after it, 26 carry the sentence and 1 neither.
- The 20 trials read before: clause 13, sentence 7 (all 13 before NCT06 with the clause, all 7 from NCT06 on with the sentence), which is what prompted this test.
- The 24 WashU-led trials that are also NCI-linked: clause 11, sentence 7, neither 6.
- Registration dates, looked up from the ClinicalTrials.gov API on 2026-10-31 after grading (not in
  the committed files and not covered by the tests): the three early trials with the sentence were
  first submitted on 2020-07-02 (NCT04462328), 2021-04-15 (NCT04852328) and 2022-08-26
  (NCT05521984); the six late trials with the clause between 2023-09-20 (NCT06063564) and
  2024-10-15 (NCT06648434). All nine were last updated in 2026, so today's wording may postdate
  their registration.

All 224 fetched trials (seen included) by NCT prefix:

| Prefix | Trials | Clause | Sentence | Neither |
|---|---|---|---|---|
| NCT00 | 5 | 0 | 0 | 5 |
| NCT01 | 8 | 4 | 0 | 4 |
| NCT02 | 34 | 27 | 0 | 7 |
| NCT03 | 34 | 29 | 0 | 5 |
| NCT04 | 46 | 34 | 2 | 10 |
| NCT05 | 35 | 19 | 1 | 15 |
| NCT06 | 31 | 6 | 15 | 10 |
| NCT07 | 31 | 0 | 24 | 7 |

## Where the sentence comes from
The same sentence follows the stock consent line in the current Generic Protocol Template of NCI's
Cancer Therapy Evaluation Program (CTEP) for its Experimental Therapeutics Clinical Trials Network,
listed as updated 2026-07-16. When CTEP's template gained the sentence is a separate pre-registered
test (results/ctep-template) that has not run yet. This result alone does not show that WashU took
the sentence from CTEP.

## What it means
- One institution's registry wording moved, over registrations from 2020 to 2024, from a
  parenthetical "if applicable" route to a plain sentence that permits representative consent.
- A yearly indicator of representative paths that counts wordings will pick up template changes
  like this as trends. It should be read alongside the template history and a read sample (see
  results/consent-permission, where 16 of 20 WashU-led mentions were real adult permissions).

## Limits
- Text matching, not reading: a reworded clause or sentence is missed, and the match does not say
  whether the route is for adults.
- Today's registry text: a trial edited after registration shows its new wording.
- NCT ids give registration order, not the order protocols were written.
- WashU-led means WashU is the lead sponsor in the registry, as in results/consent-sponsor.
- One run by AI agents, not yet checked by a person.

## Files
- washu_switch.py 0.1.0 (sha256 069ddbe740aa8dca5f302dbd9a1ca2c3435b03c103c80f4d2f78b8eedfe2807d) and test_washu_switch.py (sha256 afc97784ea3defec9d69b402be40922f25da7ae4d913b9e1f088c41b015ad2e7), unchanged since the pre-registration commit; their 15 tests passed in the run.
- result.json, result.txt and washu-switch-trials.csv: the run's output, unchanged.
- test_washu_switch_result.py re-grades from washu-switch-trials.csv with washu_switch.py, checks
  the result against the saved run, and checks every figure in this note except the registration
  dates above, plus the hashes.
