"""Offline tests for sponsor_check (no network). Apache-2.0."""

import json
import os
import tempfile
import unittest
import urllib.parse
from unittest import mock

import sponsor_check as sc
import trend_check as tc

T = sc.term
HEAR = "hearing (all wordings)"
NOT_HEAR = sc.FAMILY_NOT_OWN[HEAR]
COUNTS = {
    T("va"): 100, T(): 1000,
    T("va", no_phase=True): 50, T(no_phase=True): 400,
    T("va", HEAR): 6, T(phrase=HEAR): 20,
    T("va", HEAR, no_phase=True): 4, T(phrase=HEAR, no_phase=True): 10,
    T("va", HEAR, not_condition=NOT_HEAR): 3, T(phrase=HEAR, not_condition=NOT_HEAR): 15,
    T("va", "pregnant"): 30, T(phrase="pregnant"): 600,
}


def fake(u):
    q = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
    return {"totalCount": COUNTS[q["query.term"][0]]}


class TermTests(unittest.TestCase):
    def test_term(self):
        self.assertEqual(T(), "AREA[StudyType]INTERVENTIONAL")
        self.assertEqual(
            T("va", "dementia", no_phase=True),
            "AREA[StudyType]INTERVENTIONAL AND AREA[LeadSponsorClass]FED"
            " AND AREA[LeadSponsorName](VA OR Veteran OR Veterans)"
            ' AND AREA[Phase]NA AND AREA[EligibilityCriteria]"dementia"')
        self.assertTrue(T("va", HEAR, not_condition=NOT_HEAR).endswith(
            " AND NOT AREA[ConditionSearch](hearing OR deafness OR tinnitus OR ear)"))

    def test_custom_fragment(self):
        self.assertEqual(T("AREA[LeadSponsorClass]OTHER_GOV"),
                         "AREA[StudyType]INTERVENTIONAL AND AREA[LeadSponsorClass]OTHER_GOV")

    def test_phrases(self):
        self.assertEqual(set(sc.FAMILY_NOT_OWN), set(tc.FAMILIES))
        self.assertFalse(any(tc.kind(p) == "disability" for p in sc.PHRASES))
        self.assertTrue(all("," not in p for p in sc.PHRASES))


class RunTests(unittest.TestCase):
    def setUp(self):
        self.rows = sc.run("va", [HEAR, "pregnant"], fetch=fake, pause=0)

    def test_rows(self):
        h, p = self.rows
        self.assertEqual((h["kind"], h["sponsor_pct"], h["registry_pct"]), ("family", 6.0, 2.0))
        self.assertAlmostEqual(h["ratio"], 3.0)
        self.assertAlmostEqual(h["no_phase_ratio"], 3.2)
        self.assertAlmostEqual(h["not_own_condition_ratio"], 2.0)
        self.assertEqual(p["kind"], "control")
        self.assertAlmostEqual(p["ratio"], 0.5)
        self.assertNotIn("no_phase_ratio", p)

    def test_share_ratio_zero(self):
        self.assertIsNone(sc.share_ratio(1, 10, 0, 10))
        self.assertIsNone(sc.share_ratio(1, 0, 1, 10))

    def test_markdown(self):
        md = sc.markdown(self.rows, "va")
        self.assertIn("| hearing (all wordings) | family | 6.0 | 2.0 | 3.0 | 3.2 | 2.0 |", md)
        self.assertIn("| pregnant | control | 30.0 | 60.0 | 0.5 |  |  |", md)
        self.assertIn("Families against controls", md)

    def test_main_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "va.json")
            with mock.patch.object(tc, "fetch_json", fake), mock.patch("builtins.print"):
                rc = sc.main(["--sponsor", "va", "--phrases", HEAR + ",pregnant",
                              "--json", out, "--pause", "0"])
            self.assertEqual(rc, 0)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["sponsor"], "va")
            self.assertEqual(len(data["rows"]), 2)
            self.assertEqual(data["family_test"]["families"], 1)


# VA / registry ratios counted on 2026-10-15 (results/sponsor-check/VA-CHECK.md).
VA_FAMILIES = [3.33, 2.6, 2.67]
VA_CONTROLS = [0.58, 0.24, 0.39, 0.78, 0.21, 2.22, 0.91, 1.73, 0.26, 0.64, 0.32]


class PublishedTests(unittest.TestCase):
    def test_va_rank_test(self):
        self.assertEqual(tc.rank_test(VA_FAMILIES, VA_CONTROLS), (39.0, 0.0027))

    def test_family_test(self):
        rows = ([{"kind": "family", "ratio": v} for v in VA_FAMILIES]
                + [{"kind": "control", "ratio": v} for v in VA_CONTROLS[:3]]
                + [{"kind": "rare control", "ratio": v} for v in VA_CONTROLS[3:]]
                + [{"kind": "reference", "ratio": 0.66}])
        t = sc.family_test(rows)
        self.assertEqual((t["families"], t["controls"], t["control_max"]), (3, 11, 2.22))
        self.assertEqual((t["rank_sum"], t["p"]), (39.0, 0.0027))


if __name__ == "__main__":
    unittest.main()
