"""Offline tests for CONSENT-NEAR-VARIANT.md (no network). Apache-2.0.

Recomputes every number the note quotes from consent-phrase-trials.csv, consent-phrase.json, the
exact-line reading in consent-read.json and the near-variant reading in near-variant-read.json,
and checks that each mark follows the rules written in the file.
"""

import csv
import json
import math
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "results", "consent-phrase")
MARKS = ["adult_permission", "minor_only", "unclear", "not_a_permission", "physical_only"]


def load(name):
    with open(os.path.join(DIR, name), encoding="utf-8", newline="") as f:
        if name.endswith(".json"):
            return json.load(f)
        if name.endswith(".csv"):
            return list(csv.DictReader(f))
        return f.read()


def wilson(k, n, z=1.96):
    p = k / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - half) / (1 + z * z / n), (centre + half) / (1 + z * z / n)


def num(x):
    return "{:,}".format(x)


class NearVariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = load("consent-phrase.json")["summary"]
        cls.rows = load("consent-phrase-trials.csv")
        cls.read = load("near-variant-read.json")
        cls.exact_read = load("consent-read.json")
        cls.md = load("CONSENT-NEAR-VARIANT.md").replace("\r\n", "\n")
        washu = re.compile(cls.read["washu_pattern"], re.I)
        cls.loose = [r for r in cls.rows if r["stock_exact"] == "False" and r["stock_loose"] == "True"]
        cls.named = [r for r in cls.loose if r["adult_path"] == "True"]
        cls.groups = {"washu": [], "nci_lar": [], "other": []}
        for r in cls.named:
            if washu.search(r["snippets"]):
                cls.groups["washu"].append(r)
            elif r["nci_lar_may_sign"] == "True":
                cls.groups["nci_lar"].append(r)
            else:
                cls.groups["other"].append(r)
        cls.washu_any = [r for r in cls.rows if washu.search(r["snippets"])]

    def count(self, mark):
        return sum(1 for m in self.read["marks"] if m["mark"] == mark)

    def adult(self, rows):
        return sum(r["adult_only"] == "True" for r in rows)

    def permissions(self):
        return (self.adult(self.groups["washu"]) + self.adult(self.groups["nci_lar"])
                + self.count("adult_permission"))

    def test_reading_is_the_other_group(self):
        marks = self.read["marks"]
        self.assertEqual([m["nct_id"] for m in marks], [r["nct_id"] for r in self.groups["other"]])
        self.assertEqual(sorted(self.read["rules"]), sorted(MARKS))
        self.assertEqual(self.read["rules"], self.exact_read["rules"])
        for m in marks:
            self.assertIn(m["mark"], MARKS, m["nct_id"])
            self.assertTrue(m["note"], m["nct_id"])

    def test_marks_follow_the_rules(self):
        by_id = {r["nct_id"]: r for r in self.groups["other"]}
        for m in self.read["marks"]:
            adult = by_id[m["nct_id"]]["adult_only"] == "True"
            if m["mark"] == "adult_permission":
                self.assertTrue(adult, m["nct_id"])
            if m["mark"] in ("minor_only", "unclear"):
                self.assertFalse(adult, m["nct_id"])

    def test_groups(self):
        self.assertEqual(len(self.loose), self.s["stock_loose_only"])
        self.assertIn("%d of %s (%.1f%%) name a representative, guardian or surrogate" % (
            len(self.named), num(len(self.loose)), 100.0 * len(self.named) / len(self.loose)), self.md)
        self.assertEqual(sum(len(g) for g in self.groups.values()), len(self.named))
        perms = {"washu": self.adult(self.groups["washu"]), "nci_lar": self.adult(self.groups["nci_lar"]),
                 "other": self.count("adult_permission")}
        for g, rows in self.groups.items():
            self.assertIn("| %s | %d | %d |" % (g, len(rows), perms[g]), self.md)
        self.assertIn("| all | %d | %d |" % (len(self.named), self.permissions()), self.md)

    def test_washu_clause(self):
        # Only near-variant trials carry it, and every one names a path.
        self.assertEqual(len(self.washu_any), len(self.groups["washu"]))
        years = [int(r["start_year"]) for r in self.groups["washu"]]
        self.assertIn("%d started 2019 or earlier and %d in 2020 or later; the earliest in %d." % (
            sum(y <= 2019 for y in years), sum(y >= 2020 for y in years), min(years)), self.md)
        c = self.read["search_counts"]
        self.assertIn("in %d trials, %d of them led by" % (c["registry_with_washu_clause"],
                                                            c["washu_led_with_washu_clause"]), self.md)
        self.assertIn("(%d of the first 50 returned), and %d Washington University trials" % (
            c["washu_led_share_of_first_50_with_clause"], c["washu_led_with_near_variant_line"]), self.md)
        self.assertLessEqual(c["washu_led_with_washu_clause"], c["registry_with_washu_clause"])

    def test_mark_table(self):
        self.assertEqual(sum(self.count(k) for k in MARKS), len(self.read["marks"]))
        for k in MARKS:
            self.assertIn("| %s | %d |" % (k, self.count(k)), self.md)
        self.assertIn("The %d that are not permissions" % self.count("not_a_permission"), self.md)
        self.assertIn("all %d read by eye" % len(self.groups["other"]), self.md)

    def test_share_and_combined_estimate(self):
        loose, perms = len(self.loose), self.permissions()
        self.assertIn("%d of %s (%.1f%%) give an adult" % (perms, num(loose), 100.0 * perms / loose), self.md)
        k = sum(1 for m in self.exact_read["marks"] if m["mark"] == "adult_permission")
        n = len(self.exact_read["marks"])
        lo, hi = wilson(k, n)
        named, exact = self.s["adult_path"]["with"], self.s["stock_exact"]
        est = [round(named * x) + perms for x in (k / n, lo, hi)]
        both = exact + loose
        self.assertIn("about %d trials (%d-%d) of the %s that use either line" % (
            est[0], est[1], est[2], num(both)), self.md)
        self.assertIn("that path, %.1f%% (%.1f-%.1f)." % tuple(100.0 * e / both for e in est), self.md)
        self.assertGreater(perms / loose, 2 * named * k / n / exact)

    def test_labels(self):
        self.assertIn("not yet checked by a person", self.md)
        self.assertIn("Made by MV2 of Munim, Inc. with AI agents.", self.md)
        self.assertNotIn("MIT", self.md)


if __name__ == "__main__":
    unittest.main()
