"""Offline test: the README's lower bound on how much of the "barrier only in the inclusion
criteria" share is a consent-or-understanding item follows from the published 0.4.0 totals
(no network). Apache-2.0.

Trials that require the capacity to consent are a subset of the trials with any inclusion
requirement, so the trials with a requirement but no consent one are at most any_required_pct
minus consent_capacity_required_pct. The "requirement only" trials (a requirement and no core
exclusion) without a consent item are a subset of those, so the requirement-only trials WITH one
are at least required_only_pct minus that difference. Every share is a percentage of the same
trials (those with an exclusion section), rounded to two decimals, so the check allows 0.005 on
each. The exact split is not tallied anywhere; this is only a bound.

Made by MV2 of Munim, Inc. with AI agents.
"""

import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SUMMARY = os.path.join(HERE, "results", "v0.4.0", "summary.json")
README = os.path.join(HERE, "README.md")
HALF = 0.005  # each published share is rounded to two decimals


def totals():
    with open(SUMMARY, encoding="utf-8") as f:
        return json.load(f)["total"]


def flat(text):
    return re.sub(r"\s+", " ", text)


def readme_parts():
    """The README before its "## Changes" heading, and the Changes section itself."""
    with open(README, encoding="utf-8") as f:
        text = f.read()
    head, sep, rest = text.partition("\n## Changes\n")
    if not sep:
        raise AssertionError("README has no '## Changes' section")
    changes = re.split(r"\n## ", rest, maxsplit=1)[0]
    return flat(head), flat(changes)


def sentence(t):
    slack = round(t["any_required_pct"] - t["consent_capacity_required_pct"], 2)
    return ("At least two-thirds of that %.2f%% have an item asking for the ability to consent or to "
            "understand the study: %.2f%% have any inclusion requirement and %.2f%% a consent one, so "
            "at most %.2f points of the %.2f can lack such an item"
            % (t["required_only_pct"], t["any_required_pct"], t["consent_capacity_required_pct"],
               slack, t["required_only_pct"]))


class BoundTests(unittest.TestCase):
    def test_shares_are_of_the_same_trials(self):
        t = totals()
        self.assertEqual(t["trials"], 450201)
        self.assertLessEqual(t["consent_capacity_required_pct"], t["any_required_pct"])
        self.assertLessEqual(t["required_only_pct"], t["any_required_pct"])
        # any_barrier = requirement or core exclusion; required_only = requirement and no core.
        self.assertAlmostEqual(t["any_barrier_pct"], t["any_core_pct"] + t["required_only_pct"],
                               delta=0.02)

    def test_at_least_two_thirds_even_with_rounding(self):
        t = totals()
        no_consent_max = ((t["any_required_pct"] + HALF)
                          - (t["consent_capacity_required_pct"] - HALF))
        with_consent_min = (t["required_only_pct"] - HALF) - no_consent_max
        self.assertGreaterEqual(with_consent_min / (t["required_only_pct"] + HALF), 2 / 3)

    def test_point_values_quoted_in_the_readme(self):
        t = totals()
        slack = t["any_required_pct"] - t["consent_capacity_required_pct"]
        self.assertAlmostEqual(slack, 3.67, places=2)
        self.assertAlmostEqual(t["required_only_pct"] - slack, 7.71, places=2)
        self.assertEqual((t["required_only_pct"], t["any_required_pct"],
                          t["consent_capacity_required_pct"]), (11.38, 16.36, 12.69))


class ReadmeTests(unittest.TestCase):
    def test_summary_sentence_uses_the_published_totals(self):
        head, _ = readme_parts()
        s = sentence(totals())
        self.assertEqual(head.count(s), 1)
        self.assertIn("where an exclusion-only count cannot see it. " + s, head)
        self.assertIn("(`test_readme_bound.py` recomputes this from `results/v0.4.0/summary.json`)",
                      head)

    def test_changes_entry_once(self):
        _, changes = readme_parts()
        self.assertEqual(changes.count("`test_readme_bound.py` recomputes the bound"), 1)
        self.assertIn("The exact split is not tallied", changes)
        self.assertIn("at least two-thirds of the 11.38%", changes)


if __name__ == "__main__":
    unittest.main()
