# Where each quoted number is checked

The figures most often quoted from this repository, and the offline test that checks each one.
Run them all with `python -m unittest discover` (no network).

- **recomputed**: the test derives the number from saved data or labels with the repository's code;
- **summary**: the test checks the number against a stored summary file, not recounted from trial rows;
- **consistency**: the test checks that documents agree with each other.

Readings and labels behind these numbers were made by AI agents working for MV2 of Munim, Inc.,
one reader per item, and no person has checked them yet. A test can show that a number follows
from those readings; it cannot show that the readings are right.

| Figure | Test | Kind |
|---|---|---|
| First run: 20.1% of 450,052 trials; phase shares 25.7 / 10.7 / 14.1 / 13.5% | test_readme_first_run.py | summary (results/v0.1.1/summary.json) |
| 0.4.0 run: 22.4% (22.37%) of 450,201 trials; 33.7 / 11.4 / 16.4 / 12.7% | test_results_v040.py, test_readme_bound.py | summary (the tests check the two-decimal values 22.37 / 33.74 / 11.38 / 16.36 / 12.69, which round to the figures quoted here), and recomputed from diff_summary.json |
| Start-year ratios 1.84 / 1.55 / 1.42 times | test_results_v040.py (test_quoted_years) | summary (ratio of stored by-year shares) |
| Telephone 2.45 / 2.13 / 1.93; controls 0.24-0.61; consent 0.78; non-VA 2.41 | test_phone_matched.py | recomputed |
| 7,620 telephone trials against 202,729 other no-phase trials | test_quoted_numbers.py | recomputed (sum of six strata) |
| Phone requirement 2.58 (2.04-3.24), visual 1.62, top control 1.08; 1,890 of 7,421 | test_phone_requirement_result.py | recomputed |
| 12 of 20 phone-tied; 16 of 20 phone-access condition | test_phone_requirement_result.py | recomputed from reading labels |
| 4 of 20 (an earlier prediction that failed) | test_phone_hearing_read.py, test_phone_requirement_result.py | recomputed from reading labels |
| VA 2.21 (1.99-2.45), 1.77, 2.81, p 0.018 | test_va_matched.py | recomputed |
| Trend p 0.0045 / 0.0204 / 0.453, rank sum 33 | test_prereg_v03.py | recomputed |
| Family ratios 3.07 / 2.36 / 1.74 | test_quoted_numbers.py | recomputed from saved counts |
| Consent line 4,059 + 1,377; about 450 (392-502); 8.3%; 0 of 32 | test_consent_near_variant.py, test_consent_missed_read.py, test_readme_notes.py | recomputed by the notes' own tests; the README checked against the notes |
| Consent line names another path: 4.3% (started 2019 or earlier) vs 19.2% (2020-2026) | test_readme_notes.py (test_consent_result) | consistency: the README matches the note's table, and both shares are recomputed from its counts (103 of 2,419; 304 of 1,587) |
| Held-out recall and precision 16/16, 16/22, 13/14, 13/19; 19/78 and 13/78; mobility 0/2 and 0/3 | test_recall_numbers.py | recomputed from labels |
| Precision: 720 items, 75% to 100% by category | test_precision_numbers.py | consistency only (the verdicts are recorded in results/v0.1.1/PRECISION.md) |
| Accommodation flag: 0.4.0 matched 16, of which 5 offer one (31%, 14-56%); the current rules flag 9 | test_accommodation_flag.py, test_wording.py | recomputed (current rules run on the sample); the 16 rows and 5 offers are the note's table |

The 0.4.0 accommodation count (16 trials) was also run from that version's code in a sandbox on
2026-10-28; no test here runs old rule versions.

CC BY 4.0. Made by MV2 of Munim, Inc. with AI agents.
