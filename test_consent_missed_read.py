"""Tests for CONSENT-MISSED-READ.md (no network). Apache-2.0.

Recomputes the note's numbers from consent-missed.json and the reading by eye, and checks each
label against the words of its snippets.
"""

import collections
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "results", "consent-phrase")
# Words each label needs in at least one snippet of its trial.
NEEDS = {
    # Two snippets are cut before the word itself and keep only "abstinence), ... partners".
    "contraception": re.compile(r"contracept|birth control|abstinence", re.I),
    "caregiver_self_consent": re.compile(r"caregiver|care-partner", re.I),
    "family_meeting": re.compile(r"family member.*meet", re.I),
}
ROWS = [("Names a partner in a contraception item", "contraception"),
        ("Enrols a caregiver or care-partner", "caregiver_self_consent"),
        ("Has a family member meet the team", "family_meeting"),
        ("Lets another person consent for the participant", "consent_on_behalf")]


def load(name):
    with open(os.path.join(DIR, name), encoding="utf-8") as f:
        return f.read() if name.endswith(".md") else json.load(f)


class ConsentMissedReadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Not "run": that would hide TestCase.run.
        cls.found = load("consent-missed.json")
        cls.read = load("consent-missed-read.json")
        cls.md = load("CONSENT-MISSED-READ.md")
        cls.snips = {r["nct_id"]: r["snippets"] for r in cls.found["reading_sample"]}

    def test_every_trial_read_once(self):
        ids = [r["nct_id"] for r in self.read["rows"]]
        self.assertEqual(ids, [r["nct_id"] for r in self.found["reading_sample"]])
        self.assertEqual(len(ids), self.found["other_path"])
        self.assertEqual(sum(r["adult_only"] is True for r in self.found["reading_sample"]),
                         self.found["other_path_adult_only"])

    def test_labels_match_their_snippets(self):
        for r in self.read["rows"]:
            self.assertIn(r["category"], self.read["categories"])
            text = " ".join(self.snips[r["nct_id"]])
            self.assertTrue(NEEDS[r["category"]].search(text), r["nct_id"])
            if r["category"] == "caregiver_self_consent":
                self.assertRegex(text, r"(?i)sign")

    def test_note_quotes_the_counts(self):
        n = collections.Counter(r["category"] for r in self.read["rows"])
        for start, key in ROWS:
            self.assertRegex(self.md, re.escape(start) + r"[^|]*\| %d \|" % n[key])
        self.assertEqual(n["consent_on_behalf"], 0)
        self.assertIn("among the {:,} trials with the exact stock line".format(self.found["exact_no_path"]),
                      self.md)
        self.assertIn("%d name a caregiver" % self.found["other_path"], self.md)
        self.assertIn("(%d of them adult-only)" % self.found["other_path_adult_only"], self.md)
        self.assertIn("All %d were read by eye" % self.found["other_path"], self.md)
        self.assertIn("none of the %d is a missed path" % self.found["other_path"], self.md)


if __name__ == "__main__":
    unittest.main()
