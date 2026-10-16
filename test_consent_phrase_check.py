"""Offline tests for consent_phrase_check (no network). Apache-2.0."""

import csv
import json
import os
import tempfile
import unittest
import urllib.parse
from unittest import mock

import consent_phrase_check as cpc


def study(nct, text, start=None, phases=None, min_age=None):
    p = {"identificationModule": {"nctId": nct},
         "eligibilityModule": {"eligibilityCriteria": text},
         "designModule": {"studyType": "INTERVENTIONAL"}}
    if start:
        p["statusModule"] = {"startDateStruct": {"date": start}}
    if phases is not None:
        p["designModule"]["phases"] = phases
    if min_age:
        p["eligibilityModule"]["minimumAge"] = min_age
    return {"protocolSection": p}


S1 = study("NCT00000001",
           "Inclusion Criteria:\n* Ability to understand and the willingness to sign a written informed consent"
           " document, or a legally authorized representative (LAR) to sign\n\nExclusion Criteria:\n* Pregnant",
           "2010-05", ["PHASE2"], "18 Years")
S2 = study("NCT00000002",
           "Inclusion Criteria:\n* Ability to understand and the willingness to sign consent\n\n"
           "Exclusion Criteria:\n* Requires a legal guardian",
           "2010-11-02", ["NA"], "18 Years")
S3 = study("NCT00000003",
           "Inclusion Criteria:\n- Ability to understand and willingness to sign (parent or guardian for minors)",
           "2020-01-01", ["PHASE1", "PHASE2"], "12 Years")
S4 = study("NCT00000004",
           "Inclusion Criteria: ability to understand and the willingness to sign. Exclusion Criteria: none",
           "2020-02")
S5 = study("NCT00000005", "Willingness to sign; able to understand.")
PAGES = {None: {"totalCount": 5, "studies": [S1, S2, S3], "nextPageToken": "t2"},
         "t2": {"studies": [S4, S5]}}


def fake(u):
    q = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
    assert q["query.term"] == [cpc.SEARCH]
    return PAGES[q.get("pageToken", [None])[0]]


class ParseTests(unittest.TestCase):
    def test_url(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(cpc.url("abc", 10)).query)
        self.assertEqual((q["pageToken"], q["pageSize"]), (["abc"], ["10"]))
        self.assertNotIn("pageToken", urllib.parse.urlparse(cpc.url()).query)

    def test_years_from_age(self):
        self.assertEqual(cpc.years_from_age("18 Years"), 18.0)
        self.assertEqual(cpc.years_from_age("6 Months"), 0.5)
        self.assertIsNone(cpc.years_from_age(None))
        self.assertIsNone(cpc.years_from_age("N/A"))

    def test_paths(self):
        rep = cpc.PATHS["representative"]
        for t in ("legally authorized representative", "Legally Authorised Representatives",
                  "legally acceptable representative", "legal representative",
                  "authorized representative", "signed by the LAR"):
            self.assertIsNotNone(rep.search(t), t)
        self.assertEqual(rep.search("who have a legally-authorized representative (LAR)").group(0),
                         "legally-authorized representative")
        self.assertIsNone(rep.search("signed by Lars"))
        idmc = cpc.PATHS["idmc"]
        self.assertIsNotNone(idmc.search("Participants with impaired decision-making capacity (IDMC) who have"))
        self.assertIsNone(idmc.search("reviewed by the IDMC"))
        self.assertIsNone(rep.search("legal guardian"))
        self.assertIsNotNone(cpc.PATHS["surrogate"].search("health care proxy"))
        self.assertIsNotNone(cpc.PATHS["surrogate"].search("next of kin"))
        self.assertIsNone(cpc.STOCK.search("ability to understand and willingness to sign"))
        self.assertIsNotNone(cpc.STOCK_LOOSE.search("ability to understand and willingness to sign"))

    def test_templates(self):
        t = cpc.TEMPLATES
        self.assertIsNotNone(t["nci_lar_may_sign"].search(
            "Legally authorized representatives may sign and give informed consent on behalf of study participants."))
        self.assertIsNotNone(t["nci_idmc_also_eligible"].search(
            "Participants with impaired decision-making capacity (IDMC) who have a legally-authorized"
            " representative (LAR) and/or family member available will also be eligible"))
        self.assertIsNotNone(t["nci_idmc_must_have"].search(
            "Patients with impaired decision-making capacity (IDMC) must have a legally authorized"
            " representative or caregiver who gives such consent."))
        self.assertIsNone(t["nci_idmc_also_eligible"].search(
            "Patients with impaired decision-making capacity are excluded. Patients with HIV will also be eligible"))
        row = cpc.classify(study("NCT00000009", "Legally Authorized Representatives may sign and give informed"
                                 " consent on behalf of study participants"))
        self.assertEqual((row["nci_lar_may_sign"], row["nci_idmc_also_eligible"], row["representative"]),
                         (True, False, True))

    def test_classify(self):
        r = cpc.classify(S1)
        self.assertEqual((r["nct_id"], r["start_year"], r["phase"], r["adult_only"]),
                         ("NCT00000001", 2010, "PHASE2", True))
        self.assertTrue(r["stock_exact"] and r["representative"] and r["adult_path"] and r["adult_path_inclusion"])
        self.assertEqual(r["representative_section"], "inclusion")
        self.assertEqual(len(r["snippets"]), 2)
        r = cpc.classify(S2)
        self.assertEqual((r["guardian"], r["guardian_section"], r["adult_path_inclusion"]),
                         (True, "exclusion", False))
        r = cpc.classify(S3)
        self.assertEqual((r["stock_exact"], r["stock_loose"], r["parent"], r["phase"], r["adult_only"]),
                         (False, True, True, "PHASE1/PHASE2", False))
        r = cpc.classify(S4)
        self.assertEqual((r["phase"], r["adult_only"], r["adult_path"], r["snippets"]), ("NONE", None, False, []))
        r = cpc.classify(S5)
        self.assertEqual((r["start_year"], r["stock_loose"], r["has_exclusion_heading"]), (None, False, False))

    def test_section(self):
        m = cpc.PATHS["guardian"]
        text = "guardian ... Exclusion Criteria: guardian"
        self.assertEqual(cpc.section(list(m.finditer(text)), text.index("Exclusion")), "both")
        self.assertEqual(cpc.section([], 5), "")


class RunTests(unittest.TestCase):
    def setUp(self):
        found, self.total = cpc.studies(fetch=fake, pause=0)
        self.rows = [cpc.classify(s) for s in found]

    def test_pages(self):
        self.assertEqual((len(self.rows), self.total), (5, 5))

    def test_summary(self):
        s = cpc.summarize(self.rows, self.total)
        self.assertEqual((s["downloaded"], s["stock_exact"], s["stock_loose_only"], s["neither"]), (5, 3, 1, 1))
        self.assertEqual(s["adult_path"], {"trials": 3, "with": 2, "pct": 66.667})
        self.assertEqual(s["adult_path_inclusion"], {"trials": 3, "with": 1, "pct": 33.333})
        self.assertEqual(s["adult_path_adult_only"], {"trials": 2, "with": 2, "pct": 100.0})
        self.assertEqual(s["paths"], {"representative": 1, "guardian": 1, "surrogate": 0, "parent": 0, "idmc": 0})
        self.assertEqual([r["with"] for r in s["idmc_by_year"]], [0, 0])
        self.assertEqual(s["by_year"], [{"start_year": 2010, "trials": 2, "with": 2, "pct": 100.0},
                                        {"start_year": 2020, "trials": 1, "with": 0, "pct": 0.0}])
        self.assertEqual([(r["phase"], r["with"]) for r in s["by_phase"]], [("NA", 1), ("NONE", 0), ("PHASE2", 1)])
        self.assertEqual(s["templates"]["nci_lar_may_sign"], {"trials": 3, "with": 0, "pct": 0.0})
        self.assertEqual([r["start_year"] for r in s["template_by_year"]["nci_idmc_also_eligible"]], [2010, 2020])

    def test_reading_sample(self):
        got = cpc.reading_sample(self.rows)
        self.assertEqual(sorted(r["nct_id"] for r in got), ["NCT00000001", "NCT00000002"])
        self.assertEqual(len(cpc.reading_sample(self.rows, k=1)), 1)

    def test_main_writes_files(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(cpc, "fetch_json", fake), mock.patch("builtins.print"):
                rc = cpc.main(["--out-dir", d, "--pause", "0"])
            self.assertEqual(rc, 0)
            with open(os.path.join(d, "consent-phrase.json"), encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["summary"]["stock_exact"], 3)
            self.assertEqual(len(data["reading_sample"]), 2)
            with open(os.path.join(d, "consent-phrase-trials.csv"), newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 5)
            self.assertIn("representative: ", rows[0]["snippets"])
            with open(os.path.join(d, "CONSENT-PHRASE.md"), encoding="utf-8") as f:
                md = f.read()
            self.assertIn("Of 3 trials with the exact line, 2 (66.667%) name", md)
            self.assertIn("| 2010 | 2 | 2 | 100.0 |", md)
            self.assertIn("NCI template wording: nci_idmc_must_have 0; nci_idmc_also_eligible 0; nci_lar_may_sign 0.", md)
            self.assertIn("| 2010 | 2 | 0 | 0 | 0 |", md)


if __name__ == "__main__":
    unittest.main()
