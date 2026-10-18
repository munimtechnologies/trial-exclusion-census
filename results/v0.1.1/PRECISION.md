# Precision of the v0.1.1 word rules: a reading of sample_items.csv

These are the results of the first full run of trial-exclusion-census, using the v0.1.1 rules as
released. The rules were written and published before any registry result was seen. The data
was fetched from the ClinicalTrials.gov API v2 on 2026-10-14: 463,180 interventional studies, of
which 450,052 have an exclusion section.

`sample_items.csv` holds 60 flagged exclusion items per category. They were drawn at random
(seeded reservoir, seed 2026) from every flagged item in the registry. Each item was read and
judged on one question: **does this item exclude people who have this kind of impairment or
condition?** Whether the exclusion is justified did not count. The checker was an AI agent working
for MV2 of Munim, Inc., not a person with clinical or lived-experience expertise, and only one
checker read each item. No person has checked this reading yet. Treat these as a first estimate.

This is item-level precision, so it is not the same as trial-level precision. A trial counts as
flagged in a category when at least one of its items is flagged. Trial-level precision and recall
come from the blind recall sample (`recall/`), which has not been labelled yet.

## Results

| Category | Correct / checked | Precision |
|---|---|---|
| cognitive | 57 / 60 | 95% |
| consent_capacity | 60 / 60 | 100% |
| visual | 45 / 60 | 75% |
| hearing | 57 / 60 | 95% |
| communication | 58 / 60 | 97% (48 / 60 = 80% if literacy items are left out, see below) |
| mobility | 54 / 60 | 90% |
| psychiatric | 59 / 60 | 98% |
| substance_use | 56 / 60 | 93% |
| performance_status | 58 / 60 | 97% |
| investigator_discretion | 55 / 60 | 92% |
| english_only | 60 / 60 | 100% |
| disability_general | 56 / 60 | 93% |

## The false positives

Rows are named by NCT ID; the full item text is in `sample_items.csv`.

- **cognitive (3).** NCT06894615 is a background sentence about seizure risk, not a criterion.
  NCT02286505 is an age limit with an explanation that mentions cognitive impairment.
  NCT03998423 has "(other than Alzheimer's dementia)" inside a neurologic exclusion of a dementia trial.
- **visual (15).** All 15 are ophthalmology items about eye findings that would confound the
  trial's own eye exams. Examples are "ocular condition in the study eye that could compromise
  visual acuity", "corneal pathology that would limit evaluation of loss in visual acuity", and
  "risk of visual field or visual acuity worsening". These exclude eye pathology in the study eye.
  They do not exclude people with low vision. The items are NCT01396616, NCT01045239, NCT05093374,
  NCT05531292, NCT07260695, NCT04058535, NCT01510145, NCT07734064, NCT02611778, NCT04919499,
  NCT06502171, NCT01277302, NCT04667910, NCT01493427 and NCT02462525. Most of these trials are
  already left out of the "unrelated" columns, because their condition is an eye disease.
- **hearing (3).** NCT06085729 says irreversible toxicity such as hearing loss "may be included".
  NCT03189706 excludes grade 3 toxicity "except for hearing loss". NCT07774728 is about families
  who have already decided on hearing aids, not about hearing loss.
  - Five items count as correct but deserve a note: NCT02178696, NCT04975009, NCT06277063 and
    NCT05708586 exclude hearing-aid users through a list of implanted or metal devices (MRI or
    device safety), and NCT05186259 excludes hearing-aid wearers from a tinnitus trial.
- **communication (2).** NCT05600374 describes how consent is assessed for patients who cannot
  speak; it is not an exclusion. NCT04094337 ("Language difficulties") is most likely a language
  barrier, not a disability.
  - Ten items exclude people who cannot read or write ("illiterate", "unable to read the consent
    form"). The census counts these in communication, because they shut out many people with
    intellectual, learning and print disabilities. But reading is not a disability in itself. If
    those ten are not counted, precision is 48/60. They are NCT07108166, NCT07687394, NCT00909610,
    NCT04415411, NCT04960293, NCT07068763, NCT07433088, NCT06237218, NCT02495467 and NCT04219098.
- **mobility (6).** NCT04003480 is a planned amputation as part of treatment, and NCT03723551 is an
  amputation that the infection itself requires. NCT03856749 is a sub-heading ("Inclusion Criteria
  for caregiver of wheelchair user"). NCT06004388 is hemiplegic migraine. NCT06074250 excludes
  parents of a child with a disability. NCT06565130 says "other than a physical disability".
- **psychiatric (1).** NCT07231497 is about the family history of a first-degree relative.
- **substance_use (4).** NCT02260869 is an opioid dose limit, not substance use disorder.
  NCT03437668 says addiction treatment "will be reviewed on a case by case basis". NCT05156112
  matched the name of a treatment program. NCT02920632 is internet addiction.
- **performance_status (2).** NCT04370795 is a URL fragment. NCT05875935 is an ECoG
  (electrocorticography) recording.
- **investigator_discretion (5).** In each of these, the discretion lets people in or relaxes a
  limit rather than excluding them: NCT07379684, NCT06945081, NCT06200233, NCT05195723 and NCT04965155.
- **disability_general (4).** NCT02678845 is a disability pension case, NCT01203995 is disability
  insurance, NCT01770964 is a compensation claim, and NCT04553393 is NYHA class III/IV "cardiovascular disability".

## What changed in v0.3.0 because of this check

- Exception clauses are read out before an item is classified ("except for ...", "other than
  ...", "may be included (e.g. ...)", "will not be considered ..."). A clause ends at a full stop,
  semicolon or closing parenthesis, or after 60 characters. It is kept if a language name follows,
  as in "languages other than English".
- **Visual veto:** a visual match is dropped when the item talks about the study eye, ocular,
  retinal, macular, corneal or foveal findings, cataract, media opacity, the optic nerve,
  ophthalmology, or worsening of vision. It is kept if the item also says blind, low vision,
  visual impairment, vision problem, poor vision or unable to see.
- **Mobility veto:** a planned or required amputation is dropped unless the item also names a
  wheelchair, paralysis, being bed-bound, non-ambulatory, or a prior amputation. "Hemiplegic
  migraine" no longer counts.
- **disability_general:** disability pension, insurance, benefits, claims, compensation, payments
  and leave no longer count.

On these same 360 core items, v0.3.0 removes 22 of the 29 false positives and none of the correct
items. That figure is optimistic, because the fixes were written while looking at these items.
The v0.3.0 run therefore draws a **fresh** sample with seed 2027 for an independent check. The
v0.1.1 numbers in `results.md` stay as the pre-registered result, and v0.3.0 is reported beside
them, never instead of them.
