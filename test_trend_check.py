"""Offline tests for trend_check (no network). Apache-2.0."""

import json
import os
import tempfile
import unittest
import urllib.parse
from unittest import mock

import trend_check as tc

T = tc.term
HL = tc.NOT_OWN_CONDITION["hearing loss"]
COUNTS = {
    T(2008): 1000, T(2008, no_phase=True): 400,
    T(2008, "hearing loss"): 10, T(2008, "hearing loss", no_phase=True): 4,
    T(2008, "hearing loss", not_condition=HL): 8,
    T(2008, "pregnant"): 500, T(2008, "pregnant", no_phase=True): 150,
    T(2025): 2000, T(2025, no_phase=True): 1200,
    T(2025, "hearing loss"): 60, T(2025, "hearing loss", no_phase=True): 48,
    T(2025, "hearing loss", not_condition=HL): 48,
    T(2025, "pregnant"): 1000, T(2025, "pregnant", no_phase=True): 420,
}


def fake(u):
    q = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
    return {"totalCount": COUNTS[q["query.term"][0]]}


class TermTests(unittest.TestCase):
    def test_term(self):
        self.assertEqual(
            T(2008, "cognitive impairment"),
            'AREA[StudyType]INTERVENTIONAL AND AREA[StartDate]RANGE[2008-01-01,2008-12-31]'
            ' AND AREA[EligibilityCriteria]"cognitive impairment"')
        self.assertEqual(
            T(2025, "hearing loss", no_phase=True),
            'AREA[StudyType]INTERVENTIONAL AND AREA[StartDate]RANGE[2025-01-01,2025-12-31]'
            ' AND AREA[Phase]NA AND AREA[EligibilityCriteria]"hearing loss"')
        self.assertTrue(T(2025, "hearing loss", not_condition=HL).endswith(
            ' AND NOT AREA[ConditionSearch](hearing OR deafness OR tinnitus OR ear)'))

    def test_family_term(self):
        self.assertTrue(T(2008, "hearing (all wordings)").endswith(
            ' AND AREA[EligibilityCriteria]("hearing loss" OR "deaf" OR "deafness"'
            ' OR "hearing impairment" OR "hard of hearing" OR "hearing impaired")'))
        self.assertNotIn('"blind"', tc.criteria("visual (all wordings)"))

    def test_kind(self):
        self.assertEqual(tc.kind("hearing loss"), "disability")
        self.assertEqual(tc.kind("cognitive (all wordings)"), "family")
        self.assertEqual(tc.kind("pregnant"), "control")
        self.assertEqual(tc.kind("tattoo"), "rare control")
        self.assertEqual(tc.kind("informed consent"), "reference")
        self.assertTrue(all("," not in p for p in tc.ALL_PHRASES))

    def test_url_round_trip(self):
        u = tc.url(T(2008, "dementia"))
        self.assertTrue(u.startswith(tc.API + "?"))
        q = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
        self.assertEqual(q["query.term"], [T(2008, "dementia")])
        self.assertEqual(q["countTotal"], ["true"])


class RunTests(unittest.TestCase):
    def setUp(self):
        self.rows = tc.run([2008, 2025], ["hearing loss", "pregnant"], fetch=fake, pause=0)

    def test_rows(self):
        self.assertEqual(len(self.rows), 4)
        r = self.rows[0]
        self.assertEqual((r["year"], r["phrase"], r["kind"]), (2008, "hearing loss", "disability"))
        self.assertEqual(r["pct"], 1.0)
        self.assertEqual(r["no_phase_pct"], 1.0)
        self.assertEqual((r["other_trials"], r["other_matches"], r["other_pct"]), (600, 6, 1.0))
        self.assertEqual(r["not_own_condition_pct"], 0.8)
        p = self.rows[1]
        self.assertEqual(p["kind"], "control")
        self.assertNotIn("not_own_condition_pct", p)

    def test_ratios(self):
        out = {r["phrase"]: r for r in tc.ratios(self.rows, 2008, 2025)}
        h = out["hearing loss"]
        self.assertAlmostEqual(h["pct"], 3.0)
        self.assertAlmostEqual(h["no_phase_pct"], 4.0)
        self.assertAlmostEqual(h["other_pct"], 1.5)
        self.assertAlmostEqual(h["not_own_condition_pct"], 3.0)
        self.assertAlmostEqual(out["pregnant"]["pct"], 1.0)
        self.assertNotIn("not_own_condition_pct", out["pregnant"])

    def test_zero_denominator(self):
        a = {"m": 0, "n": 10}
        self.assertIsNone(tc.ratio(a, {"m": 1, "n": 10}, "m", "n"))
        self.assertIsNone(tc.pct(1, 0))

    def test_markdown(self):
        md = tc.markdown(self.rows, 2008, 2025)
        self.assertIn("| 2025 | hearing loss | disability | 3.0 | 4.0 | 1.5 | 2.4 |", md)
        self.assertIn("| pregnant | control | 1.0 |", md)
        self.assertNotIn("Families against controls", md)

    def test_main_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "trend.json")
            with mock.patch.object(tc, "fetch_json", fake), mock.patch("builtins.print"):
                rc = tc.main(["--years", "2008,2025", "--phrases", "hearing loss,pregnant",
                              "--json", out, "--pause", "0"])
            self.assertEqual(rc, 0)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(len(data["rows"]), 4)
            self.assertAlmostEqual(data["ratios"][0]["pct"], 3.0)
            self.assertEqual(len(data["family_tests"]), 3)


# 2008 -> 2025 ratios counted on 2026-10-15 (results/trend-check/TREND-CHECK.md, section 4).
NO_PHASE_FAMILIES = [1.74, 2.36, 3.07]
NO_PHASE_CONTROLS = [1.05, 0.62, 1.00, 1.14, 1.12, 2.76, 1.36, 0.99, 1.16, 1.81, 0.80]
OTHER_FAMILIES = [1.73, 1.76, 1.54]
OTHER_CONTROLS = [1.15, 1.96, 1.37, 1.07, 2.55, 2.63, 1.00, 0.91, 2.02, 0.79, 1.66]


class RankTests(unittest.TestCase):
    def test_midranks(self):
        self.assertEqual(tc.midranks([3, 1, 2, 2]), [4.0, 1.0, 2.5, 2.5])

    def test_rank_test_published_values(self):
        self.assertEqual(tc.rank_test(NO_PHASE_FAMILIES, NO_PHASE_CONTROLS), (36.0, 0.0192))
        self.assertEqual(tc.rank_test(OTHER_FAMILIES, OTHER_CONTROLS), (26.0, 0.3297))

    def test_rank_test_extremes(self):
        self.assertEqual(tc.rank_test([9], [1, 2, 3]), (4.0, 0.25))
        self.assertEqual(tc.rank_test([0], [1, 2, 3]), (1.0, 1.0))
        self.assertEqual(tc.rank_test([], [1]), (None, None))

    def test_family_test(self):
        rs = ([{"kind": "family", "no_phase_pct": v} for v in NO_PHASE_FAMILIES]
              + [{"kind": "rare control", "no_phase_pct": v} for v in NO_PHASE_CONTROLS[3:]]
              + [{"kind": "control", "no_phase_pct": v} for v in NO_PHASE_CONTROLS[:3]]
              + [{"kind": "disability", "no_phase_pct": 9.0},
                 {"kind": "reference", "no_phase_pct": 9.0}])
        t = tc.family_test(rs, "no_phase_pct")
        self.assertEqual((t["families"], t["controls"], t["control_max"]), (3, 11, 2.76))
        self.assertEqual((t["rank_sum"], t["p"]), (36.0, 0.0192))


if __name__ == "__main__":
    unittest.main()
