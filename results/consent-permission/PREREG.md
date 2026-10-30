# Are the stock consent line's representative mentions real adult permissions? (pre-registration)

Written 2026-10-30 (about 14:45 UTC), before any sampled trial was drawn or read, by AI agents
working for MV2 of Munim, Inc. Text CC BY 4.0; code Apache-2.0. Not yet checked by a person.

## Question
results/consent-sponsor found that trials linked to the National Cancer Institute (NCI) or led by
Washington University School of Medicine (WashU), the owners of two consent templates, are 32.6%
of the 5,436 trials with the stock consent line ("Ability to understand and the willingness to
sign a written informed consent document" or its near variant) but hold 425 of the 666 trials
that name a representative, guardian or surrogate (63.8%). Its main limit: those are mentions,
not permissions. In the 2026-10-16 reading (results/consent-phrase/consent-read.json), 30 of 50
exact-line mentions were adult permissions (60%); the rest were paths for minors only, unclear,
not a consent route at all (for example the drug "octreotide LAR"), or for physical incapacity
only.

This test reads a seeded sample of mentions from each sponsor group, blind to the group, and asks
whether template owners' mentions are real adult permissions more often than other trials'. If
so, mention counts understate how much of the real adult path comes from two templates.

## Why it is new
Prior work counts consent-capacity exclusions in trial samples (McDonald et al. 2022; DeCormier
Plosky et al. 2022; Camanni et al. 2023) or reviews IRB policies on adults with impaired
decision-making capacity (Nguyen et al. 2025, PMC12227281: 74.5% of IRB policies give guidance on
legally authorized representatives). Searches on 2026-10-30 found no count of how often registry
mentions of a representative are real adult permissions, and none by sponsor.

## Data
- results/consent-sponsor/consent-sponsor-trials.csv at commit
  dfa820661d6c06ec4eddee5e0ce1513c069a4dc6 (5,436 trials, unchanged).
- Groups, as in results/consent-sponsor (mutually exclusive here): **nci** = NCI-linked and not
  WashU-led (260 trials naming a path); **washu** = WashU-led and not NCI-linked (147); **neither**
  (241). The 18 trials that are both are not sampled.
- Sample: Python random.Random(20261030), drawing 40 nci, then 20 washu, then 40 neither, each from
  its sorted NCT ids, without replacement. 100 trials.
- Each sampled trial's current eligibility text, title and ages, fetched once from the
  ClinicalTrials.gov API v2 (fields NCTId, BriefTitle, EligibilityCriteria, MinimumAge,
  MaximumAge, StdAge) in one request.
- Before writing this, the only contact was one API call for NCT01273766 (a trial of the table
  that names no path, so it cannot be sampled) to check the field names. No trial naming a path
  was looked at for this test.

## Blind reading
The script writes reading.txt: records R001-R100 in an order fixed by a hash of the seed and the
NCT id, each with the title, ages, the path terms still found, and every line naming a path or
consent with one line either side (tagged inclusion or exclusion section; at most 4,000
characters). No NCT id or sponsor is shown. The key (blind id, NCT id, group) is a separate file,
key.csv. The reader (AI agents working for MV2) labels all 100 records before key.csv is opened,
and the labels are committed to this repository before the grading run. Limit: template wording
itself (for example NCI's sentence) can reveal the group, so the reading is blind to the sponsor
fields, not to the text.

## Labels (the 2026-10-16 categories, plus path_gone)
- **adult_permission**: someone else (a representative, guardian, surrogate or family member) may
  consent for an adult participant. In an adult-only trial any such route counts; in a trial open
  to minors the wording must plainly cover adults.
- **physical_only**: a representative may sign only for someone physically, not mentally, unable
  to.
- **minor_only**: the route is named only for minors, in a trial open to minors.
- **unclear**: the trial admits minors and the wording does not say whether the route covers
  adults, or the text cannot be read either way.
- **not_a_permission**: the match is not a consent route: a drug name, a prohibition, an exclusion
  of people who have a representative, participants who are themselves caregivers, or a person
  needed for something other than consent.
- **path_gone**: today's text no longer names a representative, guardian or surrogate. Left out
  of every share.

## Gates (if one fails, nothing is graded)
- S1 the table has 5,436 rows with its published columns; S2 it reproduces the published path
  counts (NCI-linked 278 of 1,570; WashU-led 165 of 224; Neither 241 of 3,666; both 18 of 24).
- S3 the API returns at least 98 of the 100 sampled trials; S4 at least 95 still name a path.
- L1-L3 every blind id is labelled exactly once with one of the six labels.

## Predictions
Shares are adult_permission among records read (path_gone left out), with Wilson 95% intervals.
- **R1 (main)** The nci share is at least 15 percentage points above the neither share, and the
  lower end of the Newcombe hybrid 95% interval for the difference is above 0.
- **R2** The nci share is at least 70%.
- **R3** The neither share is at most 60% (the 2026-10-16 overall rate).
- **R4** (a check: the WashU clause, "or that of legally authorized representative, if
  applicable", reads as a permission) The washu share is at least 80%.
- **R5** Estimated real adult permissions (278 NCI-linked mentions at the nci share, 147 WashU-only
  mentions at the washu share, 241 Neither mentions at the neither share): the template owners
  hold at least 70% of them (against 63.8% of mentions).

## Also reported, not graded
Every group's label counts; the estimated share of all 5,436 trials, and of the 3,666 Neither
trials, that write a real adult path.

## Code
consent_permission.py 0.1.0 and test_consent_permission.py. The sample step runs once in a sealed
container and prints both files' sha256; grading runs the same script's grade step. Thresholds,
seed and sample sizes are constants pinned by a test.

## Limits
One AI reader, not yet checked by a person. 100 records, so intervals are wide. Today's registry
text, not the 2026-10-16 text the table was built from. Sponsor fields as listed on 2026-10-30.
Only trials found by the two search phrases. The reader can sometimes infer the group from
template wording.
