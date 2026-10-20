"""Offline tests for label_tally (no network). Apache-2.0.

The published counts were first tallied outside the code by AI agents working for MV2 (runs 37
and 120, a regular expression over the six category columns); these tests hold the script to them.
"""

import contextlib
import io
import json
import os
import unittest

import label_tally as lt

HERE = os.path.dirname(os.path.abspath(__file__))
HELDOUT = os.path.join(HERE, "results", "recall", "labels-heldout.csv")
DEV = os.path.join(HERE, "results", "recall", "labels-dev.csv")


class TallyTests(unittest.TestCase):
    def test_made_up_rows(self):
        labels = {
            "R1": {"label": "R1", "done": "1", "consent_capacity": "i"},
            "R2": {"label": "R2", "done": "1", "consent_capacity": "i", "visual": "x"},
            "R3": {"label": "R3", "done": "1", "mobility": "i", "cognitive": " I "},
            "R4": {"label": "R4", "done": "1", "hearing": "xi"},
            "R5": {"label": "R5", "done": "1"},
        }
        res = lt.tally(labels)
        self.assertEqual(res["labelled"], 5)
        self.assertEqual(res["inclusion_only"], 2)
        self.assertEqual(res["inclusion_only_by_category"],
                         {"cognitive": 1, "consent_capacity": 1, "visual": 0, "hearing": 0,
                          "communication": 0, "mobility": 1})

    def test_published_heldout_counts(self):
        res = lt.tally(lt.rs.read_labels(HELDOUT))
        self.assertEqual(res["labelled"], 111)
        self.assertEqual(res["inclusion_only"], 28)
        self.assertEqual(res["inclusion_only_by_category"]["consent_capacity"], 21)

    def test_published_dev_and_all_counts(self):
        dev = lt.rs.read_labels(DEV)
        res = lt.tally(dev)
        self.assertEqual((res["labelled"], res["inclusion_only"]), (114, 28))
        self.assertEqual(res["inclusion_only_by_category"]["consent_capacity"], 19)
        both = dict(dev, **lt.rs.read_labels(HELDOUT))
        res = lt.tally(both)
        self.assertEqual((res["labelled"], res["inclusion_only"]), (225, 56))
        self.assertEqual(res["inclusion_only_by_category"]["consent_capacity"], 40)

    def test_main_prints_json(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(lt.main([DEV, HELDOUT]), 0)
        out = json.loads(buf.getvalue())
        self.assertEqual(out["version"], "0.1.0")
        self.assertEqual(out["files"][HELDOUT]["inclusion_only"], 28)
        self.assertEqual(out["all"]["labelled"], 225)

    def test_wording(self):
        with open(os.path.join(HERE, "label_tally.py"), encoding="utf-8") as f:
            text = f.read()
        self.assertNotIn("by hand", text)
        self.assertIn("AI agents working for MV2", text)
        self.assertIn("Apache-2.0", text)


if __name__ == "__main__":
    unittest.main()
