# Recall and precision of the 0.4.0 rules on the held-out half of the recall sample

These are the scores `recall_sample.py score` printed for the census rules 0.4.0 on the 111 trials
of the blind recall sample that were labelled after those rules were fixed (`labels-heldout.csv`;
run of 2026-10-15). Precision and recall are counted on the 78 random trials only; the 33 broad
trials, drawn to find misses quickly, appear only in the lists of misses. The labels were made by
AI agents working for MV2, one reader per trial, while reading the criteria without the rules'
flags. They have not yet been checked by a person. The output follows unchanged. Its first heading
is the fixed title that `recall_sample.py` prints; the labels it refers to are these AI-agent labels.

For comparison, on the same 78 trials the 0.3.0 rules flag 15 of the 22 trials labelled as
excluding someone (15/15 correct), and find 11 of the 19 labelled requirements (11/12 correct).

---

# Recall and precision of the word rules (hand-labelled sample)

census rules 0.4.0; labelled trials: 78 random, 33 broad.
Trial level: a trial counts once per category. Wilson 95% intervals.

| Category | Labelled excluded | Flagged | Precision | Recall |
|---|---|---|---|---|
| cognitive | 6 | 5 | 5/5 = 100% (57-100%) | 5/6 = 83% (44-97%) |
| consent_capacity | 12 | 9 | 9/9 = 100% (70-100%) | 9/12 = 75% (47-91%) |
| visual | 3 | 2 | 2/2 = 100% (34-100%) | 2/3 = 67% (21-94%) |
| hearing | 1 | 1 | 1/1 = 100% (21-100%) | 1/1 = 100% (21-100%) |
| communication | 2 | 2 | 2/2 = 100% (34-100%) | 2/2 = 100% (34-100%) |
| mobility | 2 | 0 | n/a | 0/2 = 0% (0-66%) |
| any | 22 | 16 | 16/16 = 100% (81-100%) | 16/22 = 73% (52-87%) |

Random-sample trials with a disability barrier in the inclusion criteria: 19/78 = 24% (16-35%); with one only there (invisible to an exclusion-only count): 13/78 = 17% (10-26%).

## Inclusion-criteria requirement rules against the i marks

| Category | Labelled required | Flagged | Precision | Recall |
|---|---|---|---|---|
| cognitive | 2 | 1 | 1/1 = 100% (21-100%) | 1/2 = 50% (9-91%) |
| consent_capacity | 15 | 10 | 10/10 = 100% (72-100%) | 10/15 = 67% (42-85%) |
| visual | 1 | 0 | n/a | 0/1 = 0% (0-79%) |
| hearing | 0 | 0 | n/a | n/a |
| communication | 2 | 3 | 2/3 = 67% (21-94%) | 2/2 = 100% (34-100%) |
| mobility | 3 | 0 | n/a | 0/3 = 0% (0-56%) |
| any | 19 | 14 | 13/14 = 93% (69-99%) | 13/19 = 68% (46-85%) |

## Misses (labelled excluded, not flagged)

- R118 NCT04876612 (broad) cognitive: decreased cognition to the extent that NRS is incomprehensible
- R126 NCT06082557 (random) consent_capacity: no/limited capacity for civil conduct; incapable to understand; able to understand the protocol
- R132 NCT03748381 (random) visual: amblyopia; retinitis pigmentosa (cataract trial; condition-related)
- R134 NCT00925197 (random) consent_capacity: blind patients and those unable to read; incomplete understanding of instructions; French language (language)
- R145 NCT02509481 (broad) consent_capacity: illness that impedes comprehension; permanent disability (general); consent item names guardian
- R169 NCT00525785 (broad) consent_capacity: abnormal mental status; cannot comprehend the protocol
- R177 NCT06379672 (random) mobility: disease that severely affects limb movement
- R178 NCT00282750 (random) consent_capacity: consent through a surrogate excluded
- R179 NCT02664909 (broad) visual: acquired defective color vision
- R201 NCT02839915 (random) cognitive: IQ below 40 excluded; IQ at least 40 required (autism language trial)
- R205 NCT02060461 (broad) visual: amblyopia (LASIK trial; condition-related)
- R207 NCT03106220 (random) mobility: inability to perform exercise (exercise trial)
- R217 NCT05402072 (broad) mobility: co-morbidities requiring assistance for ADLs; language of the site (language)
- R222 NCT06691698 (broad) communication: need for AAC (pictures or signs); cerebral palsy or neuromuscular disease (intellectual disability trial)
- R222 NCT06691698 (broad) mobility: need for AAC (pictures or signs); cerebral palsy or neuromuscular disease (intellectual disability trial)

## Requirement misses (labelled i, not flagged)

- R123 NCT07011264 (broad) mobility: able to independently perform activities of daily living
- R125 NCT06438510 (broad) consent_capacity: understand and sign the ICF
- R128 NCT01749904 (broad) visual: BCVA 20/100 or better (glaucoma trial); other ocular items are eye pathology
- R154 NCT01345448 (broad) cognitive: BCVA 20/800 or better (glaucoma); able to follow instructions judged on cognition
- R156 NCT02111850 (broad) consent_capacity: ability to understand and willingness to sign
- R162 NCT01324011 (broad) mobility: able to participate in moderate physical activity (lifestyle trial)
- R163 NCT00767299 (random) mobility: ambulatory and expected to remain so; able to comprehend and consent
- R164 NCT05387252 (random) consent_capacity: mentally capable; unable to read the google sheets; Mandarin/Taiwanese (language)
- R173 NCT07022756 (random) consent_capacity: cognitive impairment that would impair engagement; capable of consenting
- R176 NCT03656380 (random) consent_capacity: able to read; comprehend and sign consent form
- R180 NCT01919086 (random) mobility: able to provide consent; bone disease causing immobilization not eligible (myeloma)
- R181 NCT04435132 (random) consent_capacity: subject who understands the purpose of testing
- R187 NCT01211093 (broad) cognitive: walk short distance independently with or without aid; understand simple verbal commands (stroke trial)
- R189 NCT04523701 (broad) consent_capacity: ability to understand the trial
- R201 NCT02839915 (random) cognitive: IQ below 40 excluded; IQ at least 40 required (autism language trial)
- R213 NCT00815880 (random) consent_capacity: six-minute walk 100-350 m; understands the procedure
- R213 NCT00815880 (random) mobility: six-minute walk 100-350 m; understands the procedure
- R224 NCT00761826 (random) visual: visual acuity correctable to 20/40 in both eyes; blind in the fellow eye (LASIK)
