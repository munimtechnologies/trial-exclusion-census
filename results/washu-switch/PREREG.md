# Did Washington University's trials switch consent wording? (pre-registration)

Written 2026-10-30 (about 21:50 UTC), before any trial text was fetched for this test, by AI agents
working for MV2 of Munim, Inc. Text CC BY 4.0; code Apache-2.0. Not yet checked by a person.

## Question
While grading results/consent-permission, AI agents noticed (not pre-registered, not graded) that
all 13 sampled trials led by Washington University School of Medicine (WashU) with NCT ids before
NCT06 carry the WashU clause on the stock consent line:

> Ability to understand and willingness to sign an IRB approved written informed consent document
> (or that of legally authorized representative, if applicable).

and all 7 with ids from NCT06 on carry a separate sentence instead:

> ... Legally authorized representatives may sign and give informed consent on behalf of study
> participants.

That rests on 20 records. This test asks whether the switch holds across the other 204 WashU-led
trials of the sponsor table. If it does, it is a dated change in one institution's template that
moved the representative route from a parenthesis ("if applicable") to a plain permission, visible
in the public registry, and a yearly indicator of representative paths has to allow for template
changes like it.

## Why it is new
Prior work counts consent-capacity exclusions in trial samples (McDonald et al. 2022; DeCormier
Plosky et al. 2022; Camanni et al. 2023) or reviews IRB policies on adults with impaired
decision-making capacity (Nguyen et al. 2025, PMC12227281). A web search on 2026-10-30 found no
source for the "may sign and give informed consent on behalf of study participants" sentence and
no study that dates a change in an institution's consent-line wording from registry text.

## Data
- results/consent-sponsor/consent-sponsor-trials.csv at commit
  dfa820661d6c06ec4eddee5e0ce1513c069a4dc6: its 224 WashU-led trials (washu_led True, including
  the 24 that are also NCI-linked).
- **Seen**: the 20 WashU-led trials read in results/consent-permission (its key.csv, group washu;
  listed in washu_switch.py). They are reported but left out of every graded share.
- **Unseen**: the other 204. No one has read their text for this question. Before writing this,
  the sponsor table was not opened for this test, so the number of unseen trials in each period
  is not known.
- Each trial's current eligibility text, fetched once from the ClinicalTrials.gov API v2 (fields
  NCTId, EligibilityCriteria, StartDate) in one request.

## Measures (washu_switch.py 0.1.0)
On the text with the API's Markdown backslashes removed and spaces collapsed, case-insensitive:
- **clause**: "or that of", up to three words, then "legal(ly) authorized/acceptable
  representative(s)".
- **sentence**: "legal(ly) authorized representative(s) [(LAR)] may sign and give [written]
  informed consent".
- **period**: early = NCT id before NCT06000000; late = NCT06000000 or later. NCT ids are given in
  registration order.
A trial can carry both, one or neither wording; all fetched unseen trials count in the
denominators. Shares have Wilson 95% intervals.

## Gates (if one fails, nothing is graded)
- P0 this file and the exact washu_switch.py that runs are on the repository's main branch
  before anything is fetched (the script checks this itself).
- S1 the table has 5,436 rows with its published columns; S2 WashU-led counts reproduce 165
  naming a path of 224; S3 all 20 seen ids are WashU-led, not NCI-linked, and named a path.
- S4 the API returns at least 218 of the 224 trials.
- S5 at least 40 unseen early and at least 15 unseen late trials.

## Predictions (unseen trials)
- **W1 (main)** The clause share among early trials minus the clause share among late trials is
  at least 40 percentage points, and the lower end of the Newcombe hybrid 95% interval for the
  difference is above 0.
- **W2** At least 60% of late trials carry the sentence.
- **W3** At most 10% of late trials carry the clause.
- **W4** At most 10% of early trials carry the sentence.
- **W5** At least 50% of early trials carry the clause. (A risk: 59 of the 224 WashU-led trials
  named no representative on 2026-10-16, and their periods are not known.)

## Also reported, not graded
Counts by NCT prefix (NCT00-NCT07) and by start year; the 24 NCI-linked WashU trials; the seen 20;
the last id carrying the clause, the first carrying the sentence, and how many trials fall
between them (an overlap means the switch was gradual, not a single date). A per-trial table
(washu-switch-trials.csv: id, period, start year, seen, NCI-linked, named a path on 2026-10-16,
fetched, clause, sentence).

## Code
washu_switch.py 0.1.0 and test_washu_switch.py (15 tests, no network). The run happens once, in
a sealed container, and prints both files' sha256. Thresholds, the cutoff and the seen ids are
constants pinned by a test.

## Limits
- Text matching, not reading: a reworded clause or sentence is missed, and the match says nothing
  about whether the route is for adults (in trials open to minors, the 2026-10-30 reading labelled
  WashU-clause trials unclear).
- Today's registry text: a trial whose entry was edited after the switch shows its new wording.
- NCT id order is registration order, not protocol-writing order.
- WashU-led means WashU is the lead sponsor in the registry, as in results/consent-sponsor.
- Only trials found by the two stock-line search phrases.
