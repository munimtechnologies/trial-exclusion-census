# Did WashU's trials use the representative-consent sentence before CTEP's template did? (result: not graded)

The pre-registered test in PREREG.md (this folder), run once from 2026-10-31T18:08:18Z. The
pre-registration and washu_history.py were committed at 11:28:24 UTC on 2026-10-31
(commit f9ae5eb), and the run found both on main at its first poll. Run and written up by AI agents
working for MV2 of Munim, Inc.; not yet checked by a person. Text CC BY 4.0; code Apache-2.0.

## In short
**Gate A3 failed, so nothing is graded: H1, H2 and H3 stay open.**
- The run stopped reading at its 150-minute limit (9,140 seconds elapsed) after 81 of the 224 trials.
- Those 81 trials took 162 Internet Archive index queries; 3 were not answered (HTTP 503), and 1 of 86 page downloads failed.
- None of the 9 boundary trials the main questions turn on (NCT04462328, NCT04852328, NCT05521984 and six later ones) was reached, so H2 could not be tried at all.

The Internet Archive answered far more slowly than the plan assumed: about 113 seconds per trial on average, retries and page downloads included.
The trials were read in NCT order, so the newer trials, where the sentence is, came last.

## What the run did read (not graded, and not evidence for H1)
- 75 trials had a usable page captured on or before 2022-07-09; none of the 75 carries the sentence.
- All 56 of them that carry WashU's clause today carried it on that page too; the other 19 carry neither wording, then and now.
- Every one of the 75 was registered before NCT04 (NCT00240162 to NCT03982004), long before the template change.

These are old trials that never adopted the sentence, so their pages say little about whether
WashU used it before CTEP. H1 is left ungraded, as the pre-registration requires; it is not
re-tuned or re-read here.

## What comes next
The question moves to a smaller, faster pre-registered test, results/sentence-origin. It reads
only the 30 trials that carry the sentence today and were first submitted before CTEP's first
template version with it (August 4, 2023), including the three early WashU trials. H2 is carried
over as its S4, with the page window narrowed to captures up to 2023-08-03. The ctep-spread result added SWOG Cancer Research Network as a second large
user of the sentence, so the new test also asks when it entered SWOG's trials.

## Files
- washu_history.py 0.1.0 (sha256 76fd50842103c79b22ea5d143ca4219a2ac151e31a788ceabfdb8364d75b78cc) and test_washu_history.py (sha256 aee3c3c1a464e7a56108f7fbc92954fe86a1383656c2ecb6081a5ebea7c03e20), unchanged since the pre-registration commit; their 20 tests passed in the run.
- result.json, result.txt and washu-history-pages.csv: the run's output, unchanged.
- test_washu_history_result.py rebuilds the printed result from result.json and checks every
  figure in this note and the hashes.
