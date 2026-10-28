"""Offline tests: the first run's item-level precision table against its sample and its error list. Apache-2.0.

Made by MV2 of Munim, Inc. with AI agents. The README quotes 720 flagged exclusion items read for
precision (60 per category, 360 in the six disability categories) and per-category figures from
75% (visual) to 100%. The per-item verdicts were made by AI agents and are recorded only in
results/v0.1.1/PRECISION.md: the table of correct / checked counts and the named false positives
(the `correct` column of sample_items.csv was left empty). These tests check that the table, the
error list, the sampled items and the README agree with each other. They cannot check the
verdicts themselves; only a person re-reading the items can. No network.
"""

import collections
import csv
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PRECISION = "results/v0.1.1/PRECISION.md"
ITEMS = "results/v0.1.1/sample_items.csv"
README = "README.md"
DISABILITY = ("cognitive", "consent_capacity", "visual", "hearing", "communication", "mobility")
ROW = re.compile(r"^\| ([a-z_]+) \| (\d+) / (\d+) \| (\d+)%")
BULLET = re.compile(r"^- \*\*([A-Za-z_ ]+) \((\d+)\)\.\*\*")


def read(rel):
    with open(os.path.join(HERE, *rel.split("/")), encoding="utf-8") as f:
        return f.read()


def table(text):
    return {m.group(1): (int(m.group(2)), int(m.group(3)), int(m.group(4)))
            for m in map(ROW.match, text.splitlines()) if m}


def false_positives(text):
    """{category: (count in the bold label, NCT ids named in its bullet and sub-bullets)}."""
    section = text.split("## The false positives", 1)[1].split("\n## ", 1)[0]
    found, cat = {}, None
    for line in section.splitlines():
        m = BULLET.match(line)
        if m:
            cat = m.group(1).strip().replace(" ", "_")
            found[cat] = (int(m.group(2)), set())
        elif line.startswith(("- ", "#")):
            cat = None
        if cat:
            found[cat][1].update(re.findall(r"NCT\d{8}", line))
    return found


def pct(k, n):
    return int(100 * k / n + 0.5)


class PrecisionNumberTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = read(PRECISION)
        cls.table = table(text)
        cls.errors = false_positives(text)
        with open(os.path.join(HERE, *ITEMS.split("/")), encoding="utf-8", newline="") as f:
            cls.items = list(csv.DictReader(f))

    def test_table_is_720_items(self):
        self.assertEqual(len(self.table), 12)
        self.assertEqual({n for _, n, _ in self.table.values()}, {60})
        self.assertEqual(sum(n for _, n, _ in self.table.values()), 720)
        self.assertEqual(sum(self.table[c][1] for c in DISABILITY), 360)

    def test_sample_matches_table(self):
        per = collections.Counter(r["category"] for r in self.items)
        self.assertEqual(len(self.items), 720)
        self.assertEqual(set(per), set(self.table))
        self.assertEqual(set(per.values()), {60})

    def test_printed_percentages(self):
        for cat, (k, n, p) in self.table.items():
            self.assertEqual(pct(k, n), p, cat)
        shares = [p for _, _, p in self.table.values()]
        self.assertEqual((min(shares), max(shares)), (75, 100))
        self.assertEqual(self.table["visual"][:2], (45, 60))

    def test_error_list_matches_table(self):
        self.assertTrue(set(self.errors) <= set(self.table), sorted(self.errors))
        for cat, (k, n, _) in self.table.items():
            listed = self.errors[cat][0] if cat in self.errors else 0
            self.assertEqual(listed, n - k, cat)
        self.assertEqual(sum(n - k for k, n, _ in self.table.values()), 45)
        self.assertEqual(sum(self.table[c][1] - self.table[c][0] for c in DISABILITY), 29)

    def test_named_items_were_sampled(self):
        sampled = {(r["category"], r["nct"]) for r in self.items}
        for cat, (_, ncts) in self.errors.items():
            for nct in sorted(ncts):
                self.assertIn((cat, nct), sampled)

    def test_readme_figures(self):
        text = " ".join(read(README).split())  # the README wraps its lines
        self.assertIn("720 random flagged exclusion items", text)
        t = self.table
        self.assertIn(f"Cognitive was {t['cognitive'][2]}% correct", text)
        for cat in ("consent_capacity", "hearing", "communication", "mobility", "visual"):
            self.assertIn(f"{cat.replace('_', ' ')} {t[cat][2]}%", text)


if __name__ == "__main__":
    unittest.main()
