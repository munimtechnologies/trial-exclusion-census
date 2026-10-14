# Writing eligibility criteria that do not shut out disabled people

A working guide for study teams, sponsors and IRB reviewers. Draft 0.2, October 2026.

By MV2 of Munim, Inc. Drafted with AI agents and checked against the sources listed at the end. **This draft has not yet been reviewed by people with lived experience of disability.** That review is the next step, and the guide will change because of it. Comments are welcome as issues at https://github.com/munimtechnologies/trial-exclusion-census or by email to munimversion2@gmail.com.

Text licensed CC BY 4.0. The checker it refers to is Apache-2.0. This is information, not medical, legal or IRB advice.

## Why this matters

People with disabilities are often left out of clinical research. Sometimes it is written into the criteria, and sometimes it happens through inaccessible procedures or assumptions about who can consent. Studies that coded trial criteria by hand keep finding the same thing:

- Of 97 ClinicalTrials.gov protocols in four common conditions, 42% excluded people for cognitive or intellectual disability, 34% for visual, 10% for hearing, 9% for mobility and 3% for communication disability. Only 18% allowed any accommodation, and 85% let investigators exclude anyone at their discretion. A documented justification was given for only 24% of the exclusions (DeCormier Plosky et al., Health Affairs 2022).
- 74.6% of NIH-funded Phase 2-4 trials of working-age US adults had criteria that could exclude adults with intellectual disability: about a third directly and 64.5% indirectly, through reading and writing requirements, functional capacity or staff discretion (McDonald, Schwartz and Sabatello, Disability and Health Journal 2022).
- In 2,710 trials from 2010-2020, 35.3% excluded disabled people explicitly and 44.5% implicitly ("Being disabled" as an exclusion criterion, scoping review, 2023, PMC10626873).
- People notice. In a survey of adults with disabilities and caregivers reached through the Cerebral Palsy Foundation's network, 22.6% of adults and 30.2% of caregivers said they or their child had been excluded from a study because of disability. They still rated inclusion as highly important (PMC13025233).

The National Council on Disability (2024) found that eligibility criteria often exclude disabled people without scientific justification. It recommended guidance that bases exclusions on science, reduces investigator subjectivity and writes permissible accommodations into the criteria themselves. This guide is a practical way to do that for one protocol at a time.

When an exclusion is not needed, results apply less well to the people who will actually use the treatment, and disabled people lose access to the benefits of taking part.

## How to use this guide

1. Paste your draft criteria into the checker (see "The checker" below). It flags items that touch disability and offers an alternative to consider.
2. For each flagged item, go to its section and answer the **three questions**:
   - **Safety:** would taking part put this person at real, specific extra risk that an accommodation cannot remove?
   - **Science:** does the outcome measure itself depend on this function (for example, a walking test, or a visual acuity endpoint)?
   - **Procedure:** or is the barrier only how the study is run (the forms, the site, the format of a questionnaire), which an accommodation can fix?
3. If the answer is "procedure", remove the exclusion and write the accommodation into the protocol. If it is "safety" or "science", keep a **narrow** exclusion: name the measure and the cut-off, and write the reason in the protocol.
4. Replace open-ended discretion ("any condition that, in the investigator's opinion...") with the specific safety reasons you have in mind.
5. Budget for the accommodations (see the plan template at the end).

An exclusion that is justified for one study can be unjustified in the next. A cataract trial must screen vision, but a diabetes trial need not. The checker marks items in the same category as the trial's own condition so reviewers can tell these apart.

---

## 1. Cognitive and intellectual disability

**Often seen:** "dementia", "cognitive impairment", "intellectual disability", "MMSE < 24", "developmental delay", "learning disability".

**Ask:** Is cognition part of what you measure? Does the intervention need the participant to manage something complex alone (dosing, a device, a diary)? Or is the real worry consent and paperwork?

**If an exclusion is needed, narrow it:**
- Name the instrument, the cut-off and the reason: "MoCA below 18, because the primary outcome is a self-administered diary that the study cannot adapt" is reviewable. "Cognitive impairment" is not.
- Do not use a cognitive screen as a stand-in for capacity to consent. These are different questions (see section 2).
- Check whether the screen itself is accessible: many cognitive screens need sight, hearing or speech, so they mis-score people with sensory or communication disabilities.

**Instead of excluding, consider:**
- Easy-read and plain-language information sheets and consent forms, tested with readers who have intellectual disability.
- Supported decision-making: the participant chooses a trusted supporter who helps them understand and decide. The participant still makes the decision.
- Teach-back: ask the person to explain the study in their own words, and re-explain until they can.
- A study partner or caregiver who helps with diaries, reminders and visits, if the participant agrees.
- Fewer, shorter visits; reminders by text or phone; pictorial schedules.

**Protocol wording to adapt:** "People with intellectual or cognitive disability are eligible. Study information is provided in easy-read format, and participants may choose a supporter to help them decide and take part. Capacity to consent is assessed as described in section [X]."

## 2. Capacity to consent

**Often seen:** "unable to provide informed consent", "lacks decision-making capacity", "legally incompetent", "unable to understand the study".

**Ask:** Can the study be done with people who cannot consent alone, and does it offer them a prospect of benefit or answer a question about their own condition? Many dementia, critical care, stroke and intellectual disability studies must include them for the results to mean anything.

**If an exclusion is needed, narrow it:** "Unable to give informed consent **after** accessible information, supported decision-making and adequate time, **and** no legally authorized representative is available" excludes far fewer people than "unable to consent".

**Instead of excluding, consider:**
- A formal capacity assessment for this specific decision, done after the information has been made accessible. Capacity is decision-specific and can change over time.
- Consent by a legally authorized representative (LAR) **plus** the participant's own assent, where the IRB approves it under the applicable rules (45 CFR 46; 21 CFR 50 for FDA-regulated studies; state law decides who can be an LAR).
- Respect dissent: if a participant objects or shows distress, stop, whatever the LAR has agreed.
- Re-consent if capacity returns, or check capacity again during long studies.

**Protocol wording to adapt:** "Adults who cannot consent for themselves may take part with consent from a legally authorized representative and their own assent, as approved by the IRB. A participant's dissent is always respected."

## 3. Vision

**Often seen:** "blind", "visual impairment", "low vision", "visual acuity worse than 20/40".

**Ask:** Does the outcome need sight (a visual task, an eye endpoint)? Is there an eye-safety reason (for example, a drug with known retinal toxicity)? If not, the barrier is almost always the format of the forms, screens and questionnaires.

**If an exclusion is needed, narrow it:** name the measure, the eye and the threshold, and the reason (for example, "best-corrected acuity worse than 20/200 in the study eye, because the endpoint is change in acuity").

**Instead of excluding, consider:**
- Consent forms and questionnaires that work with screen readers (tagged PDF or accessible HTML or Word, read in order, with real headings and labelled form fields), large print and braille on request.
- Reading documents aloud, with a witness where the rules require one.
- Electronic diaries and eConsent platforms that meet WCAG 2.1 AA. Test them with a screen reader before launch.
- Tactile or audible labels on study medication and devices; a guide at unfamiliar sites; travel support.

**Protocol wording to adapt:** "Blind and low-vision participants are eligible. Study documents are available in large print, braille and screen-reader-accessible formats, and staff will read documents aloud on request."

## 4. Hearing

**Often seen:** "deaf", "hearing impairment", "uses hearing aids", "unable to hear instructions".

**Ask:** Does the outcome need hearing (an audiology endpoint, an auditory task)? Does the intervention affect hearing (an ototoxic drug), so that a baseline is needed? Otherwise, the barrier is communication access.

**If an exclusion is needed, narrow it:** state the audiometric threshold and why, for example "baseline hearing loss above 40 dB HL, because the primary outcome is change in hearing threshold". If ototoxicity is the concern, consider monitoring rather than exclusion.

**Instead of excluding, consider:**
- Qualified sign language interpreters (ASL in the US) for consent and visits. Deaf interpreters where needed. Never use family members as the default interpreter.
- Captioned consent videos and study videos; written or typed instructions; text or relay services instead of phone-only contact.
- Hearing loops or assistive listening devices at sites. Let people keep their hearing aids or cochlear implants on unless there is a specific reason.
- Translated and back-translated sign language versions of key questionnaires where they exist.

**Protocol wording to adapt:** "Deaf and hard-of-hearing participants are eligible. The study provides qualified sign language interpreters, captioned media and text-based contact at no cost to the participant."

## 5. Communication and speech

**Often seen:** "aphasia", "dysarthria", "non-verbal", "unable to communicate", "unable to read or write", "illiterate".

Note that "unable to read English" is a **language** requirement, not a disability. Handle it in section 9.

**Ask:** Does the outcome depend on speech or language (a speech therapy trial, a verbal test)? If not, ask how else the person could give the same answer.

**If an exclusion is needed, narrow it:** name the task and why it cannot be adapted, for example "unable to complete the verbal fluency test, because it is the primary outcome".

**Instead of excluding, consider:**
- Accept answers given through AAC (communication boards, speech-generating devices, eye gaze), writing, typing, pointing or yes/no signals.
- Allow a familiar communication partner to be present, and give extra time for visits and interviews.
- Aphasia-friendly consent materials: short sentences, one idea per line, key words in bold, supporting pictures.
- Read documents aloud for people who cannot read print. Reading ability is not the same as understanding.

**Protocol wording to adapt:** "Participants may communicate by speech, writing, typing, pointing or an AAC device, and may bring a communication partner. Extra time is allowed for all study visits."

## 6. Mobility and physical disability

**Often seen:** "wheelchair", "non-ambulatory", "unable to walk", "bedridden", "uses a walker or cane", "paraplegia", "amputation".

**Ask:** Is walking or standing the outcome (a 6-minute walk test, a balance test)? Is there a safety reason tied to the intervention (for example, a fall risk with a sedating drug, or a procedure that needs a particular position)? Otherwise, the barrier is the site and the travel.

**If an exclusion is needed, narrow it:** name the test and the reason. Consider an alternative outcome that wheelchair users can complete (for example, a seated or upper-limb measure).

**Instead of excluding, consider:**
- Accessible sites: step-free entrance, accessible toilets, height-adjustable exam tables, accessible scales (wheelchair or seated scales) and imaging that allows transfer help.
- Home visits, remote visits, local labs and mailed study drugs where the design allows.
- Paid transport, accessible parking, and visit times that fit personal care schedules.
- Trained staff and equipment for safe transfers.

**Protocol wording to adapt:** "Wheelchair users and people with limited mobility are eligible. Study sites are accessible, and home or remote visits and transport are offered where the protocol allows."

## 7. Psychiatric and mental health conditions

**Often seen:** "any psychiatric disorder", "history of depression", "schizophrenia", "bipolar disorder", "suicidal ideation".

**Ask:** Is there a specific interaction or risk (for example, a drug with a known psychiatric effect, or active suicidality during a high-burden study)? "History of any psychiatric illness" is rarely needed.

**Instead of a blanket exclusion:** exclude current, specific, unstable states with a named measure (for example, "current suicidal ideation with intent, C-SSRS"), and allow people whose condition is stable on treatment. Plan monitoring and a referral pathway rather than excluding everyone with a diagnosis.

## 8. Investigator discretion

**Often seen:** "any condition that, in the opinion of the investigator, would make participation unsafe or interfere with the study".

**The problem:** these clauses were in 85% of the protocols DeCormier Plosky et al. read. They give no reason that can be reviewed, and they can turn into a quiet exclusion of disabled people.

**Instead:** list the specific safety concerns you have in mind. If you keep a discretion clause, require the reason to be recorded for every person excluded under it, and review those reasons for patterns (for example, every month, by the PI and a team member who did not make the decision).

## 9. Language and literacy

**Often seen:** "must read and speak English", "unable to read".

Language rules are not disability rules, but they often exclude deaf people who use sign language, and people who cannot read print. Offer translated materials, interpreters and read-aloud consent. Treat ASL and other sign languages as languages.

## 10. Performance status (cancer trials)

**Often seen:** "ECOG performance status 0-1", "Karnofsky 70 or more".

These scales score how much a person does unaided, including walking, so a wheelchair user who is otherwise well can score as "limited". ASCO and Friends of Cancer Research recommend including ECOG 2 unless there is a specific reason not to. Write a note for assessors: score the person's disease-related function, not a long-standing disability.

---

## Other resources, and how this guide differs

- **The MRCT Center's Accessibility by Design in Clinical Research Toolkit** (v1.2, 2023) is the most complete resource on the whole study lifecycle. Its Tool A.2.i sets problematic eligibility wording beside preferred wording, for sponsors, IRBs and people with disabilities. Use it alongside this guide. It is licensed CC BY-NC-SA 4.0, so this CC BY guide does not reproduce any of its text. Everything here was written separately.
- **The National Council on Disability's report** *The Implicit and Explicit Exclusion of People with Disabilities in Clinical Trials* (2024) sets out the policy case and the federal recommendations.

What this guide adds is narrow. It is organised by the kind of exclusion that a reviewer actually finds in a protocol, and each section pairs the three questions with narrowing and accommodation options. It is also tied to an open checker that finds those items automatically, using the same rules as a registry-wide count. That way a study team can see how its criteria compare with the field.

## The checker

`check` (in trial-exclusion-census, Apache-2.0) runs the same open word rules used for the registry-wide census on one study's criteria. It lists each flagged item, its category and an alternative to consider. A browser version runs inside the page at https://munimv2.github.io/inclusive-criteria/, and nothing you paste is sent anywhere.

What it is not: it reads words, not meaning. It flags what a criterion says, not whether the exclusion is justified, and it misses exclusions worded in ways it does not know. It reads only the exclusion section, so an inclusion criterion such as "able to walk 100 m unaided" is not flagged. Its precision and recall for each category are being measured by hand on random samples, and the results will be published with the census.

## Accessibility plan: a one-page template for the protocol

1. **Who might be excluded:** list each criterion that touches disability and its justification (safety, science or none).
2. **Accommodations offered:** formats of documents (large print, braille, screen-reader accessible, easy-read, captioned video, sign language), communication support (interpreters, AAC, communication partner), physical access (site, equipment, home or remote visits, transport), and time (longer visits, breaks, flexible scheduling).
3. **How people ask for them:** a named contact. Ask every participant about access needs at screening. Do not wait for them to disclose a disability.
4. **Consent:** accessible formats, supported decision-making, capacity assessment, LAR and assent rules, respecting dissent.
5. **Budget:** a line for accommodations (interpreters, format conversion, transport, home visits). The 2026 BMJ Open scoping review names a dedicated accommodations budget as a core recommendation.
6. **Digital tools:** eConsent, ePRO and apps tested against WCAG 2.1 AA and with assistive technology before launch.
7. **Data:** record disability status with a standard tool (for example, the Washington Group Short Set), so that inclusion can be reported.
8. **Reporting:** report how many people were excluded under each disability-related criterion and how many accommodations were given.

## Sources

- DeCormier Plosky W, et al. Excluding people with disabilities from clinical research: eligibility criteria lack clarity and justification. Health Affairs. 2022;41(10). doi:10.1377/hlthaff.2022.00520
- McDonald KE, Schwartz AE, Sabatello M. Eligibility criteria in NIH-funded clinical trials: can adults with intellectual disability get in? Disability and Health Journal. 2022;15(4):101368. doi:10.1016/j.dhjo.2022.101368
- "Being disabled" as an exclusion criterion for clinical trials: a scoping review. 2023. https://pmc.ncbi.nlm.nih.gov/articles/PMC10626873/
- Disability community perspectives on participation in research and studying positive health. https://pmc.ncbi.nlm.nih.gov/articles/PMC13025233/ (survey run with a disability advisory board recruited through the Cerebral Palsy Foundation)
- Equitable inclusion of people with disabilities in clinical trials: a scoping review. BMJ Open, 2026. doi:10.1136/bmjopen-2025-108550, https://pmc.ncbi.nlm.nih.gov/articles/PMC12878309/ (69 guidance documents, 2019-2025: universal design, multi-format materials, supported decision-making, accommodations budgets, disabled IRB members.)
- MRCT Center of Brigham and Women's Hospital and Harvard. Accessibility by Design in Clinical Research Toolkit, v1.2. 2023. CC BY-NC-SA 4.0. https://mrctcenter.org/wp-content/uploads/2023/12/12-11-2023-AbD-Toolkit.pdf
- National Council on Disability. The Implicit and Explicit Exclusion of People with Disabilities in Clinical Trials. August 2024. https://www.ncd.gov/report/the-implicit-and-explicit-exclusion-of-people-with-disabilities-in-clinical-trials/
- US FDA. Enhancing the Diversity of Clinical Trial Populations: Eligibility Criteria, Enrollment Practices, and Trial Designs. Guidance for Industry, November 2020.
- ASCO and Friends of Cancer Research. Modernizing clinical trial eligibility criteria (recommendations, 2017 and 2021, including performance status).
- US HHS. Protection of Human Subjects, 45 CFR 46 (including 46.102 on legally authorized representatives and 46.111(b) on additional safeguards); FDA, 21 CFR 50.
- Washington Group on Disability Statistics. Short Set on Functioning.
- NIH challenge: Advancing the Inclusion of People with Disabilities in Clinical Research (2026), which names restrictive eligibility, inaccessible procedures and assumptions about consent capacity as the barriers to address.

## Changes

- 0.2 (2026-10-14): added the MRCT Center toolkit, the National Council on Disability report and a recent community survey, and said plainly what the checker does not read (inclusion criteria). No change to the advice.
- 0.1 (2026-10-14): first draft.
