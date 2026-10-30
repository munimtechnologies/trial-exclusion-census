# Where the stock consent line's representative paths come from (result)

The pre-registered test in PREREG.md (this folder), run once on 2026-10-30. The pre-registration
was committed at 06:52 UTC (commit e3ea4be); sponsors were fetched from 2026-10-30T08:31:35Z.
Run and written up by AI agents working for MV2 of Munim, Inc.; not yet checked by a person.
Text CC BY 4.0; code Apache-2.0.

## In short
Trials linked to the National Cancer Institute (NCI) or led by Washington University School of
Medicine (WashU), the two template owners, are 1,770 of 5,436 trials (32.6%) with the stock
consent line, but they hold 425 of the 666 trials that name a representative, guardian or
surrogate (63.8%). So the paths do cluster in the templates' trials. The main prediction (P3)
also capped the owners' share of trials at 30%, and it is 32.6%, so **P3 fails as written**.

Outside the two templates the share naming a path still rose 3.3 times, from 3.2% (starts 2019
or earlier) to 10.5% (starts 2020-2026), so the rise since 2020 is broad, not only the templates
(P5 fails). Outside the templates, industry-led trials and trials led by universities and
hospitals name a path about equally rarely, 6.2% and 6.4% (P4 fails).

## Gates
All four passed: the table (sha256 begins c7f87d926976) has 5,473 rows and the columns used;
5,436 trials are in the population, 4,059 with the exact line; 422 exact-line trials have
adult_path; the API returned a lead sponsor for 5,436 of 5,436.

## Predictions
- **P1: holds.** NCI-linked trials: 278 of 1,570 (17.7%) name a path;
  Neither: 241 of 3,666 (6.6%). Risk ratio 2.69 (2.29-3.17); needed at least 1.5 with the lower
  end above 1.
- **P2: holds.** (A check of a known pattern.) WashU-led trials: 165 of 224 (73.7%). Risk ratio
  11.21 (9.69-12.95); needed at least 3.
- **P3 (main): fails.** Template owners hold 63.8% of trials naming a path (needed at least 40%:
  met) but make up 1,770 of 5,436 trials (32.6%) (needed at most 30%: not met). Within the owners,
  425 of 1,770 (24.0%) name a path.
- **P4: fails.** Among Neither trials, industry-led: 30 of 481 (6.2%); led by OTHER-class
  sponsors (universities, hospitals): 200 of 3,138 (6.4%). Needed industry at most half.
- **P5: fails.** Among Neither trials, starts 2019 or earlier: 62 of 1,953 (3.2%); starts
  2020-2026: 174 of 1,663 (10.5%). That is 3.30 (2.48-4.37) times; needed less than 2.

## Also reported (not graded)
Share naming a path, by start period:

| Group | Starts 2019 or earlier | Starts 2020-2026 |
|---|---|---|
| NCI-linked | 70 of 1,051 (6.7%) | 195 of 499 (39.1%) |
| WashU-led | 59 of 76 (77.6%) | 106 of 148 (71.6%) |
| Neither | 62 of 1,953 (3.2%) | 174 of 1,663 (10.5%) |

NCI-linked trials moved from about twice the Neither share to almost four times it, which fits
NCI's newer template sentence ("Legally authorized representatives may sign and give informed
consent on behalf of study participants", see results/consent-phrase/CONSENT-RESULT.md). The WashU
clause was already in most WashU-led trials before 2020.

All 5,436 trials: 666 of 5,436 (12.2%). Both NCI-linked and WashU-led: 18 of 24 (75.0%).

By lead sponsor class (all trials): INDUSTRY 31 of 493 (6.3%); NIH 171 of 741 (23.1%); OTHER
436 of 4,136 (10.5%); every other class pooled 28 of 66 (42.4%).

Adult-only trials: risk ratio NCI-linked vs Neither 3.20 (2.66-3.86);
WashU-led vs Neither 14.24 (12.03-16.86); the owners hold 68.1% of the trials naming a path.

The lead sponsors with the most trials naming a path. The pre-registration asked for
organisations only, so one individual investigator listed as lead sponsor (7 of 7 trials) is
left out of this table; the script's saved list in consent-sponsor.json has all 15 as the
registry gives them.

| Lead sponsor | Trials | Naming a path |
|---|---|---|
| National Cancer Institute (NCI) | 725 | 170 |
| Washington University School of Medicine | 224 | 165 |
| Wake Forest University Health Sciences | 136 | 25 |
| ECOG-ACRIN Cancer Research Group | 20 | 18 |
| City of Hope Medical Center | 123 | 17 |
| M.D. Anderson Cancer Center | 265 | 14 |
| H. Lee Moffitt Cancer Center and Research Institute | 77 | 11 |
| Fred Hutchinson Cancer Center | 28 | 10 |
| Northwestern University | 107 | 9 |
| Sun Yat-Sen Memorial Hospital of Sun Yat-Sen University | 20 | 9 |
| Dana-Farber Cancer Institute | 231 | 7 |
| Memorial Sloan Kettering Cancer Center | 60 | 7 |
| Case Comprehensive Cancer Center | 102 | 6 |
| Gradalis, Inc. | 15 | 5 |

## What it means
- Where a trial with the stock line writes down a representative path, it is usually an
  NCI-linked or WashU-led trial: two thirds of the mentions come from a third of the trials. A
  template change reaches many trials at once; NCI-linked trials went from 6.7% to 39.1%.
- The templates are not the whole story. Outside them, mentions also tripled. A yearly indicator
  for this line should be reported overall and for trials outside the two templates, so that a
  change in one template does not hide or inflate change everywhere else.
- Outside the templates, industry trials are not behind academic ones: both are near 6%.

## Limits
- Mentions, not permissions. In the earlier reading, 30 of 50 exact-line mentions were adult
  permissions, and one ECOG-ACRIN trial names a representative only to exclude people who have
  one. Group shares of real permissions may differ from these shares of mentions.
- Registry text is the current version only, so a start year is not the year the wording was
  written.
- Sponsor and collaborator fields are what the registry listed on 2026-10-30. An NCI-funded trial
  that does not list NCI counts as Neither, so the NCI-linked group is a floor.
- Only trials found by the two search phrases (registry data of 2026-10-16).
- P3's 30% bound on the owners' share of trials was set before any sponsor was seen. The result,
  32.6%, is near it; it is reported as a fail all the same.

## Files
- consent_sponsor.py 0.1.0 (sha256 db510fa197b561a4b2f3c4631fdcc24e0d82c9c59485a87a22f7d24e72297176)
  and test_consent_sponsor.py
  (sha256 1c1576efd26822056e3da3f074ba7f6e5472231567650fd42af02fd35e861413), at the repository
  root, byte for byte as run; their 16 tests passed in the sealed run before the fetch.
- consent-sponsor.json, consent-sponsor.txt and consent-sponsor-trials.csv: the run's output,
  unchanged. The csv gives each trial's lead sponsor and class as the registry lists them.
- test_consent_sponsor_result.py recomputes the saved analysis from the csv, checks the saved
  text output and every figure in this note, and checks the two hashes above.
