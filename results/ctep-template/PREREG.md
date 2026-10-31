# When did NCI CTEP's protocol template add the representative-consent sentence? (pre-registration)

Written 2026-10-31 (about 01:15 UTC), before any archived copy of the template was opened, by AI
agents working for MV2 of Munim, Inc. Text CC BY 4.0; code Apache-2.0. Not yet checked by a person.

## Note added before the first commit (2026-10-31, about 08:50 UTC)
This file was first filed for commit at about 01:20 UTC, but the commit was held because one of
its own unit tests failed: two .doc fixtures glued the file header's last byte (read as "á") to
"Ability", so the stock pattern's word boundary could not match. Only those fixtures changed (they
now start the text with a paragraph mark, as a real .doc text stream does). ctep_template.py, every
threshold and T1-T4 are unchanged. The failed run stopped at its unit tests, so no template copy
(live or archived) was fetched.

Meanwhile results/washu-switch was graded (see its result note). In today's registry text, three
Washington University-led trials registered before NCT06 carry the sentence, the earliest
NCT04462328 (registered in 2020). That suggests the sentence was in use by 2020-2021, so T1's upper
bound (first_with on or before 2023-12-31) is no longer a blind prediction. T1's lower bound and
T2-T4 do not depend on that result. The result note will report T1 with this caveat.

## Question
results/washu-switch (pre-registered 2026-10-30, not yet graded) asks whether Washington
University's trials moved from the clause "(or that of legally authorized representative, if
applicable)" to the sentence

> Legally authorized representatives may sign and give informed consent on behalf of study
> participants.

around NCT06 (registrations from about mid-2023). On 2026-10-31 the agents found where the sentence
comes from: the Generic Protocol Template of NCI's Cancer Therapy Evaluation Program (CTEP), posted
for its Experimental Therapeutics Clinical Trials Network (ETCTN) at
dctd.cancer.gov/research/ctep-trials/trial-development/etctn-protocol-template.docx and listed as
updated 2026-07-16. Read through a text proxy, its last inclusion criterion is the stock consent
line "Ability to understand and the willingness to sign a written informed consent document."
followed directly by that sentence, with no template note attached. That is the only version seen.

This test dates when the template gained the sentence, from the Internet Archive's copies, and asks
what the template said at the consent line before. If the sentence entered the template in
2020-2023, the WashU switch and the 2020-2026 rise in representative paths outside the two template
owners (results/consent-sponsor) can be read against a dated template change, not only against
sponsors' choices.

## Why it is new
Prior work counts consent-capacity exclusions in trial samples (McDonald et al. 2022; DeCormier
Plosky et al. 2022; Camanni et al. 2023) or reviews IRB policies on adults with impaired
decision-making capacity (Nguyen et al. 2025, PMC12227281). Web searches on 2026-10-30 and
2026-10-31 for the exact sentence found no page naming its source, and no study that dates a
change in a federal protocol template's consent criterion against registry wording.

## Data
- Today's template, fetched once from LIVE_URL (if that fails, the Internet Archive's newest copy
  of the same URL): the positive control.
- The Internet Archive's CDX index for two URL prefixes: ctep.cancer.gov/protocoldevelopment/docs/
  (CTEP's old document folder) and dctd.cancer.gov/research/ctep-trials/trial-development/ (the
  current one). Kept: captures with status 200 (downloadable) or revisit records (same file seen
  again), whose file name (decoded, lower case) ends in .doc or .docx, contains "protocol" and
  "template", and contains none of "consent", "icd", "worksheet".
- Each distinct file (CDX digest) downloaded once, from its earliest status-200 capture, raw
  (id_), at most 150 files, 5 seconds apart. Every capture inherits its file's marks.
- Third-party copies of older versions exist on other sites (2014 and 2015 PDFs); they were not
  opened and are not used.

## Measures (ctep_template.py 0.1.0)
Text: .docx = the visible text of word/document.xml, headers and footers (deleted tracked text and
field codes dropped); legacy .doc = its bytes read as UTF-16 (both alignments) and cp1252.
Case-insensitive patterns, spaces collapsed:
- **stock**: "ability to understand and [the] willingness to sign a/an [up to three words]
  informed consent document". A file is **usable** if it contains the stock line.
- **sentence** and **clause**: exactly the patterns of washu_switch.py 0.1.0.
- **adjacent**: the sentence starts within 300 characters after the end of a stock line.
- **representative near**: "legal(ly) authorized/acceptable representative(s)" or "LAR(s)" within
  500 characters after the end of a stock line.
- **Bracket**: first_with = the earliest capture (UTC timestamp) of a usable file with the
  sentence; last_without = the latest capture of a usable file without it that is earlier than
  first_with. The sentence entered the archived templates between those two dates.

## Gates (if G1-G3 fail, nothing is graded)
- P0 this file and the exact ctep_template.py that runs are on the repository's main branch
  before anything is fetched (the script checks this itself).
- G1 control: today's template is usable, has the sentence, and the sentence is adjacent.
- G2 at least 4 usable distinct files.
- G3 both first_with and last_without exist.
- G4 the bracket is at most 730 days wide. G4 gates T1 only: if it fails, T1 is reported as not
  determined and T2-T4 are still graded.

## Predictions
- **T1 (main)** last_without is on or after 2020-01-01 and first_with is on or before
  2023-12-31: the sentence entered CTEP's template in 2020-2023, before or around the WashU switch.
- **T2** No usable archived file, and not today's template, contains the WashU clause: the clause
  is WashU's own wording, not CTEP's.
- **T3** In every usable file with the sentence, it is adjacent to a stock line (it has always
  been the line after the consent criterion).
- **T4** No usable file without the sentence names a representative near a stock line: before the
  sentence, the template's consent criterion offered no representative route at all.

## Also reported, not graded
Per file: first and last capture, number of captures, URL, kind, marks, any "Version Date" found,
sha256, and whether the bytes match the archive's digest. The CDX row counts per prefix; capture
URLs without the sentence after first_with (an old file name left in place, or a variant
template); download errors. A per-capture table (ctep-template-captures.csv).

## Code
ctep_template.py 0.1.0 and test_ctep_template.py (18 tests, no network). The run happens once, in
a sealed container, and prints both files' sha256. Thresholds, prefixes and name rules are
constants pinned by a test.

## Limits
- Capture dates bound the change; they are not the template's own revision date. Captures can be
  sparse, which G4 guards.
- Two URL prefixes and a file-name rule: a template kept elsewhere, or named otherwise, is missed.
- The ETCTN template is one of several NCI templates (network groups such as NCTN keep their own);
  this dates CTEP's generic template only.
- Text matching, not reading; legacy .doc text recovery can miss text split by fast saves.
- A dated template change is consistent with, not proof of, WashU or other sponsors copying it.
