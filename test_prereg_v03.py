"""Offline tests for prereg_v03 (no network). Apache-2.0."""

import json
import os
import tempfile
import unittest
from unittest import mock

import prereg_v03 as pv
import trend_check as tc

HERE = os.path.dirname(os.path.abspath(__file__))
SMALL = {
    "first": 2008, "last": 2025,
    "trials": {"2008": {"all": 100, "no_phase": 40}, "2025": {"all": 200, "no_phase": 100}},
    "phrases": {
        "F": {"kind": "family", "2008": {"all": 10, "no_phase": 4}, "2025": {"all": 40, "no_phase": 20}},
        "C": {"kind": "control", "2008": {"all": 30, "no_phase": 10}, "2025": {"all": 60, "no_phase": 20}},
    },
    "va_no_phase": {
        "trials": {"va": 10, "registry": 100},
        "phrases": {"F": {"kind": "family", "va": 3, "registry": 10},
                    "C": {"kind": "control", "va": 0, "registry": 20},
                    "R": {"kind": "reference", "va": 1, "registry": 0}},
    },
}


class SmallTests(unittest.TestCase):
    def test_split(self):
        self.assertEqual(pv.split({"all": 9, "no_phase": 4}), {"all": 9, "no_phase": 4, "other": 5})

    def test_trend_rows(self):
        f, c = pv.trend_rows(SMALL)
        for s in pv.STRATA:
            self.assertAlmostEqual(f[s], 2.0)
            self.assertTrue(f[s + "_kept"])
        self.assertAlmostEqual(c["all"], 1.0)
        self.assertAlmostEqual(c["no_phase"], 0.8)
        self.assertAlmostEqual(c["other"], 1.2)
        self.assertEqual((c["no_phase_first"], c["other_first"]), (10, 20))
        self.assertEqual((c["all_kept"], c["no_phase_kept"], c["other_kept"]), (True, False, True))

    def test_floor(self):
        rows = pv.trend_rows(SMALL)
        t = pv.test(rows, "no_phase")
        self.assertEqual((t["controls"], t["left_out"], t["p"]), (0, ["C"], None))
        t = pv.test(rows, "no_phase", floor=False)
        self.assertEqual((t["controls"], t["left_out"], t["p"]), (1, [], 0.5))

    def test_va_rows(self):
        f, c, r = pv.va_rows(SMALL)
        self.assertAlmostEqual(f["ratio"], 3.0)
        self.assertEqual(c["ratio"], 0.0)
        self.assertIsNone(r["ratio"])

    def test_verdicts_without_controls(self):
        res = {"H1": {"p": None}, "H2": {"p": None}}
        self.assertEqual(pv.verdicts(res), {"H1": False, "H2": False})


# The no-phase 2025/2008 ratios of 2026-10-15 that pass the 20-match rule (PREREG-v0.3-RESULT.md).
H1_FAMILIES = [1.74, 2.36, 3.07]
H1_CONTROLS = [1.05, 0.62, 1.0, 1.12, 1.36, 0.99, 1.16, 1.22, 1.63]


class PublishedTests(unittest.TestCase):
    def test_h1_rank_test(self):
        self.assertEqual(tc.rank_test(H1_FAMILIES, H1_CONTROLS), (33.0, 0.0045))

    def test_counts_file(self):
        path = os.path.join(HERE, pv.COUNTS)
        if not os.path.exists(path):
            self.skipTest("counts file not present")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        res = pv.results(data)
        h1, h2 = res["H1"], res["H2"]
        self.assertEqual((h1["families"], h1["controls"], h1["control_max"]), (3, 9, 1.63))
        self.assertEqual((h1["rank_sum"], h1["p"]), (33.0, 0.0045))
        self.assertEqual(len(h1["left_out"]), 14)
        self.assertIn("tattoo", h1["left_out"])
        self.assertEqual((h2["controls"], h2["left_out"], h2["rank_sum"]), (22, ["hemorrhoids"], 41.0))
        self.assertAlmostEqual(h2["p"], 0.453, places=4)
        self.assertEqual((res["all"]["controls"], res["all"]["rank_sum"]), (23, 70.5))
        self.assertAlmostEqual(res["all"]["p"], 0.005, places=4)
        self.assertEqual(res["no_phase_every_control"]["controls"], 23)
        self.assertAlmostEqual(res["no_phase_every_control"]["p"], 0.0204, places=4)
        self.assertAlmostEqual(res["other_every_control"]["p"], 0.4104, places=4)
        va = res["va_no_phase"]
        self.assertEqual((va["families"], va["controls"], va["control_max"], va["rank_sum"]),
                         (3, 23, 2.7, 73.0))
        self.assertAlmostEqual(va["p"], 0.0015, places=4)
        self.assertEqual(pv.verdicts(res), {"H1": True, "H2": True})

    def test_main_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            counts, out = os.path.join(d, "counts.json"), os.path.join(d, "out.json")
            with open(counts, "w", encoding="utf-8") as f:
                json.dump(SMALL, f)
            with mock.patch("builtins.print"):
                rc = pv.main(["--counts", counts, "--json", out])
            self.assertEqual(rc, 0)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(len(data["trend"]), 2)
            self.assertEqual(data["tests"]["H1"]["left_out"], ["C"])

    def test_markdown(self):
        md = pv.markdown(SMALL)
        self.assertIn("| C | control | 1.0 | 0.8* | 1.2 |", md)
        self.assertIn("| VA against registry, no-phase | 1 | 1 |", md)


if __name__ == "__main__":
    unittest.main()
