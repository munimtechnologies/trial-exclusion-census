"""Offline tests for consent_sponsor.py (no network). Apache-2.0.

Expected values for the small synthetic tables below were worked out outside the code by AI
agents working for MV2 on 2026-10-30; the Wilson interval is checked against the 46.2-72.4
printed in results/consent-phrase/CONSENT-RESULT.md for 30 of 50.
"""

import csv
import io
import os
import re
import unittest
import urllib.parse

import consent_sponsor as cs

HERE = os.path.dirname(os.path.abspath(__file__))


def table(specs):
    """CSV bytes in the published table's layout from (nct, year, exact, loose, path, adult)."""
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(cs.HEADER)
    for nct, year, exact, loose, path, adult in specs:
        row = dict.fromkeys(cs.HEADER, "")
        row.update({"nct_id": nct, "start_year": year, "stock_exact": str(exact),
                    "stock_loose": str(loose), "adult_path": str(path), "adult_only": str(adult)})
        w.writerow([row[h] for h in cs.HEADER])
    return out.getvalue().encode("utf-8")


SPECS = [("NCT00000001", "2021", True, True, True, True),
         ("NCT00000002", "2018", True, True, False, True),
         ("NCT00000003", "2022", False, True, True, True),
         ("NCT00000004", "2015", True, True, False, True),
         ("NCT00000005", "2016", True, True, True, False),
         ("NCT00000006", "2020", False, False, False, True)]

STUDIES = {
    "NCT00000001": ("Some University", "OTHER", [("National Cancer Institute (NCI)", "NIH")]),
    "NCT00000002": ("National Cancer Institute (NCI)", "NIH", []),
    "NCT00000003": ("Washington University School of Medicine", "OTHER", []),
    "NCT00000004": ("A Drug Company", "INDUSTRY", []),
    "NCT00000005": ("University X", "OTHER", [("National Cancer Institute, Egypt", "OTHER")]),
}


def study(nct, lead, cls, collabs):
    sc = {"leadSponsor": {"name": lead, "class": cls}}
    if collabs:
        sc["collaborators"] = [{"name": n, "class": c} for n, c in collabs]
    return {"protocolSection": {"identificationModule": {"nctId": nct},
                                "sponsorCollaboratorsModule": sc}}


def fake_fetch(url):
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    ids = q["filter.ids"][0].split(",")
    return {"studies": [study(i, *STUDIES[i]) for i in ids if i in STUDIES]}


EXPECTED = {"rows": 6, "population": 5, "exact": 4, "exact_adult_path": 2}


def synthetic():
    data = table(SPECS)
    header, rows = cs.read_table(data)
    pop = cs.population(rows)
    sponsors = cs.fetch_sponsors([r["nct_id"] for r in pop], fetch=fake_fetch, pause=0)
    return cs.result_from(data, header, rows, pop, sponsors, expected=EXPECTED)


class HelperTests(unittest.TestCase):
    def test_header_is_the_published_one(self):
        self.assertEqual(len(cs.HEADER), 24)
        self.assertEqual(cs.HEADER[18], "adult_path")

    def test_period(self):
        self.assertEqual(cs.period("2019"), "<=2019")
        self.assertEqual(cs.period("1999"), "<=2019")
        self.assertEqual(cs.period("2020"), "2020-2026")
        self.assertEqual(cs.period("2026"), "2020-2026")
        self.assertIsNone(cs.period("2027"))
        self.assertIsNone(cs.period(""))

    def test_wilson_matches_consent_result(self):
        lo, hi = cs.wilson(30, 50)
        self.assertAlmostEqual(lo, 0.462, places=3)
        self.assertAlmostEqual(hi, 0.724, places=3)
        self.assertIsNone(cs.wilson(0, 0))

    def test_risk_ratio(self):
        r = cs.risk_ratio(20, 100, 10, 100)
        self.assertEqual(r["rr"], 2.0)
        self.assertAlmostEqual(r["low"], 0.99, places=2)
        self.assertAlmostEqual(r["high"], 4.05, places=2)
        self.assertIsNone(cs.risk_ratio(0, 10, 1, 10)["rr"])

    def test_groups(self):
        rec = {"lead": "X", "lead_class": "OTHER",
               "collaborators": [("National Cancer Institute (NCI) ", "NIH")]}
        self.assertTrue(cs.nci_linked(rec))
        rec["collaborators"] = [("National Cancer Institute, Egypt", "OTHER")]
        self.assertFalse(cs.nci_linked(rec))
        self.assertTrue(cs.washu_led({"lead": "washington university school of medicine"}))
        self.assertFalse(cs.washu_led({"lead": "Washington University in St. Louis"}))
        self.assertEqual(cs.lead_bucket({"lead_class": "fed"}), "OTHER_KINDS")
        self.assertEqual(cs.lead_bucket({"lead_class": "INDUSTRY"}), "INDUSTRY")

    def test_fetch_follows_page_tokens(self):
        calls = []

        def fetch(url):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            calls.append(q)
            if "pageToken" not in q:
                return {"studies": [study("NCT1", "A", "OTHER", [])], "nextPageToken": "t2"}
            return {"studies": [study("NCT2", "B", "INDUSTRY", [])]}

        out = cs.fetch_sponsors(["NCT1", "NCT2"], fetch=fetch, pause=0)
        self.assertEqual(sorted(out), ["NCT1", "NCT2"])
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["fields"][0], cs.FIELDS)

    def test_fetch_batches_of_100(self):
        seen = []

        def fetch(url):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            seen.append(len(q["filter.ids"][0].split(",")))
            return {"studies": []}

        cs.fetch_sponsors(["NCT%08d" % i for i in range(250)], fetch=fetch, pause=0)
        self.assertEqual(seen, [100, 100, 50])


class SyntheticRunTests(unittest.TestCase):
    def setUp(self):
        self.result, self.lab = synthetic()
        self.a = self.result["analysis"]

    def test_gates_pass(self):
        self.assertTrue(all(self.result["gates"].values()), self.result["gates"])
        self.assertEqual(self.result["counts"]["population"], 5)
        self.assertEqual(self.result["counts"]["coverage"], 1.0)

    def test_groups(self):
        g = self.a["groups"]
        self.assertEqual((g["nci_linked"]["with_path"], g["nci_linked"]["trials"]), (1, 2))
        self.assertEqual((g["washu_led"]["with_path"], g["washu_led"]["trials"]), (1, 1))
        self.assertEqual((g["neither"]["with_path"], g["neither"]["trials"]), (1, 2))
        self.assertEqual(self.a["template_owner_paths"], 2)
        self.assertEqual(self.a["paths"], 3)
        self.assertEqual(self.a["template_owner_share_of_paths"], 0.6667)
        self.assertEqual(self.a["template_owner_share_of_trials"], 0.6)

    def test_ratios(self):
        r = self.a["rr_nci_vs_neither"]
        self.assertEqual(r["rr"], 1.0)
        self.assertAlmostEqual(r["low"], 0.141, places=3)
        self.assertEqual(self.a["rr_washu_vs_neither"]["rr"], 2.0)
        self.assertIsNone(self.a["rr_neither_late_vs_early"]["rr"])

    def test_predictions(self):
        self.assertEqual(self.result["predictions"],
                         {"P1": False, "P2": False, "P3": False, "P4": True, "P5": False})

    def test_secondary_adult_only_drops_child_rows(self):
        s = self.result["secondary_adult_only"]
        self.assertEqual(s["groups"]["all"]["trials"], 4)

    def test_gate_failure_means_no_grading(self):
        data = table(SPECS)
        header, rows = cs.read_table(data)
        pop = cs.population(rows)
        sponsors = cs.fetch_sponsors([r["nct_id"] for r in pop], fetch=fake_fetch, pause=0)
        del sponsors["NCT00000005"]
        result, _ = cs.result_from(data, header, rows, pop, sponsors, expected=EXPECTED)
        self.assertFalse(result["gates"]["G4_coverage"])
        self.assertIsNone(result["predictions"])
        self.assertIn("not graded", cs.markdown(result))

    def test_markdown_lines(self):
        text = cs.markdown(self.result)
        self.assertIn("group nci_linked: 1 of 2 (50.0%;", text)
        self.assertIn("predictions: P1=False, P2=False, P3=False, P4=True, P5=False", text)


class WordingTests(unittest.TestCase):
    def test_header_and_wording(self):
        with open(os.path.join(HERE, "consent_sponsor.py"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("Apache-2.0", text)
        self.assertIn("Made by MV2 of Munim, Inc. with AI agents.", text)
        self.assertIn("mv2@munimtech.com", text)
        self.assertEqual(re.findall(r"by\s+hand|by\s+eye|hand[- ]check", text, re.I), [])

    def test_thresholds_match_prereg(self):
        self.assertEqual((cs.P1_MIN_RR, cs.P2_MIN_RR, cs.P3_MIN_PATH_SHARE, cs.P3_MAX_TRIAL_SHARE,
                          cs.P4_MAX_FRACTION, cs.P5_MAX_RISE), (1.5, 3.0, 0.40, 0.30, 0.5, 2.0))


if __name__ == "__main__":
    unittest.main()
