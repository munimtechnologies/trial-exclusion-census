"""Offline tests for trial-exclusion-census (no network). Apache-2.0."""

import json
import os
import tempfile
import unittest
import urllib.error

import exclusion_census as ec


def study(nct, stype="INTERVENTIONAL", criteria="", conditions=(), start=None, sponsor=None):
    ps = {"identificationModule": {"nctId": nct, "briefTitle": "Trial " + nct},
          "designModule": {"studyType": stype, "phases": ["PHASE2"]},
          "conditionsModule": {"conditions": list(conditions)},
          "eligibilityModule": {"eligibilityCriteria": criteria}}
    if start:
        ps["statusModule"] = {"overallStatus": "COMPLETED", "startDateStruct": {"date": start}}
    if sponsor:
        ps["sponsorCollaboratorsModule"] = {"leadSponsor": {"name": "X", "class": sponsor}}
    return {"protocolSection": ps}


class SectionTests(unittest.TestCase):
    def test_exclusion_section_after_header(self):
        text = ("Inclusion Criteria:\n\n* Age 18 or older\n* Type 2 diabetes\n\n"
                "Exclusion Criteria:\n\n* Legally blind\n* Unable to walk without assistance\n")
        sec = ec.exclusion_section(text)
        self.assertIn("Legally blind", sec)
        self.assertNotIn("diabetes", sec)

    def test_bold_header(self):
        sec = ec.exclusion_section("**Inclusion Criteria**:\n* Adults\n**Exclusion Criteria**:\n* Deafness\n")
        self.assertIn("Deafness", sec)
        self.assertNotIn("Adults", sec)

    def test_no_exclusion_section(self):
        self.assertIsNone(ec.exclusion_section("Adults with asthma."))
        self.assertIsNone(ec.exclusion_section(""))

    def test_inline_exclusion(self):
        a = ec.analyze({"criteria": "Patients must be adults. Exclusion criteria: pregnancy; deafness."})
        self.assertTrue(a["has_exclusion"])
        self.assertIn("hearing", a["hits"])

    def test_split_items_strips_bullets(self):
        self.assertEqual(ec.split_items("\n* one item\n2. second item\n\n"), ["one item", "second item"])

    def test_inclusion_section(self):
        text = ("Inclusion Criteria:\n\n* Age 18 or older\n* Type 2 diabetes\n\n"
                "Exclusion Criteria:\n\n* Legally blind\n")
        sec = ec.inclusion_section(text)
        self.assertIn("diabetes", sec)
        self.assertNotIn("blind", sec)
        self.assertIsNone(ec.inclusion_section("Adults with asthma."))
        self.assertIsNone(ec.inclusion_section(""))

    def test_inclusion_section_stops_at_inline_exclusion(self):
        sec = ec.inclusion_section("Inclusion criteria: adults able to walk. Exclusion criteria: unable to read.")
        self.assertIn("able to walk", sec)
        self.assertNotIn("read", sec)


class ClassifyTests(unittest.TestCase):
    def test_categories(self):
        cases = {
            "Legally blind": {"visual"},
            "Unable to speak English": {"english_only"},
            "Aphasia severe enough to prevent participation": {"communication"},
            "Unable or unwilling to provide informed consent": {"consent_capacity"},
            "MMSE score below 24": {"cognitive"},
            "Wheelchair-bound": {"mobility"},
            "Any condition that, in the opinion of the investigator, would interfere with the study":
                {"investigator_discretion"},
            "ECOG performance status of 3 or more": {"performance_status"},
            "Significant hearing loss": {"hearing"},
            "Lack of decision-making capacity": {"consent_capacity"},
            "Inability to understand the study procedures": {"consent_capacity"},
        }
        for item, want in cases.items():
            with self.subTest(item=item):
                self.assertEqual(ec.classify(item), want)

    def test_not_flagged(self):
        self.assertNotIn("visual", ec.classify("Participation in another double-blind study"))
        self.assertNotIn("mobility", ec.classify("Paralytic ileus"))
        self.assertNotIn("disability_general", ec.classify("Expanded Disability Status Scale score above 6"))
        self.assertNotIn("investigator_discretion", ec.classify("Opinion of the pilot study team"))

    def test_curly_apostrophe(self):
        self.assertIn("investigator_discretion", ec.classify("Excluded at the investigator’s judgement"))


class ExceptionAndVetoTests(unittest.TestCase):
    """0.3.0: the false positives found by hand in the first full run's sample_items.csv."""

    def test_exception_clauses(self):
        cases = {
            "Toxicity grade 3 or more except for hearing loss, alopecia and nausea": set(),
            "Irreversible toxicity may be included (e.g., hearing loss, peripheral neuropathy).": set(),
            "Having a neurological or cognitive disorder other than a physical disability.": {"cognitive"},
            "Significant neurologic disease (other than Alzheimer's dementia)": set(),
            "Vascular dementia or any dementia other than Alzheimer's disease": {"cognitive"},
            # An exception clause ends at its closing parenthesis.
            "Neurologic disease (other than Parkinson's disease) or dementia": {"cognitive"},
        }
        for item, want in cases.items():
            with self.subTest(item=item):
                self.assertEqual(ec.classify(item) & set(ec.CORE), want)

    def test_language_after_other_than_kept(self):
        self.assertEqual(ec.classify("Unable to speak languages other than English"), {"english_only"})

    def test_visual_veto(self):
        for item in ("Ocular condition in the study eye that could compromise visual acuity",
                     "Corneal pathology that would limit evaluation of loss in visual acuity",
                     "Retinal pathology contributing to visual loss",
                     "Risk of visual field or visual acuity worsening as a consequence of participation"):
            with self.subTest(item=item):
                self.assertNotIn("visual", ec.classify(item))
        for item in ("Corrected visual acuity worse than 20/40",
                     "Permanent legal blindness in the fellow (non-study) eye",
                     "Visual impairment due to retinal disease",
                     "Less than 0.1 (20/200) visual acuity in the non-test eye"):
            with self.subTest(item=item):
                self.assertIn("visual", ec.classify(item))

    def test_mobility_veto(self):
        self.assertNotIn("mobility", ec.classify("Planned above-ankle amputation within 4 weeks"))
        self.assertNotIn("mobility", ec.classify("Gangrene requiring complete lower extremity amputation"))
        self.assertNotIn("mobility", ec.classify("History of basilar or hemiplegic migraine"))
        self.assertIn("mobility", ec.classify("Lower extremity amputation"))
        self.assertIn("mobility", ec.classify("Hemiplegia"))
        self.assertIn("mobility", ec.classify("Prior amputation; planned amputation of the other limb"))

    def test_disability_benefits_not_flagged(self):
        self.assertNotIn("disability_general", ec.classify("Patients with a pending disability pension case"))
        self.assertNotIn("disability_general", ec.classify("Receiving disability insurance."))
        self.assertIn("disability_general", ec.classify("Physical disability"))

    def test_check_text_applies_exceptions(self):
        out = ec.check_text("Exclusion Criteria:\n* Grade 3 toxicity except for hearing loss\n* Deafness")
        self.assertIn("- Deafness", out)
        self.assertNotIn("- Grade 3 toxicity", out)


class RecallRuleTests(unittest.TestCase):
    """0.4.0: wordings missed in the first 114 hand-labelled trials of the blind recall sample."""

    def test_coordinated_lists(self):
        cases = {
            "Cognitive, visual or motor impairment": {"cognitive", "visual", "mobility"},
            "Cognitive or visual impairment": {"cognitive", "visual"},
            "Visual or auditory impairment": {"visual", "hearing"},
            "Unable to hear, read, visualize or comprehend the assessment":
                {"hearing", "communication", "visual", "consent_capacity"},
        }
        for item, want in cases.items():
            with self.subTest(item=item):
                self.assertEqual(ec.classify(item) & set(ec.CORE), want)

    def test_new_wordings(self):
        cases = {
            "Learning difficulties such as dyslexia": "cognitive",
            "Dementing illness": "cognitive",
            "Limited cognitive ability": "cognitive",
            "Decisionally impaired individuals": "consent_capacity",
            "Adult under guardianship or curatorship": "consent_capacity",
            "Condition that limits ability to consent": "consent_capacity",
            "Cochlear implant": "hearing",
            "Motor deficit due to another neurological disorder": "mobility",
            "Severe upper extremity spasticity": "mobility",
            "Limb conditions affecting ambulation": "mobility",
        }
        for item, cat in cases.items():
            with self.subTest(item=item):
                self.assertEqual(ec.classify(item) & set(ec.CORE), {cat})

    def test_literacy_next_to_language(self):
        self.assertIn("communication", ec.classify("Unable to read, not English speaking"))
        self.assertEqual(ec.classify("Unable to read English"), {"english_only"})

    def test_still_not_flagged(self):
        self.assertNotIn("visual", ec.classify("Visual analogue scale score below 4"))
        self.assertNotIn("mobility", ec.classify("History of physical or sexual abuse"))

    def test_new_requirements(self):
        cases = {
            "20/20 vision or correctable to 20/20": {"visual"},
            "No visual or auditory impairments": {"visual", "hearing"},
            "Able to converse with study staff": {"communication"},
            "Able to verbally consent": {"communication"},
            "No communication problem": {"communication"},
            "GMFCS level I-III": {"mobility"},
            "GMFCS level I-V": set(),
            "Able to perform the 6-minute walk test": {"mobility"},
            "Adequate cognitive cooperation": {"cognitive"},
            "BCVA 20/320 or better in the study eye": {"visual"},
        }
        for item, want in cases.items():
            with self.subTest(item=item):
                self.assertEqual(ec.requirements(item), want)


class FormatRuleTests(unittest.TestCase):
    """0.5.0: exclusion items found by reading every registry trial that names sign language,
    large print or braille in its eligibility criteria (wordings quoted from those trials)."""

    def test_sign_language_users_excluded(self):
        for item in ("Requires use of sign language interpreter",
                     "Primary use of American Sign Language (ASL)",
                     "Adults who use sign language as a primary means of communication",
                     "Significant sensory impairment (e.g., needing a British Sign Language interpreter).",
                     "Psychotherapy using American Sign Language is not possible within the scope of this study"):
            with self.subTest(item=item):
                self.assertEqual(ec.classify(item) & set(ec.CORE), {"hearing"})

    def test_sign_language_offered_not_flagged(self):
        for item in ("Non-English speakers (Spanish and sign language interpreters are available)",
                     "Failure to understand instructions given either orally or in sign language"):
            with self.subTest(item=item):
                self.assertNotIn("hearing", ec.classify(item))

    def test_large_print_and_braille(self):
        for item in ("Severe visual impairment, defined as being unable to read large-print materials",
                     "Self-reported inability to read large print books",
                     "Materials would need translation into Braille"):
            with self.subTest(item=item):
                self.assertIn("visual", ec.classify(item))


class AccommodationTests(unittest.TestCase):
    """0.5.0: an item that offers an accommodation, not just an accommodation word.
    The wordings come from the 16 recall-sample trials the 0.4.0 word list flagged."""

    def test_offered(self):
        for crit in (
                "Inclusion Criteria:\n* Informed consent signed by the subject or legally acceptable representative\n"
                "Exclusion Criteria:\n* Pregnancy",
                "Inclusion Criteria:\n* The subject or legal guardian must have signed an informed consent form\n"
                "Exclusion Criteria:\n* Pregnancy",
                "Inclusion Criteria:\n* Able to walk 10 m with or without an assistive device\nExclusion Criteria:\n* Pregnancy",
                "Inclusion Criteria:\n* Able to walk 10 m with or without assistance\nExclusion Criteria:\n* Pregnancy",
                "Inclusion Criteria:\n* Willing to fill out questionnaires. In patients that are unable to read, "
                "the research nurse will be available to assist.\nExclusion Criteria:\n* Pregnancy",
                "Exclusion Criteria:\n* Unable to provide consent and no legally authorized representative available"):
            with self.subTest(crit=crit):
                self.assertTrue(ec.accommodations(crit))

    def test_not_offered(self):
        for crit in (
                "Exclusion Criteria:\n* Use of drugs affecting pupil size or accommodation",
                "Inclusion Criteria:\n* Access for device delivery to accommodate a 22F sheath\n"
                "Exclusion Criteria:\n* Pregnancy",
                "Inclusion Criteria:\n* Parent or legally authorized representative must sign consent\n"
                "Exclusion Criteria:\n* Pregnancy",
                "Inclusion Criteria:\n* Parent(s) or legal guardian(s) must provide written informed consent\n"
                "Exclusion Criteria:\n* Pregnancy",
                "Inclusion Criteria:\n* Sufficient English to permit communication without an interpreter\n"
                "Exclusion Criteria:\n* Pregnancy",
                "Inclusion Criteria:\n* Able to walk without an assistive device\nExclusion Criteria:\n* Pregnancy",
                "Exclusion Criteria:\n* Requires use of sign language interpreter",
                "Exclusion Criteria:\n* Patients whose consent needs to be obtained through a surrogate",
                "Exclusion Criteria:\n* Severe visual impairment, defined as being unable to read large-print materials"):
            with self.subTest(crit=crit):
                self.assertEqual(ec.accommodations(crit), [])

    def test_census_samples_accommodation_items(self):
        recs = [{"nct": "N1", "criteria": "Inclusion Criteria:\n* Subject or legally authorized representative consents\n"
                                          "Exclusion Criteria:\n* Pregnancy"},
                {"nct": "N2", "criteria": "Inclusion Criteria:\n* Parent or guardian consents\n"
                                          "Exclusion Criteria:\n* Pregnancy"}]
        res = ec.census(recs)
        self.assertEqual(res["total"]["accommodation_pct"], 50.0)
        self.assertEqual(res["samples"]["accommodation"],
                         [("N1", "Subject or legally authorized representative consents")])


class RequirementTests(unittest.TestCase):
    def test_requirements(self):
        cases = {
            "Able to walk 100 m without assistance": {"mobility"},
            "Ambulatory without a walking aid": {"mobility"},
            "Willing and able to provide written informed consent": {"consent_capacity"},
            "Normal or corrected-to-normal vision": {"visual"},
            "Normal hearing": {"hearing"},
            "Able to read and write": {"communication"},
            "MMSE score of 24 or higher": {"cognitive"},
            "Cognitively intact": {"cognitive"},
        }
        for item, want in cases.items():
            with self.subTest(item=item):
                self.assertEqual(ec.requirements(item), want)

    def test_not_required(self):
        for item in ("Able to read and write English",
                     "Able to provide informed consent, or consent from a legally authorized representative",
                     "Parent or guardian able to provide informed consent",
                     "Ambulatory blood pressure above 130/80",
                     "Stable dose of medication for 3 months",
                     "Unable to walk",
                     "Able to comply with study procedures",
                     "Age 18 or older"):
            with self.subTest(item=item):
                self.assertEqual(ec.requirements(item), set())

    def test_analyze_reads_both_sections(self):
        a = ec.analyze({"criteria": "Inclusion Criteria:\n* Able to walk 6 minutes unaided\n"
                                    "Exclusion Criteria:\n* Legally blind",
                        "conditions": ["Heart Failure"]})
        self.assertEqual(set(a["hits"]), {"visual"})
        self.assertEqual(a["requires"], {"mobility": ["Able to walk 6 minutes unaided"]})
        self.assertEqual(a["related_req"], set())

    def test_inline_both(self):
        a = ec.analyze({"criteria": "Inclusion criteria: adults able to walk. Exclusion criteria: unable to read."})
        self.assertEqual(set(a["requires"]), {"mobility"})
        self.assertIn("communication", a["hits"])

    def test_related_requirement(self):
        a = ec.analyze({"criteria": "Inclusion Criteria:\n* Able to walk 10 m\nExclusion Criteria:\n* Pregnancy",
                        "conditions": ["Stroke"]})
        self.assertEqual(a["related_req"], {"mobility"})

    def test_check_text_lists_requirements(self):
        out = ec.check_text("Inclusion Criteria:\n* Normal hearing\n* Adults\nExclusion Criteria:\n* Pregnancy")
        self.assertIn("No disability-related exclusion items found", out)
        self.assertIn("Inclusion items that require an ability:", out)
        self.assertIn("- Normal hearing", out)
        self.assertIn("  requires: hearing", out)
        self.assertIn(ec.REQUIRE_SUGGESTIONS["hearing"], out)
        self.assertNotIn("- Adults", out)


class AnalyzeTests(unittest.TestCase):
    def test_accommodation(self):
        a = ec.analyze({"criteria": "Inclusion Criteria:\n* Adults; a legally authorized representative may consent\n"
                                    "Exclusion Criteria:\n* Dementia"})
        self.assertTrue(a["accommodation"])
        self.assertEqual(a["accommodations"], ["Adults; a legally authorized representative may consent"])
        self.assertIn("cognitive", a["hits"])

    def test_condition_related(self):
        a = ec.analyze({"criteria": "Exclusion Criteria:\n* Visual acuity worse than 20/200\n* Deafness",
                        "conditions": ["Glaucoma"], "title": "Eye drops"})
        self.assertEqual(set(a["hits"]), {"visual", "hearing"})
        self.assertEqual(a["related"], {"visual"})

    def test_item_counts(self):
        a = ec.analyze({"criteria": "Exclusion Criteria:\n* Deafness\n* Pregnancy\n* Legally blind; dementia"})
        self.assertEqual(a["n_items"], 3)
        self.assertEqual(a["core_items"], 2)

    def test_sarcoma_is_not_coma(self):
        a = ec.analyze({"criteria": "Exclusion Criteria:\n* Unable to provide informed consent",
                        "conditions": ["Soft Tissue Sarcoma"]})
        self.assertIn("consent_capacity", a["hits"])
        self.assertEqual(a["related"], set())

    def test_check_text(self):
        out = ec.check_text("Exclusion Criteria:\n* Deafness\n* Pregnancy")
        self.assertIn("Deafness", out)
        self.assertIn("hearing", out)
        self.assertIn("consider:", out)
        self.assertNotIn("Pregnancy", out)
        self.assertNotIn("Inclusion items", out)
        self.assertIn("Accommodation offered in the criteria: no", out)

    def test_check_text_lists_accommodations(self):
        out = ec.check_text("Inclusion Criteria:\n* Consent by the patient or a legal representative\n"
                            "Exclusion Criteria:\n* Deafness")
        self.assertIn("Accommodation offered in the criteria: yes\n- Consent by the patient or a legal representative",
                      out)

    def test_check_text_nothing(self):
        self.assertEqual(ec.check_text("Adults with asthma."), "No exclusion criteria section found.")


class ApiTests(unittest.TestCase):
    def test_extract(self):
        s = study("NCT01", criteria="Exclusion Criteria:\n* Deafness", conditions=["Asthma"],
                  start="2019-05", sponsor="NIH")
        s["protocolSection"]["eligibilityModule"]["healthyVolunteers"] = False
        s["protocolSection"]["designModule"]["enrollmentInfo"] = {"count": 40}
        r = ec.extract(s)
        self.assertEqual(r["nct"], "NCT01")
        self.assertEqual(r["start"], "2019-05")
        self.assertEqual(r["sponsor_class"], "NIH")
        self.assertEqual(r["phases"], ["PHASE2"])
        self.assertEqual(r["conditions"], ["Asthma"])
        self.assertIs(r["healthy"], False)
        self.assertEqual(r["enrollment"], 40)

    def test_extract_missing_modules(self):
        r = ec.extract({"protocolSection": {"identificationModule": {"nctId": "NCT02"}}})
        self.assertEqual(r["nct"], "NCT02")
        self.assertIsNone(r["start"])
        self.assertIsNone(r["sponsor_class"])
        self.assertEqual(r["criteria"], "")

    def test_paging_and_fallback(self):
        urls = []
        pages = [
            {"totalCount": 3, "nextPageToken": "t2",
             "studies": [study("NCT1", stype="OBSERVATIONAL"), study("NCT2")]},
            {"studies": [study("NCT3")]},
        ]

        def get(url):
            urls.append(url)
            if len(urls) == 1:
                raise urllib.error.HTTPError(url, 400, "Bad Request", None, None)
            return pages[len(urls) - 2]

        recs = list(ec.iter_studies(get=get, pause=0))
        self.assertEqual([r["nct"] for r in recs], ["NCT2", "NCT3"])
        self.assertIn("filter.advanced", urls[0])
        self.assertIn("fields=", urls[1])
        self.assertNotIn("filter.advanced", urls[1])
        self.assertIn("pageToken=t2", urls[2])

    def test_cache_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            cache = os.path.join(d, "c.jsonl.gz")
            recs = list(ec.load_records(cache, get=lambda url: {"studies": [study("NCT9")]}))
            self.assertEqual(len(recs), 1)
            self.assertTrue(os.path.exists(cache))

            def offline(url):
                raise AssertionError("should read the cache")
            again = list(ec.load_records(cache, get=offline))
            self.assertEqual(again[0]["nct"], "NCT9")


class CensusTests(unittest.TestCase):
    def records(self):
        return [
            {"nct": "NCT1", "start": "2019-03", "sponsor_class": "NIH", "phases": ["PHASE3"],
             "conditions": ["Diabetes"], "criteria": "Exclusion Criteria:\n* Legally blind\n* Unable to walk"},
            {"nct": "NCT2", "start": "2025-01", "sponsor_class": "INDUSTRY", "phases": [],
             "conditions": ["Asthma"], "criteria": "Exclusion Criteria:\n* Pregnancy"},
            {"nct": "NCT3", "criteria": ""},
        ]

    def test_aggregates(self):
        res = ec.census(self.records())
        self.assertEqual(res["records"], 3)
        self.assertEqual(res["with_criteria"], 2)
        t = res["total"]
        self.assertEqual(t["trials"], 2)
        self.assertEqual(t["any_core_pct"], 50.0)
        self.assertEqual(t["visual_pct"], 50.0)
        self.assertEqual(t["mobility_unrelated_pct"], 50.0)
        self.assertEqual(set(res["by_year"]), {2019, 2025})
        self.assertEqual(res["by_year"][2019]["any_core_pct"], 100.0)
        self.assertEqual(res["plosky_areas"]["diabetes"]["trials"], 1)
        self.assertEqual(res["plosky_areas"]["diabetes"]["visual_pct"], 100.0)
        self.assertEqual(res["plosky_areas"]["dementia"]["trials"], 0)
        self.assertEqual(res["by_phase"]["NA"]["trials"], 1)
        self.assertEqual(res["samples"]["visual"], [("NCT1", "Legally blind")])
        self.assertEqual(len(res["trials"]), 2)

    def test_items_and_design(self):
        res = ec.census(self.records())
        t = res["total"]
        self.assertEqual(t["exclusion_items_mean"], 1.5)
        self.assertEqual(t["core_items_per_100"], 66.67)
        self.assertEqual(set(res["by_year_design"]), {"2019|phased", "2025|no_phase"})
        self.assertEqual(res["by_year_design"]["2019|phased"]["any_core_pct"], 100.0)
        self.assertEqual(res["by_year_design"]["2025|no_phase"]["any_core_pct"], 0.0)
        rows = {r[0]: r for r in res["trials"]}
        self.assertEqual(rows["NCT1"][ec.TRIAL_COLUMNS.index("exclusion_items")], 2)
        self.assertEqual(ec.design_of(["NA"]), "no_phase")
        self.assertEqual(ec.design_of(["PHASE1", "PHASE2"]), "phased")
        self.assertEqual(ec.design_of(None), "no_phase")

    def test_requirement_aggregates(self):
        recs = [
            {"nct": "N1", "start": "2020-01", "conditions": ["Asthma"],
             "criteria": "Inclusion Criteria:\n* Able to walk 6 minutes unaided\nExclusion Criteria:\n* Pregnancy"},
            {"nct": "N2", "start": "2020-02", "conditions": ["Asthma"],
             "criteria": "Inclusion Criteria:\n* Adults\nExclusion Criteria:\n* Legally blind"},
        ]
        res = ec.census(recs)
        t = res["total"]
        self.assertEqual(t["trials"], 2)
        self.assertEqual(t["any_core_pct"], 50.0)
        self.assertEqual(t["any_required_pct"], 50.0)
        self.assertEqual(t["mobility_required_pct"], 50.0)
        self.assertEqual(t["visual_required_pct"], 0.0)
        self.assertEqual(t["required_only_pct"], 50.0)
        self.assertEqual(t["any_barrier_pct"], 100.0)
        self.assertEqual(res["by_year"][2020]["any_required_pct"], 50.0)
        self.assertEqual(res["samples"]["required_mobility"], [("N1", "Able to walk 6 minutes unaided")])
        rows = {r[0]: r for r in res["trials"]}
        req = ec.TRIAL_COLUMNS.index("required")
        self.assertEqual(rows["N1"][req], "mobility")
        self.assertEqual(rows["N2"][req], "")
        self.assertEqual(len(ec.TRIAL_COLUMNS), len(rows["N1"]))

    def test_seed_changes_sample_only(self):
        recs = [{"nct": "S%d" % i, "start": "2020-01", "criteria": "Exclusion Criteria:\n* Deafness"}
                for i in range(200)]
        a, b = ec.census(recs, seed=2026), ec.census(recs, seed=2027)
        self.assertEqual(a["total"], b["total"])
        self.assertEqual(len(a["samples"]["hearing"]), 60)
        self.assertNotEqual(a["samples"]["hearing"], b["samples"]["hearing"])

    def test_outputs(self):
        res = ec.census(self.records())
        with tempfile.TemporaryDirectory() as d:
            ec.write_outputs(res, d, "2026-10-14")
            for name in ("summary.json", "results.md", "by_year.csv", "by_year_design.csv", "by_sponsor.csv",
                         "by_phase.csv", "plosky_areas.csv", "sample_items.csv", "trials.csv.gz"):
                self.assertTrue(os.path.exists(os.path.join(d, name)), name)
            with open(os.path.join(d, "summary.json"), encoding="utf-8") as f:
                summary = json.load(f)
            self.assertEqual(summary["version"], ec.__version__)
            self.assertEqual(summary["total"]["trials"], 2)
            self.assertEqual(summary["sample_seed"], 2026)
            with open(os.path.join(d, "results.md"), encoding="utf-8") as f:
                md = f.read()
            self.assertIn("Disability-related exclusion criteria", md)
            self.assertIn("Ability requirements in the inclusion criteria", md)
            self.assertIn("Is a trend only longer criteria or a different mix of trials?", md)
            self.assertIn("| 2019 | 2.0 | 100.0 | 1 | 100.0 | 0 | None |", md)


if __name__ == "__main__":
    unittest.main()
