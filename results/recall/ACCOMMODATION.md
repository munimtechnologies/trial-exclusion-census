# How good is the accommodation flag?

trial-exclusion-census notes, for each trial, whether its criteria offer an accommodation (a
legally authorized representative, an interpreter, an assistive device allowed, large print and
the like). Up to 0.4.0 the flag was a word list matched anywhere in the criteria. The v0.1.1 run
reported that **7.0%** of trials with a disability exclusion "mention any accommodation", and that
NIH-led trials do so most often (14.9%).

This file checks that flag on the blind recall sample: 225 trials drawn at random from the
2026-10-14 registry without looking at any flag ([README.md](README.md)). Read on 2026-10-15 by an
AI agent working for MV2 of Munim, Inc., one reader, reading each trial's full criteria. No person
has checked this reading yet.

## Result

The 0.4.0 word list matches 16 of the 225 trials. **5 of the 16 offer an accommodation** to
disabled adults: precision **31%** (Wilson 95% interval 14% to 56%).

| Label | NCT | Matched words, in context | Offers an accommodation? |
|---|---|---|---|
| R001 | NCT05977036 | "written informed consent document (or that of legally authorized representative, if applicable)" | yes |
| R005 | NCT07844356 | "drugs affecting pupil size or accommodation" (the eye's focusing) | no |
| R016 | NCT01654133 | "Access for device delivery to accommodate 22F or 24F sheath" | no |
| R023 | NCT07592780 | "Subject's parent and/ or guardian must be able to understand and provide informed consent" (ages 2-17) | no: consent for a child |
| R043 | NCT03090802 | "Parent/guardian is willing and available to consent" (ages 14-19) | no: consent for a minor |
| R062 | NCT03282656 | "Parental/guardian/patient signed informed consent" (ages 3-40) | no: consent for a minor |
| R103 | NCT07188090 | "for cognitively or decisionally impaired individuals ..., the availability of a family member or guardian to give consent and assist in the consent process" | yes |
| R106 | NCT00692575 | "Sufficient English to permit communication without an interpreter" | no: the opposite |
| R114 | NCT07846787 | "the subject and his/her legal guardian sign the informed consent form" (ages 6-9) | no: consent for a child |
| R119 | NCT07650994 | "Informed consent form signed by the subject or legally acceptable representative" | yes |
| R145 | NCT02509481 | "parent or guardian consent if study participant age is < 18 years" | no: consent for a minor |
| R178 | NCT00282750 | exclusion: "Patients whose consent needs to be obtained through a surrogate" | no: the opposite |
| R191 | NCT02303262 | "Patients or their legal representative must be able to read (or have read to them), understand, and sign" | yes |
| R200 | NCT02222454 | "The subject or legal guardian must have signed an informed consent form" (adults) | yes |
| R216 | NCT03600428 | "Parent(s) or legal guardian(s) must provide written, informed consent" (ages 5-11) | no: consent for a child |
| R225 | NCT07039682 | "Have obtained written parental or guardian consent" (ages 15-17) | no: consent for a minor |

The labels' own notes record three more trials whose accommodations the word list does not
match: R068 ("In patients that are unable to read, the research nurse will be available to
assist"), R144 (consent "obtained from the patient's family members") and R170 ("Score >30 on the
TICS ... or if lower than 30 has assistance to participate"). R177 is similar ("with the consent
of the patient or his/her family members"). So the word list both over-counts (11 false of 16)
and misses some real offers.

## What this means for the published figure

The 7.0% figure counted word matches, not offers. In this sample most matches are a parent's
consent for a child, which is about age and not disability, so the share of trials that **offer**
an accommodation is likely lower than reported, but this sample is too small to say by how much,
and the trials with a disability exclusion may differ from the sample as a whole. The figure has
been withdrawn from the README until 0.5.0 has been run on the whole registry and its own
precision checked on a fresh sample.

## What 0.5.0 changes

- An item counts only if it offers an accommodation. The bare words "accommodate" and
  "guardian" are gone. Kept and added: consent by a legally authorized or acceptable
  representative or a legal representative; "subject or (legal) guardian"; "family member or
  guardian"; consent by family members; "with or without an assistive device / assistance";
  interpreters, sign language, braille, large print, screen readers, reading aloud; "has
  assistance"; "available to assist"; reasonable accommodations.
- Items are dropped if they mention a parent, a child, a minor or an age under 18; say "without"
  an interpreter, assistance or a representative; or say someone is unable to use large print,
  braille or sign language. In the exclusion criteria, items that require, need, use or rely on
  the accommodation are dropped too ("requires use of sign language interpreter").
- On these 16 trials, 0.5.0 keeps exactly the 5 real offers and drops the 11 others. Across the
  225 it matches 4 more trials, each a real offer by this reading: R067 ("Patients or authorized
  guardians must have the ability to understand and sign", an adult cancer trial), R068, R170 and
  R177. It still misses R144, whose text has an HTML-escaped apostrophe (`&#39;`) between
  "consent" and "family members", and the rule stops at its ";".
  That is 9 matches in 225, all offers, against 5 of 16 before (traced by the same AI agent
  through the rules' text, then run as code on 2026-10-28: the rules flag these same 9
  trials, which `test_accommodation_flag.py` checks). **This is not a fair test**: the rules were written from these same trials. The
  fair test is the `accommodation` rows of the next run's `sample_items.csv`.

CC BY 4.0. Made by MV2 of Munim, Inc. with AI agents.
