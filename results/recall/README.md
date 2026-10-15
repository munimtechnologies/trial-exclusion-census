# Blind recall labels (CC BY 4.0)

These are hand labels for the 225 trials of the blind recall sample in
[../v0.1.1/recall/](../v0.1.1/recall/). It holds 150 random trials and 75 "broad" trials, drawn by
`recall_sample.py` (seed 2026) from the 2026-10-14 registry. Each trial was labelled from its full
eligibility text in `blind.md`, without looking at `flags.csv`.

For each core category, a label is `x` if the exclusion criteria shut people out for that kind of
disability, `i` if the inclusion criteria require an ability that does, `xi` for both, or blank.
The `notes` column gives the wording the label rests on.

## Two halves, in this order

1. **labels-dev.csv (R001-R114)** was labelled first. The misses it showed (coordinated lists such
   as "cognitive, visual or motor impairment", wordings such as "learning difficulties",
   "decisionally impaired", "under guardianship or curatorship", "cochlear implant", "motor
   deficit" and "spasticity", "unable to read, not English speaking", "20/20 vision", "no visual
   or auditory impairments", "able to converse", GMFCS I-III) became the v0.4.0 rules. Scores of
   v0.4.0 on this half are optimistic.
2. **labels-heldout.csv (R115-R225)** was labelled after the v0.4.0 rules were written and fixed in
   the run's work folder. It is the fair test of v0.4.0. Both halves fairly test v0.1.1 and v0.3.0.

Both halves and the rules were published in the same commit, so git history does not prove the
order. The order is stated here, and by the labeller.

## Conventions

- "Unable or unwilling to consent" counts as a consent exclusion. A refusal alone does not.
- "Able to understand / capable of understanding and signing consent" counts as an `i` for consent
  when the item names no representative, guardian or parent. A plain "signed informed consent"
  does not count.
- Language requirements ("English-speaking", "read and write Spanish") are not disability labels.
- In eye trials, eye findings that only matter to the eye exam are not counted, but amblyopia,
  blindness in the fellow eye and visual acuity limits are.
- Cochlear implants excluded for MRI or brain-stimulation safety count as hearing, because they
  shut out people who are deaf.
- Adults under guardianship, curatorship or safeguard of justice count as consent capacity.

## Limits

The labeller was an AI agent working for MV2 of Munim, Inc., one reader per trial, and the
categories involve judgment (for example, "able to understand simple verbal commands" was labelled
cognitive). A second, independent labeller would let agreement be measured. Disagreements are
welcome as issues.
