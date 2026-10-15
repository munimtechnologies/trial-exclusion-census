"""Offline tests for diff_rules (no network). Apache-2.0."""

import csv
import os
import tempfile
import types
import unittest

import diff_rules as dr
import exclusion_census as ec

# An "old" rule set that flags nothing, so every flag of the current rules counts as added.
NOTHING = types.SimpleNamespace(classify=lambda item: set(), requirements=lambda item: set(),
                                __version__="none")

RECORDS = [
    {"nct": "A", "criteria": "Inclusion Criteria:\n* Normal hearing\nExclusion Criteria:\n* Cochlear implant\n* Pregnancy"},
    {"nct": "B", "criteria": "Exclusion Criteria:\n* Pregnancy"},
    {"nct": "C", "criteria": "Adults with asthma."},
]


class DiffTests(unittest.TestCase):
    def test_added(self):
        res = dr.diff(RECORDS, NOTHING, ec)
        self.assertEqual(res["trials"], 2)
        self.assertEqual(res["any_core_old"], 0)
        self.assertEqual(res["any_core_new"], 1)
        self.assertEqual(res["items"][("exclusion", "hearing", "added")], 1)
        self.assertEqual(res["trial_counts"][("inclusion", "hearing", "added")], 1)
        self.assertEqual(res["samples"][("exclusion", "hearing", "added")], [("A", "Cochlear implant")])

    def test_same_rules_no_changes(self):
        res = dr.diff(RECORDS, ec, ec)
        self.assertEqual(sum(res["items"].values()), 0)
        self.assertEqual(res["any_core_old"], res["any_core_new"])

    def test_write(self):
        res = dr.diff(RECORDS, NOTHING, ec)
        with tempfile.TemporaryDirectory() as d:
            summary = dr.write(res, d, NOTHING, ec)
            self.assertEqual(summary["any_core_new_pct"], 50.0)
            with open(os.path.join(d, "changed_items.csv"), newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertIn({"section": "exclusion", "category": "hearing", "direction": "added",
                           "nct": "A", "item": "Cochlear implant", "correct": ""}, rows)
            self.assertTrue(os.path.exists(os.path.join(d, "changes.csv")))


if __name__ == "__main__":
    unittest.main()
