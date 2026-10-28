"""Offline tests: the accommodation flag on the 225-trial recall sample, run as code. Apache-2.0.

Made by MV2 of Munim, Inc. with AI agents. results/recall/ACCOMMODATION.md lists the 16 sample
trials the 0.4.0 word list matched, of which an AI agent working for MV2 read 5 as real offers
(5/16 = 31%, 14-56%), and says the current rules match 9: the same 5 plus R067, R068, R170 and
R177, still missing R144. test_wording.py checks the table's row counts; this runs the current
rules' analyze on results/v0.1.1/recall/sample.jsonl and checks the flagged trials against the
note's table and its named labels. The readings are one AI agent's, and no person has checked
them yet. No network.
"""

import json
import os
import re
import unittest

import exclusion_census as ec
import recall_sample as rs

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = "results/v0.1.1/recall/sample.jsonl"
NOTE = "results/recall/ACCOMMODATION.md"
ROW = re.compile(r"^\| (R\d{3}) \| (NCT\d{8}) \| .* \| (yes|no[^|]*) \|\s*$")
OFFERS = {"R001", "R103", "R119", "R191", "R200"}
ADDED = {"R067": "NCT06237491", "R068": "NCT02369068", "R170": "NCT06619496", "R177": "NCT06379672"}


def path(rel):
    return os.path.join(HERE, *rel.split("/"))


def table(text):
    """{label: (NCT id, read as an offer)} from the note's table of the trials 0.4.0 matched."""
    rows = {}
    for m in map(ROW.match, text.splitlines()):
        if m:
            rows[m.group(1)] = (m.group(2), m.group(3) == "yes")
    return rows


class AccommodationFlagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(path(SAMPLE), encoding="utf-8") as f:
            cls.sample = [json.loads(line) for line in f if line.strip()]
        cls.flagged = {r["label"]: r.get("nct") for r in cls.sample if ec.analyze(r).get("accommodation")}
        with open(path(NOTE), encoding="utf-8") as f:
            cls.note = f.read()
        cls.table = table(cls.note)

    def test_note_table(self):
        self.assertEqual(len(self.sample), 225)
        self.assertEqual(len(self.table), 16)
        self.assertEqual({k for k, (_, yes) in self.table.items() if yes}, OFFERS)
        self.assertEqual(rs._rate(5, 16), "5/16 = 31% (14-56%)")

    def test_table_ids_match_sample(self):
        by_label = {r["label"]: r.get("nct") for r in self.sample}
        for label, (nct, _) in self.table.items():
            self.assertEqual(by_label[label], nct, label)

    def test_current_rules_flag_nine(self):
        self.assertEqual(len(self.flagged), 9)
        self.assertEqual(set(self.flagged), OFFERS | set(ADDED))
        for label, nct in ADDED.items():
            self.assertEqual(self.flagged[label], nct, label)

    def test_dropped_and_missed(self):
        others = {k for k, (_, yes) in self.table.items() if not yes}
        self.assertEqual(len(others), 11)
        self.assertEqual(others & set(self.flagged), set())
        self.assertNotIn("R144", self.flagged)

    def test_note_sentences(self):
        text = " ".join(self.note.split())  # the note wraps its lines
        self.assertIn("The 0.4.0 word list matches 16 of the 225 trials.", text)
        self.assertIn("Across the 225 it matches 4 more trials", text)
        for label in ADDED:
            self.assertIn(label, text.split("## What 0.5.0 changes", 1)[1])
        self.assertIn("It still misses R144", text)
        self.assertIn("run as code on 2026-10-28", text)


if __name__ == "__main__":
    unittest.main()
