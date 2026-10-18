"""Offline tests for peryear_v03 (no network). Apache-2.0."""

import json
import math
import os
import tempfile
import unittest
from unittest import mock

import peryear_v03 as py

HERE = os.path.dirname(os.path.abspath(__file__))
# F doubles its share every year; C keeps the same share.
SMALL = {
    "stratum": "no_phase", "years": [2008, 2009, 2010], "trials": [100, 200, 400],
    "phrases": {"F": {"kind": "family", "counts": [1, 4, 16]},
                "C": {"kind": "control", "counts": [10, 20, 40]}},
}


class SmallTests(unittest.TestCase):
    def test_slope(self):
        self.assertAlmostEqual(py.slope([0, 1, 2], [1, 2, 4], [10, 10, 10]), math.log(2))
        self.assertAlmostEqual(py.slope([0, 1, 2], [3, 6, 12], [30, 60, 120]), 0.0)
        self.assertIsNone(py.slope([0, 1], [0, 2], [10, 10]))

    def test_rows_and_test(self):
        f, c = py.rows(SMALL)
        self.assertEqual((f["slope"], f["per_year_pct"]), (0.6931, 100.0))
        self.assertEqual((c["slope"], c["per_year_pct"]), (0.0, 0.0))
        self.assertEqual(f["shares_pct"], [1.0, 2.0, 4.0])
        t = py.test([f, c])
        self.assertEqual((t["families"], t["controls"], t["rank_sum"], t["p"]), (1, 1, 2.0, 0.5))

    def test_markdown(self):
        md = py.markdown(SMALL)
        self.assertIn("| F | family | 0.6931 | 100.0% | 1.0% | 4.0% |", md)
        self.assertIn("| Families against controls, slopes | 1 | 1 | 0.0 | 2.0 | 0.5 |", md)
        self.assertLess(md.index("| F |"), md.index("| C |"))

    def test_main_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            counts, out = os.path.join(d, "counts.json"), os.path.join(d, "out.json")
            with open(counts, "w", encoding="utf-8") as f:
                json.dump(SMALL, f)
            with mock.patch("builtins.print"):
                self.assertEqual(py.main(["--counts", counts, "--json", out]), 0)
            with open(out, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["test"]["p"], 0.5)


class PublishedTests(unittest.TestCase):
    def test_counts_file(self):
        path = os.path.join(HERE, py.COUNTS)
        if not os.path.exists(path):
            self.skipTest("counts file not present")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data["years"]), 18)
        self.assertEqual(len(data["trials"]), 18)
        for c in data["phrases"].values():
            self.assertEqual(len(c["counts"]), 18)
        rs = {r["phrase"]: r for r in py.rows(data)}
        # First worked out outside the code by AI agents working for MV2 on 2026-10-15
        # (PREREG-v0.3-RESULT.md section "By year"); no person has checked them yet.
        for phrase, b in [("visual (all wordings)", 0.0703), ("hearing (all wordings)", 0.0604),
                          ("cognitive (all wordings)", 0.0319), ("eczema", 0.0237),
                          ("hepatitis", -0.0211), ("pregnant", -0.0001)]:
            self.assertAlmostEqual(rs[phrase]["slope"], b, delta=0.0005)
        t = py.test(list(rs.values()))
        self.assertEqual((t["families"], t["controls"], t["rank_sum"], t["p"]), (3, 9, 33.0, 0.0045))


if __name__ == "__main__":
    unittest.main()
