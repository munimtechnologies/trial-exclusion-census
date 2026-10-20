"""Offline tests: the README describes the consent-capacity requirement rule as the code applies it
(no network). Apache-2.0.

The 0.4.0 share of trials that require the capacity to consent (12.69%) counts "able to provide
informed consent" only when the same item names no representative, but counts "able to understand
the study" even when it does, and never looks at other items. The README must not call it a count
of trials with no representative named, except where its Changes section quotes the old wording.
"""

import os
import re
import unittest

import exclusion_census as ec

HERE = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HERE, "README.md")
STOCK = "Ability to understand and the willingness to sign a written informed consent document"
OLD = "with no representative named"


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


class RuleTests(unittest.TestCase):
    def test_provide_consent_needs_no_representative_in_item(self):
        self.assertIn("consent_capacity", ec.requirements("Able to provide informed consent"))
        self.assertNotIn("consent_capacity", ec.requirements(
            "Able to provide informed consent, or a legally authorized representative able to do so"))

    def test_understand_counts_with_representative_in_item(self):
        self.assertIn("consent_capacity", ec.requirements(
            "Able to understand the study, or has a legally authorized representative"))

    def test_stock_line_counts(self):
        self.assertIn("consent_capacity", ec.requirements(STOCK))

    def test_other_items_are_not_read(self):
        crit = ("Inclusion Criteria:\n\n* Age 18 or older\n* " + STOCK + "\n"
                "* A legally authorized representative may sign consent on the participant's behalf\n\n"
                "Exclusion Criteria:\n\n* Pregnancy\n")
        reqs = [ec.requirements(item) for item in ec.split_items(ec.inclusion_section(crit))]
        self.assertIn({"consent_capacity"}, reqs)


class ReadmeTests(unittest.TestCase):
    def test_summary_says_what_is_counted(self):
        text, _ = readme_parts()
        self.assertNotIn(OLD, text)
        self.assertIn("most often the ability to consent or to understand the study (12.69%), counted "
                      "whether or not another item lets a representative consent.", text)

    def test_limits_say_understand_is_counted(self):
        text, _ = readme_parts()
        self.assertIn("is counted even when the same item names a representative", text)
        self.assertIn("trials that ask for the ability, not trials that offer no way in", text)

    def test_changes_quote_the_old_wording_once(self):
        _, changes = readme_parts()
        self.assertEqual(changes.count(OLD), 1)
        self.assertIn("After 0.5.0 (on main): wording only.", changes)
        self.assertIn("No number changes, and the census rules are unchanged.", changes)


if __name__ == "__main__":
    unittest.main()
