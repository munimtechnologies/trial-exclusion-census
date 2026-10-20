"""Offline wording test for score_recall.sh, the recall-scoring script (no network). Apache-2.0.

The sixth pass after test_wording.py: the recall labels were made by AI agents working for MV2,
one reader per trial, and no person has checked them yet. score_recall.sh used to call them
"labelled by hand"; only its header comment changed, and its commands must stay as they were.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCORE_RECALL = os.path.join(HERE, "score_recall.sh")

CLAIMS = re.compile(r"by\s+hand|hand[- ]check|hand-label|by\s+eye", re.I)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class ScoreRecallWordingTests(unittest.TestCase):
    def setUp(self):
        self.text = read(SCORE_RECALL)
        self.comments = " ".join(l[1:].strip() for l in self.text.splitlines()[1:] if l.startswith("#"))

    def test_no_hand_or_eye_claims(self):
        self.assertEqual(CLAIMS.findall(re.sub(r"\s+", " ", self.text)), [])

    def test_who_labelled_is_named(self):
        self.assertIn("labelled blind to the flags by AI agents working for MV2, one reader per trial; "
                      "no person has checked the labels yet.", self.comments)
        self.assertIn("only the held-out scores measure v0.4.0 fairly.", self.comments)

    def test_commands_unchanged(self):
        commands = [l for l in self.text.splitlines() if l and not l.startswith("#")]
        self.assertEqual(len(commands), 18)
        self.assertEqual(commands[0], "set -u")
        self.assertIn("tail -n +2 results/recall/labels-heldout.csv >> labels-all.csv", commands)
        for labels, name in (("results/recall/labels-dev.csv", "dev"),
                             ("results/recall/labels-heldout.csv", "heldout"),
                             ("labels-all.csv", "all")):
            self.assertIn("  python $d/recall_sample.py score --sample sample.jsonl --labels %s "
                          "--out /out/$v-%s.md > /dev/null" % (labels, name), commands)
        self.assertEqual(commands[-1], "ls -la /out")


if __name__ == "__main__":
    unittest.main()
