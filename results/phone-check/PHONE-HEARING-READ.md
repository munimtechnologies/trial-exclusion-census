# Hearing mentions in telephone and other trials outside the VA, read (S2)

Read on 2026-10-15 from the ClinicalTrials.gov API v2. CC BY 4.0.
Made by MV2 of Munim, Inc. with AI agents.

[PHONE-MATCHED-RESULT.md](PHONE-MATCHED-RESULT.md) found that telephone-delivered no-phase trials
name a hearing wording 2.45 times as often as other trials of the same condition. Those are
mentions. This is S2, the reading fixed in [PREREG-PHONE-MATCHED.md](PREREG-PHONE-MATCHED.md)
before any counting: does the hearing item itself say the telephone is the reason?

**Which trials.** The first 20, in the API's default order, of each of two queries: no-phase
interventional trials, not led by the VA, trials of cognitive, brain-injury, stroke, hearing and
eye conditions left out, whose criteria name the hearing family; one with the telephone exposure
(279 trials, the same number the exploratory non-VA count gave) and one without it (3,150
trials). The exact queries are in [phone-hearing-read.json](phone-hearing-read.json). Not a
random sample. Every quote was checked against the single record, and where an item was cut
(marked ...) the rest was read there.

**Marks (pre-registered).** *Phone-tied:* the hearing item itself names telephone, phone or calls.
*Shuts out:* an exclusion, or an inclusion requirement of hearing. *Not shutting out:* anything
else.

## Result

| | Telephone trials | Other trials |
|---|---|---|
| Hearing item is phone-tied | **4 of 20** | **1 of 20** |
| Hearing item shuts people out | 20 of 20 | 20 of 20 |
| Another item of the record names a phone (exploratory) | 12 of 20 | 5 of 20 |
| A phone is named anywhere in the criteria (exploratory) | 13 of 20 | 5 of 20 |

- **The first prediction fails by one:** at least 5 of the 20 telephone items were to be
  phone-tied, and 4 are. **The second holds:** at most 2 of the other 20 were to be, and 1 is.
- **The difference is in the predicted direction but not significant:** one-sided Fisher exact
  test p = 0.17 (4 of 20 against 1 of 20). Twenty trials a side could only show a large gap.
- So the reading **does not confirm** that the telephone is the stated reason for most hearing
  exclusions in telephone trials. Most items, in both groups, give no reason at all.
- **All 40 shut people with hearing loss out.** None offers captioned telephone, relay, text or
  an interpreter. One makes an exception when a caregiver can help ("Severe hearing impairment
  ( if lacks caregiver)", NCT02776566).

**Exploratory (not pre-registered).** In 12 of the 20 telephone trials, another item of the same
criteria names a phone: telephone access ("Must have access to a telephone", NCT03060096), owning
a smartphone, or being able to take calls ("Able to talk on the phone and use whatsapp",
NCT04992741; "able to answer calls", NCT07149311). With the phone-tied items, 13 of 20 telephone
trials name a phone somewhere in their criteria, against 5 of 20 others. In these trials a bare
hearing exclusion sits beside a requirement to use a phone, so the phone may be the reason even
when the hearing item does not say so. The registry text cannot tell, and this was chosen after
reading, so it is a lead, not a result.

**Beside the VA reading.** Under the same rule, 6 of the 20 VA hearing items in
[VA-HEARING-READ.md](../sponsor-check/VA-HEARING-READ.md) are phone-tied. That reading was not
limited to telephone trials and is not a matched comparison.

## The items

Telephone trials (`AREA[InterventionSearch]telephone`):

| # | Trial | Title (short) | Item (quoted) | Phone-tied |
|---|---|---|---|---|
| 1 | NCT05592288 | Mobile app for adults at risk of diabetes | "have no hearing or vision impairment," (inclusion) | no |
| 2 | NCT05283200 | Lifestyle interventions for epilepsy | "Significant hearing loss" | no |
| 3 | NCT06070168 | Telephone counseling for postpartum depression | "No hearing or vision problems" (inclusion) | no |
| 4 | NCT01985074 | Case management for frequent ED visitors | "Severe hearing impairment or language difficulties" | no |
| 5 | NCT05880810 | Glucose monitor for advanced care at home | "...not able to hear a smart phone alert or alarm." | yes (an alarm, not a call) |
| 6 | NCT03060096 | Stepped-care telehealth for cancer survivors | "Hearing loss that would preclude participating in telephone sessions ..." | yes |
| 7 | NCT03515889 | Ideal Protein vs low-fat diet | "...a hearing impairment that interferes with study participation." | no |
| 8 | NCT03739762 | Healthy Aging Resources to Thrive | "diagnosis codes indicating hearing loss, dementia or serious mental illness ..." | no |
| 9 | NCT01811264 | Quality of life in advanced breast cancer | "patients with an uncorrectable hearing impairment or having limited English proficiency ..." | no |
| 10 | NCT05529732 | Mobile education on anxiety | "Hearing, speech, or visual impairment" (and the same as an inclusion requirement) | no |
| 11 | NCT07149311 | Diabetes self-management education | "Mentally stable, with no vision, verbal, or hearing impairments" (inclusion) | no |
| 12 | NCT04885439 | NextSteps for advanced cancer | "patient or caregiver is deaf or has significant hearing impairment and thus cannot use the telephone" | yes |
| 13 | NCT04002336 | Smartphone app for voice therapy | "Impaired hearing"; inclusion "Hearing level within normal limits" | no |
| 14 | NCT03177447 | ENABLE: CHF-PC | "Non-correctable hearing loss" (patients and caregivers) | no |
| 15 | NCT02886234 | Health Improvement Project, Providence | "Severe hearing impairment not allowing phone delivery" | yes |
| 16 | NCT05426200 | Pre-transplant health coaching | "Non-English speaking, nonverbal, or extremely hard of hearing" | no |
| 17 | NCT03947606 | Decision partnering for cancer caregivers | "... uncorrected hearing loss, or active substance abuse" | no |
| 18 | NCT04992741 | HPV vaccination education | "People with hearing or sight impairments that may interfere with communication," (and as an inclusion requirement) | no |
| 19 | NCT02499094 | Mobile sensor data in depression | "Participants with visual or hearing impairment" | no |
| 20 | NCT02776566 | Anticoagulation self-monitoring | "Severe hearing impairment ( if lacks caregiver)" | no |

Other trials (`NOT AREA[InterventionSearch]telephone`):

| # | Trial | Title (short) | Item (quoted) | Phone-tied |
|---|---|---|---|---|
| 1 | NCT01778686 | PET radioligand imaging | "non-fluent in danish or severe visual or hearing impairment" | no |
| 2 | NCT06037369 | Short-message-based intervention | "Being unable to read text messages on mobile phone, or with impaired hearing, could not answer the phone" | yes |
| 3 | NCT07860203 | Stellate ganglion block and sleep | "Cognitive impairment, hearing impairment, language impairment, ..." | no |
| 4 | NCT05602883 | Music therapy in threatened preterm birth | "be deaf," | no |
| 5 | NCT05331261 | Exercise after knee replacement | "Not having visual and hearing impairment," (inclusion) | no |
| 6 | NCT05064683 | Facilitated tucking for newborns on CPAP | "Newborns with hearing loss" | no |
| 7 | NCT03230890 | HIRREM in military personnel | "Severe hearing impairment (because the subject will be using ear buds during HIRREM)" | no |
| 8 | NCT05344846 | Guided imagery after cesarean | "Hearing loss and deafness" | no |
| 9 | NCT06885554 | Adjustment disorders in the US military | "Deafness in one or both ears, perceived differences in hearing between ears" | no |
| 10 | NCT03297320 | Advance care planning, London | "Patients who do not speak English; hard of hearing" | no |
| 11 | NCT04292561 | EEG monitoring and delirium | "...such as language, vision and hearing impairment" | no |
| 12 | NCT03085446 | Insomnia in older adults | "... have any significant visual or hearing impairments or chronic pain ..." | no |
| 13 | NCT07499986 | Respiratory muscle training | "Presence of physical limitations (e.g., visual or hearing impairment, orthopedic problems)" | no |
| 14 | NCT06036069 | Vibration vs core exercise in Down syndrome | "Vision or hearing loss." | no |
| 15 | NCT03775356 | EEG burst suppression | "hearing difficulty"; "deafness" | no |
| 16 | NCT05489653 | Music for sleep in Parkinson's disease | "... no obvious hearing impairment ..." (inclusion) | no |
| 17 | NCT07239258 | Tele-integrated therapy after knee arthroplasty | "...hearing impairments that would prevent them from following therapy instructions ..." | no |
| 18 | NCT02004236 | tDCS in autistic children | "Acute visual or hearing loss." | no |
| 19 | NCT03351764 | Non-invasive brain stimulation | "Subjects who have hearing loss that has been clinically evaluated and diagnosed." | no |
| 20 | NCT07463638 | Mindfulness in vascular surgery | "Unable to wear or use the VR device, including because of blindness or deafness." | no |

The one phone-tied item among the other trials comes from a text-message study the telephone
search did not catch, as the pre-registration expected ("a trial delivered by telephone that
never says so is counted as other").

## What it means for the telephone finding

The count result stands: telephone trials name hearing (and visual and cognitive) wordings far
more often than other trials of the same condition. This reading adds that their registry
entries rarely give the telephone as the reason in the hearing item itself (4 of 20), though
most of them require a phone elsewhere. The fix to offer is the same either way: where a study
runs by phone, offer captioned telephone, relay services (711 in the US), text or chat, or video
with captions, before excluding people with hearing loss.

## Limits

- 20 trials a side, the first the API returned, not a random sample. One reader (AI agents
  working for MV2), no second coder.
- The rule looks at the hearing item only. A record can name a phone in another item, which the
  exploratory rows count, but registry criteria are often a summary of the protocol.
- This does not say any exclusion is unjustified for its study.

`test_phone_hearing_read.py` checks the queries against the pre-registration, the marks against
the rule, and every number here against [phone-hearing-read.json](phone-hearing-read.json).
