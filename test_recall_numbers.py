"""Offline tests: the quoted held-out recall and precision counts, recomputed from the labels. Apache-2.0.

Made by MV2 of Munim, Inc. with AI agents. test_results_v040.py recomputes each Wilson interval
from the printed fraction, and test_recall_sample.py scores a synthetic fixture; this re-scores
the real held-out half of the blind sample (R115-R225, labelled by AI agents after the 0.4.0
rules were fixed) with the current rules and checks the counts the README and SCORES-0.4.0.md
quote: exclusions 16/16 correct and 16 of 22 found, requirements 13/14 and 13 of 19, 19 and 13
of 78 random trials with a barrier in the inclusion criteria (13 only there), mobility 0 of 2
and 0 of 3. The 0.5.0 rule change (accommodation offers; sign-language, large-print and braille
exclusions) is not meant to move these counts, and this checks that it does not. No network.
"""

import os
import unittest

import recall_sample as rs

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = "results/v0.1.1/recall/sample.jsonl"
HELDOUT = "results/recall/labels-heldout.csv"
SCORES = "results/recall/SCORES-0.4.0.md"


def path(rel):
    return os.path.join(HERE, *rel.split("/"))


class HeldOutRecallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        labels = rs.read_labels(path(HELDOUT))
        cls.labels = labels
        cls.res = rs.score(rs.read_sample(path(SAMPLE)), labels)

    def test_labelled_trials(self):
        self.assertEqual(len(self.labels), 111)
        self.assertEqual(self.res["labelled"], {"random": 78, "broad": 33})

    def test_exclusion_rules(self):
        k = self.res["counts"]["any"]
        self.assertEqual((k["tp"], k["fp"], k["fn"]), (16, 0, 6))
        self.assertEqual(rs._rate(16, 16), "16/16 = 100% (81-100%)")
        self.assertEqual(rs._rate(16, 22), "16/22 = 73% (52-87%)")

    def test_requirement_rules(self):
        k = self.res["req_counts"]["any"]
        self.assertEqual((k["tp"], k["fp"], k["fn"]), (13, 1, 6))
        self.assertEqual(rs._rate(13, 14), "13/14 = 93% (69-99%)")
        self.assertEqual(rs._rate(13, 19), "13/19 = 68% (46-85%)")

    def test_inclusion_only_share(self):
        self.assertEqual((self.res["inclusion_any"], self.res["inclusion_only"]), (19, 13))
        self.assertEqual(rs._rate(19, 78), "19/78 = 24% (16-35%)")
        self.assertEqual(rs._rate(13, 78), "13/78 = 17% (10-26%)")

    def test_mobility_floor(self):
        k = self.res["counts"]["mobility"]
        self.assertEqual((k["tp"], k["tp"] + k["fn"]), (0, 2))
        k = self.res["req_counts"]["mobility"]
        self.assertEqual((k["tp"], k["tp"] + k["fn"]), (0, 3))

    def test_saved_report_rows(self):
        with open(path(SCORES), encoding="utf-8") as f:
            saved = f.read()
        lines = rs._table(self.res["counts"], "Labelled excluded")
        lines += rs._table(self.res["req_counts"], "Labelled required")
        for line in lines[2:]:
            if line.startswith("| any |"):
                self.assertIn(line, saved)


if __name__ == "__main__":
    unittest.main()
