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
        self.assertIn("cognitive", a["hits"])

    def test_condition_related(self):
        a = ec.analyze({"criteria": "Exclusion Criteria:\n* Visual acuity worse than 20/200\n* Deafness",
                        "conditions": ["Glaucoma"], "title": "Eye drops"})
        self.assertEqual(set(a["hits"]), {"visual", "hearing"})
        self.assertEqual(a["related"], {"visual"})

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
        self.assertIn("Accommodation mentioned anywhere in the criteria: no", out)

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
        self.assertEqual(rows["N1"][-1], "mobility")
        self.assertEqual(rows["N2"][-1], "")
        self.assertEqual(len(ec.TRIAL_COLUMNS), len(rows["N1"]))

    def test_outputs(self):
        res = ec.census(self.records())
        with tempfile.TemporaryDirectory() as d:
            ec.write_outputs(res, d, "2026-10-14")
            for name in ("summary.json", "results.md", "by_year.csv", "by_sponsor.csv", "by_phase.csv",
                         "plosky_areas.csv", "sample_items.csv", "trials.csv.gz"):
                self.assertTrue(os.path.exists(os.path.join(d, name)), name)
            with open(os.path.join(d, "summary.json"), encoding="utf-8") as f:
                summary = json.load(f)
            self.assertEqual(summary["version"], ec.__version__)
            self.assertEqual(summary["total"]["trials"], 2)
            with open(os.path.join(d, "results.md"), encoding="utf-8") as f:
                md = f.read()
            self.assertIn("Disability-related exclusion criteria", md)
            self.assertIn("Ability requirements in the inclusion criteria", md)


if __name__ == "__main__":
    unittest.main()
