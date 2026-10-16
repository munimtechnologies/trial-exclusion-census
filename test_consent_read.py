"""Offline tests for CONSENT-RESULT.md (no network). Apache-2.0.

Recomputes every number the note quotes from consent-phrase.json, consent-phrase-trials.csv and
the reading in consent-read.json, and checks that each mark follows the rules written in the file.
"""

import csv
import json
import math
import os
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


class ConsentReadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load("consent-phrase.json")
        cls.s = cls.data["summary"]
        cls.rows = load("consent-phrase-trials.csv")
        cls.read = load("consent-read.json")
        cls.marks = cls.read["marks"]
        cls.md = load("CONSENT-RESULT.md").replace("\r\n", "\n")

    def count(self, mark):
        return sum(1 for m in self.marks if m["mark"] == mark)

    def test_reading_is_the_saved_sample(self):
        self.assertEqual([m["nct_id"] for m in self.marks],
                         [r["nct_id"] for r in self.data["reading_sample"]])
        self.assertEqual(len(self.marks), 50)
        self.assertEqual(sorted(self.read["rules"]), sorted(MARKS))
        for m in self.marks:
            self.assertIn(m["mark"], MARKS, m["nct_id"])
            self.assertTrue(m["note"], m["nct_id"])

    def test_marks_follow_the_rules(self):
        by_id = {r["nct_id"]: r for r in self.rows}
        for m in self.marks:
            r = by_id[m["nct_id"]]
            self.assertEqual((r["stock_exact"], r["adult_path"]), ("True", "True"), m["nct_id"])
            adult = r["adult_only"] == "True"
            if m["mark"] == "adult_permission":
                self.assertTrue(adult, m["nct_id"])
            if m["mark"] in ("minor_only", "unclear"):
                self.assertFalse(adult, m["nct_id"])

    def test_mark_table(self):
        self.assertEqual(sum(self.count(k) for k in MARKS), len(self.marks))
        for k in MARKS:
            self.assertIn("| %s | %d |" % (k, self.count(k)), self.md)
        self.assertIn("sample of %d of the %d was read" % (len(self.marks), self.s["adult_path"]["with"]), self.md)

    def test_registry_counts(self):
        s = self.s
        self.assertEqual(s["downloaded"], s["registry_total"])
        self.assertEqual(len(self.rows), s["downloaded"])
        self.assertEqual(sum(r["stock_exact"] == "True" for r in self.rows), s["stock_exact"])
        self.assertEqual(sum(r["stock_exact"] == "True" and r["adult_path"] == "True" for r in self.rows),
                         s["adult_path"]["with"])
        self.assertIn("The search found %s trials; all were downloaded." % num(s["registry_total"]), self.md)
        self.assertIn("%s have the exact line; %s only a near variant" % (num(s["stock_exact"]),
                                                                           num(s["stock_loose_only"])), self.md)
        self.assertIn("; %d neither." % s["neither"], self.md)
        a = s["adult_path"]
        self.assertIn("%d of %s (%.1f%%) name a representative" % (a["with"], num(a["trials"]),
                                                                   100.0 * a["with"] / a["trials"]), self.md)
        self.assertIn("IDMC phrase appears in %d trials with the exact line" % s["paths"]["idmc"], self.md)

    def test_permission_share_and_estimate(self):
        k, n = self.count("adult_permission"), len(self.marks)
        lo, hi = wilson(k, n)
        self.assertIn("Adult permission: %d of %d, %.1f%% (%.1f-%.1f, Wilson 95%%)." % (
            k, n, 100.0 * k / n, 100 * lo, 100 * hi), self.md)
        named, exact = self.s["adult_path"]["with"], self.s["stock_exact"]
        p = k / n
        self.assertIn("about %d trials (%d-%d), %.1f%% (%.1f-%.1f) of the %s with the exact line." % (
            round(named * p), round(named * lo), round(named * hi), 100.0 * named * p / exact,
            100.0 * named * lo / exact, 100.0 * named * hi / exact, num(exact)), self.md)
        self.assertIn("So in roughly %d%% of trials" % round(100 - 100.0 * named * p / exact), self.md)
        self.assertIn("in this sample %d of %d trials" % (k, n), self.md)

    def test_years(self):
        by_year = [r for r in self.s["by_year"] if r["start_year"] is not None]
        for label, rows in (("2019 or earlier", [r for r in by_year if r["start_year"] <= 2019]),
                            ("2020-2026", [r for r in by_year if 2020 <= r["start_year"] <= 2026])):
            t, w = sum(r["trials"] for r in rows), sum(r["with"] for r in rows)
            self.assertIn("| %s | %s | %d | %.1f |" % (label, num(t), w, 100.0 * w / t), self.md)

    def test_templates(self):
        t, by = self.s["templates"], self.s["template_by_year"]

        def started(name, first, last):
            return sum(r["with"] for r in by[name]
                       if r["start_year"] is not None and first <= r["start_year"] <= last)

        also = t["nci_idmc_also_eligible"]["with"]
        self.assertIn("is in %d trials with the exact line, %d of %d started 2020-2023" % (
            also, started("nci_idmc_also_eligible", 2020, 2023), also), self.md)
        lar = t["nci_lar_may_sign"]["with"]
        self.assertIn("is in %d trials with the exact line, %d of %d started 2023 or later" % (
            lar, started("nci_lar_may_sign", 2023, 9999), lar), self.md)
        lar_all = sum(r["nci_lar_may_sign"] == "True" for r in self.rows)
        lar_not_exact = sum(r["nci_lar_may_sign"] == "True" and r["stock_exact"] == "False" for r in self.rows)
        self.assertEqual(lar_all - lar_not_exact, lar)
        self.assertIn("the LAR sentence is in %d trials in all, %d of them without the exact line." % (
            lar_all, lar_not_exact), self.md)

    def test_near_variant(self):
        loose = [r for r in self.rows if r["stock_exact"] == "False" and r["stock_loose"] == "True"]
        self.assertEqual(len(loose), self.s["stock_loose_only"])
        w = sum(r["adult_path"] == "True" for r in loose)
        self.assertIn("%d of %s (%.1f%%) name a representative, guardian or" % (
            w, num(len(loose)), 100.0 * w / len(loose)), self.md)

    def test_labels(self):
        self.assertIn("not yet checked by a person", self.md)
        self.assertIn("Made by MV2 of Munim, Inc. with AI agents.", self.md)
        self.assertNotIn("MIT", self.md)


if __name__ == "__main__":
    unittest.main()
