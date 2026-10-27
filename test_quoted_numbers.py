"""Offline tests: quoted trend ratios and telephone base counts, recomputed from the saved counts. Apache-2.0.

Made by MV2 of Munim, Inc. with AI agents. test_prereg_v03.py runs the rank-sum test on ratios
typed in from PREREG-v0.3-RESULT.md; this checks that those typed-in ratios are the ones the saved
counts give. The telephone comparison quotes 7,620 telephone trials against 202,729 other no-phase
trials; this sums them from the saved per-stratum counts (the registry count includes the
telephone trials, as phone_matched.markdown prints). No network.
"""

import json
import os
import unittest

import prereg_v03 as pv

HERE = os.path.dirname(os.path.abspath(__file__))
PHONE = "results/phone-check/phone-matched-counts.json"

# As typed in test_prereg_v03.py (H1_FAMILIES, H1_CONTROLS).
H1_FAMILIES = [1.74, 2.36, 3.07]
H1_CONTROLS = [1.05, 0.62, 1.0, 1.12, 1.36, 0.99, 1.16, 1.22, 1.63]


def load(rel):
    with open(os.path.join(HERE, *rel.split("/")), encoding="utf-8") as f:
        return json.load(f)


class TrendRatioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = pv.trend_rows(load(pv.COUNTS))

    def test_family_ratios(self):
        fam = [r["no_phase"] for r in self.rows if r["kind"] == "family"]
        self.assertEqual(len(fam), 3)
        self.assertNotIn(None, fam)
        self.assertEqual(sorted(fam), H1_FAMILIES)

    def test_kept_controls(self):
        kept = [r["no_phase"] for r in self.rows if r["kind"] == "control" and r["no_phase_kept"]]
        self.assertEqual(sorted(kept), sorted(H1_CONTROLS))
        self.assertEqual(max(kept), 1.63)


class TelephoneBaseTests(unittest.TestCase):
    def test_base_counts(self):
        data = load(PHONE)
        self.assertEqual(len(data["strata"]), 6)
        phone = sum(data["trials"][s]["phone"] for s in data["strata"])
        registry = sum(data["trials"][s]["registry"] for s in data["strata"])
        self.assertEqual((phone, registry - phone), (7620, 202729))


if __name__ == "__main__":
    unittest.main()
