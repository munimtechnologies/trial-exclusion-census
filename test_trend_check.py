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


if __name__ == "__main__":
    unittest.main()
