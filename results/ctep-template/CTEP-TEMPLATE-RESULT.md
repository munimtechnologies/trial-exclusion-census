# When did NCI CTEP's protocol template add the representative-consent sentence? (result)

The pre-registered test in PREREG.md (this folder), run once on 2026-10-31. Order of events, all UTC:
the pre-registration and ctep_template.py were committed at 08:40:26 on 2026-10-31 (commit 219a278);
the run found both on main at its first poll and started fetching at 2026-10-31T09:12:59Z. (The dated
note in PREREG.md says it was written at about 08:50 UTC; the commit shows it was about ten minutes
earlier.) Run and written up by AI agents working for MV2 of Munim, Inc.; not yet checked by a
person. Text CC BY 4.0; code Apache-2.0.

## In short
The sentence "Legally authorized representatives may sign and give informed consent on behalf of
study participants" is in the protocol templates of NCI's Cancer Therapy Evaluation Program (CTEP)
today, right after the stock consent line "Ability to understand and the willingness to sign a
written informed consent document". In the Internet Archive's copies, the sentence is not in any archived copy of CTEP's protocol templates up to 2022-07-09, and is in every copy from 2023-11-15 on.
Before it, the consent criterion named no representative at all.
- 28 distinct template files (49 archived captures, 2011-04-03 to 2026-07-23) were downloaded, every one matched the archive's digest, and every one has the stock consent line.
- 16 files (26 captures) do not have the sentence; the last of them was captured on 2022-07-09.
- 12 files (23 captures) have it; the first was captured on 2023-11-15, 494 days later.

**All four predictions hold.**

## Gates
All passed. P0: the pre-registration and the exact script were on main at the first poll. G1: today's template (fetched directly; sha256 begins 97be84e6f4f4) has the stock line with the sentence right after it, and it is byte for byte the Internet Archive's copy of 2026-07-23.
G2: 28 usable files (at least 4 needed). G3: both sides of the bracket exist. G4: the bracket is 494 days (at most 730 allowed).
The two CDX prefixes returned 4,235 and 804 rows, both complete; no download failed.

## Predictions
- **T1 (main): holds.** The last capture without the sentence is 2022-07-09 (on or after 2020-01-01 needed) and the first with it is 2023-11-15 (on or before 2023-12-31 needed).
  As the dated note in PREREG.md says, the upper bound was no longer a blind prediction when the
  test ran. The lower bound was, and it is the informative half: the template did not carry the
  sentence through mid-2022.
- **T2: holds.** WashU's clause ("or that of legally authorized representative, if applicable") is in none of the 28 files and not in today's template.
- **T3: holds.** In all 12 files with the sentence it starts within 300 characters after the stock line.
- **T4: holds.** None of the 16 files without the sentence names a legally authorized or acceptable representative, or a LAR, within 500 characters after the stock line.

## The templates' own version dates (not pre-registered, not graded)
The files print dates after the words "Version Date". March 16, 2012 is in 26 of the 28 files (the two captured in 2011 print none); the other date changes from version to version and is always earlier than the file's first capture.
- Last versions without the sentence: June 13, 2022 (Generic Protocol Template for Cancer Treatment Trial) and February 10, 2022 (Organ Dysfunction Protocol Template).
- First version with it: August 4, 2023, in both templates.

So the sentence was added in a version dated after June 13, 2022 and no later than August 4, 2023.
A version in between that the Internet Archive never captured would narrow this further.
No capture without the sentence appears after 2023-11-15.

## Against the WashU switch (not pre-registered)
results/washu-switch found that trials led by Washington University School of Medicine (WashU)
moved from WashU's clause to this sentence over registrations from 2020 to 2024.
- The bulk of that move, in registrations from NCT06 on, comes after CTEP's templates gained the
  sentence. That fits WashU taking the sentence from CTEP, but does not show it.
- Three WashU-led trials registered before NCT06 carry the sentence today: NCT04462328,
  NCT04852328 and NCT05521984, registered in 2020, 2021 and 2022, all before the first template
  version with the sentence. All three were last updated in 2026. Either they gained the sentence
  in later edits, or the sentence was in use before CTEP's template carried it and came from
  somewhere else first. Today's registry text cannot tell these apart; archived copies of their
  registry pages can, and that is the next pre-registered test (results/washu-history).
- WashU's clause never appears in CTEP's templates (T2): it is WashU's own wording.

## What it means
- CTEP's protocol templates gave no route for a representative to consent at the consent criterion
  from 2011 to mid-2022, and have given a plain one since a version dated by August 4, 2023.
- The 2020-2026 rise in representative paths outside the two template owners
  (results/consent-sponsor) can now be read against a dated change in a widely used federal
  template, not only against sponsors' own choices. Whether other sponsors copied it is not
  tested here.

## Limits
- Capture dates and printed version dates bound the change; CTEP's own change log was not read.
- Two URL prefixes and a file-name rule: a template kept elsewhere, or named otherwise, is missed.
- CTEP's templates only; NCTN network groups and institutions keep their own templates.
- Text matching, not reading.
- One run by AI agents, not yet checked by a person.

## Files
- ctep_template.py 0.1.0 (sha256 9c49174bb2c868c788e3b1aeb03d5ddab5ede44bc00b2c0abe02979223464688) and test_ctep_template.py (sha256 41cec9c40d8d25f4aef13a130e3426c191e1ab86c31b0e10155e29c643b7f7ad), unchanged since the pre-registration commit; their 18 tests passed in the run.
- result.json, result.txt and ctep-template-captures.csv: the run's output, unchanged.
- test_ctep_template_result.py re-grades from the saved per-capture table and per-file marks with
  ctep_template.py, rebuilds the table, the file list and the printed result, and checks every
  figure in this note except the WashU registration years, plus the hashes.
