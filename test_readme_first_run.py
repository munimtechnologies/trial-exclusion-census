"""Offline tests for the README's first-run numbers (v0.1.1 rules, pre-registered; no network). Apache-2.0.

Made by MV2 of Munim, Inc. with AI agents. The opening section quotes the first census run, whose
rules were published before any data; each number it quotes must be the one in
results/v0.1.1/summary.json, rounded as printed.
"""

import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HERE, "README.md")
RUN = os.path.join(HERE, "results", "v0.1.1")


def first_run_section():
    with open(README, encoding="utf-8") as f:
        text = f.read()
    start = text.index("## First results (v0.1.1 rules, pre-registered)")
    end = text.find("\n## ", start + 1)
    return re.sub(r"\s+", " ", text[start:end if end > 0 else len(text)])


class FirstRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(RUN, "summary.json"), encoding="utf-8") as f:
            cls.s = json.load(f)
        cls.text = first_run_section()

    def test_run(self):
        s = self.s
        self.assertEqual((s["records"], s["with_criteria"], s["total"]["trials"]),
                         (463180, 463140, 450052))
        self.assertIn("**{:,} interventional studies**, of which **{:,}** have an exclusion".format(
            s["records"], s["total"]["trials"]), self.text)

    def test_headline_share(self):
        self.assertIn("- **%.1f%%** of trials with an exclusion section" % self.s["total"]["any_core_pct"],
                      self.text)
        self.assertEqual("%.1f" % self.s["total"]["any_core_pct"], "20.1")

    def test_phase_shares(self):
        p = {k: self.s["by_phase"][k]["any_core_pct"] for k in ("NA", "PHASE1", "PHASE2", "PHASE3")}
        self.assertIn("trials with no phase (devices, behavioural studies, procedures) %.1f%%; phase 1 "
                      "%.1f%%, phase 2 %.1f%% and phase 3 %.1f%%."
                      % (p["NA"], p["PHASE1"], p["PHASE2"], p["PHASE3"]), self.text)
        self.assertEqual(["%.1f" % p[k] for k in ("NA", "PHASE1", "PHASE2", "PHASE3")],
                         ["25.7", "10.7", "14.1", "13.5"])


if __name__ == "__main__":
    unittest.main()
