"""Offline wording tests for the README and ACCOMMODATION.md (no network). Apache-2.0.

Readings and labels in this repository were made by AI agents working for MV2, and no person has
checked them yet. These pages must say so and must not describe that work as done "by hand" or
"by eye". "By hand" may still describe the hand-coded studies of others, and instructions to
people who check the rules themselves.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HERE, "README.md")
ACCOMMODATION = os.path.join(HERE, "results", "recall", "ACCOMMODATION.md")

CLAIMS = re.compile(r"hand[- ]check|hand-label|(?<!can be )checked\s+by\s+hand|read\s+by\s+hand|"
                    r"traced\s+by\s+hand|adding\s+(?:\S+\s+){0,4}by\s+hand|by\s+eye", re.I)
# Every "by hand" left on the README, in the sentence it belongs to.
ALLOWED = ("hand-coded study", "coded by hand", "Earlier studies coded samples by hand",
           "precision can be checked by hand", "new rules can be checked by hand",
           "label recall/labels.csv by hand")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class WordingTests(unittest.TestCase):
    def test_no_hand_or_eye_claims(self):
        for path in (README, ACCOMMODATION):
            text = re.sub(r"\s+", " ", read(path))
            self.assertEqual(CLAIMS.findall(text), [], os.path.basename(path))

    def test_every_by_hand_is_allowed(self):
        text = re.sub(r"\s+", " ", read(README))
        for match in re.finditer(r"by hand|hand-coded", text):
            window = text[max(0, match.start() - 60):match.end() + 10]
            self.assertTrue(any(a in window for a in ALLOWED), window)

    def test_who_did_the_reading_is_named(self):
        readme = re.sub(r"\s+", " ", read(README))
        for s in ("720 random flagged exclusion items were read by AI agents working for MV2 (not "
                  "yet checked by a person)",
                  "Every reading and label so far was done by AI agents working for MV2",
                  "All 225 were labelled by AI agents working for MV2, one reader per trial."):
            self.assertIn(s, readme)
        accommodation = re.sub(r"\s+", " ", read(ACCOMMODATION))
        self.assertIn("Read on 2026-10-15 by an AI agent working for MV2 of Munim, Inc., one reader",
                      accommodation)
        self.assertIn("No person has checked this reading yet.", accommodation)

    def test_numbers_unchanged(self):
        readme = re.sub(r"\s+", " ", read(README))
        for s in ("found only **5** that offer an accommodation (31%; Wilson 95% interval 14% to 56%)",
                  "60 per category, 360 of them in the six disability categories",
                  "(263 instead of 255)", "the first 114 trials, whose misses shaped 0.4.0"):
            self.assertIn(s, readme)
        accommodation = read(ACCOMMODATION)
        self.assertEqual(len(re.findall(r"^\| R\d{3} \|", accommodation, re.M)), 16)
        self.assertEqual(len(re.findall(r"^\| R\d{3} \|.*\| yes \|\s*$", accommodation, re.M)), 5)
        self.assertIn("That is 9 matches in 225, all offers, against 5 of 16 before",
                      re.sub(r"\s+", " ", accommodation))


if __name__ == "__main__":
    unittest.main()
