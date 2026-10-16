"""Offline tests for the published 0.4.0 full-registry run (no network). Apache-2.0.

Checks that the tables in results/v0.4.0/ agree with each other, that the held-out recall scores
in results/recall/SCORES-0.4.0.md are correct fractions with correct Wilson intervals, and that
every number the README quotes from them is the number in the data.
"""

import csv
import json
import math
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join(HERE, "results", "v0.4.0")
SCORES = os.path.join(HERE, "results", "recall", "SCORES-0.4.0.md")
README = os.path.join(HERE, "README.md")
FRACTION = re.compile(r"(\d+)/(\d+) = (\d+)% \((\d+)-(\d+)%\)")


def load(name):
    with open(os.path.join(RUN, name), encoding="utf-8") as f:
        return json.load(f)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def wilson(a, n, z=1.96):
    p = a / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - half) / (1 + z * z / n), (centre + half) / (1 + z * z / n)


def readme_section():
    text = read(README)
    start = text.index("## The 0.4.0 rules on the full registry")
    return text[start:text.index("\n## ", start + 1)]


class TableTests(unittest.TestCase):
    def test_run(self):
        s = load("summary.json")
        self.assertEqual((s["version"], s["fetched_at"]), ("0.4.0", "2026-10-15"))
        self.assertEqual((s["records"], s["with_criteria"], s["total"]["trials"]),
                         (463329, 463289, 450201))

    def test_csv_tables_match_summary(self):
        s = load("summary.json")
        for name, key in (("by_year.csv", "by_year"), ("by_year_design.csv", "by_year_design"),
                          ("by_sponsor.csv", "by_sponsor"), ("by_phase.csv", "by_phase")):
            with open(os.path.join(RUN, name), encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), len(s[key]), name)
            for row in rows:
                group = s[key][row[next(iter(row))]]
                shared = [k for k in row if k in group]
                self.assertGreaterEqual(len(shared), 30, name)
                for k in shared:
                    if row[k] == "":  # a share of no trials, e.g. accommodation_if_core_pct
                        self.assertIsNone(group[k], (name, k))
                    else:
                        self.assertEqual(float(row[k]), float(group[k]), (name, k))

    def test_year_groups_add_up(self):
        s = load("summary.json")
        for year, group in s["by_year"].items():
            parts = [s["by_year_design"][year + "|" + d]["trials"] for d in ("phased", "no_phase")
                     if year + "|" + d in s["by_year_design"]]
            self.assertEqual(sum(parts), group["trials"], year)

    def test_diff_with_030_rules(self):
        d, s = load("diff_summary.json"), load("summary.json")
        n = d["trials_with_exclusion_section"]
        self.assertEqual(n, s["total"]["trials"])
        self.assertEqual(round(100 * d["any_core_new"] / n, 2), s["total"]["any_core_pct"])
        self.assertEqual(round(100 * d["any_core_old"] / n, 2), d["any_core_old_pct"])


class ScoreTests(unittest.TestCase):
    def test_every_fraction_and_interval(self):
        found = FRACTION.findall(read(SCORES))
        self.assertGreaterEqual(len(found), 25)
        for a, n, pct, lo, hi in found:
            a, n = int(a), int(n)
            low, high = wilson(a, n)
            self.assertLessEqual(abs(100 * a / n - int(pct)), 0.5, (a, n))
            self.assertLessEqual(abs(100 * low - int(lo)), 0.5, (a, n))
            self.assertLessEqual(abs(100 * high - int(hi)), 0.5, (a, n))

    def test_headline_rows(self):
        text = read(SCORES)
        self.assertIn("census rules 0.4.0; labelled trials: 78 random, 33 broad.", text)
        for s in ("| any | 22 | 16 | 16/16 = 100% (81-100%) | 16/22 = 73% (52-87%) |",
                  "| any | 19 | 14 | 13/14 = 93% (69-99%) | 13/19 = 68% (46-85%) |",
                  "13/78 = 17% (10-26%)"):
            self.assertIn(s, text)


class ReadmeTests(unittest.TestCase):
    def test_quoted_registry_numbers(self):
        t, text = load("summary.json")["total"], readme_section()
        quotes = {"463,329": 463329, "450,201": t["trials"],
                  "**22.37%**": t["any_core_pct"], "**20.18%**": t["any_core_unrelated_pct"],
                  "cognitive 10.38%": t["cognitive_pct"],
                  "consent capacity 8.67%": t["consent_capacity_pct"],
                  "mobility 3.44%": t["mobility_pct"], "hearing 2.63%": t["hearing_pct"],
                  "visual 2.25%": t["visual_pct"], "communication 2.01%": t["communication_pct"],
                  "16.36%": t["any_required_pct"], "(12.69%)": t["consent_capacity_required_pct"],
                  "**33.74%**": t["any_barrier_pct"], "**11.38%**": t["required_only_pct"],
                  "(5.13%)": t["accommodation_pct"],
                  "19.81%": load("diff_summary.json")["any_core_old_pct"]}
        for quoted, value in quotes.items():
            self.assertIn(quoted, text)
            number = float(re.sub(r"[^\d.]", "", quoted).strip(".").replace(",", ""))
            self.assertEqual(number, value, quoted)

    def test_quoted_years(self):
        s, text = load("summary.json"), readme_section()
        y, d = s["by_year"], s["by_year_design"]
        for quoted, value in (("15.16%", y["2008"]["any_core_pct"]),
                              ("27.83%", y["2025"]["any_core_pct"]),
                              ("30.91%", y["2026"]["any_core_pct"]),
                              ("8.96", y["2008"]["exclusion_items_mean"]),
                              ("9.31", y["2025"]["exclusion_items_mean"]),
                              ("2.04", y["2008"]["core_items_per_100"]),
                              ("3.98", y["2025"]["core_items_per_100"]),
                              ("21.59%", d["2008|no_phase"]["any_core_pct"]),
                              ("33.40%", d["2025|no_phase"]["any_core_pct"]),
                              ("12.48%", d["2008|phased"]["any_core_pct"]),
                              ("17.66%", d["2025|phased"]["any_core_pct"])):
            self.assertIn(quoted, text)
            self.assertEqual(float(quoted.rstrip("%")), value, quoted)
        ratio = lambda g, a, b: "%.2f times" % (g[b]["any_core_pct"] / g[a]["any_core_pct"])
        for quoted in (ratio(y, "2008", "2025"), ratio(d, "2008|no_phase", "2025|no_phase"),
                       ratio(d, "2008|phased", "2025|phased")):
            self.assertIn(quoted, text)
        self.assertEqual([ratio(y, "2008", "2025"), ratio(d, "2008|no_phase", "2025|no_phase"),
                          ratio(d, "2008|phased", "2025|phased")],
                         ["1.84 times", "1.55 times", "1.42 times"])

    def test_quoted_recall(self):
        text = readme_section()
        for quoted in ("16 of the 22", "(73%; Wilson 95% interval 52% to 87%)", "15 of 22",
                       "13 of 19 (68%, 46% to 85%)", "13 of 14", "13 of 78 (17%, 10% to 26%)"):
            self.assertIn(quoted, text)
        scores = read(SCORES)
        for s in ("16/22 = 73% (52-87%)", "16/16", "13/19 = 68% (46-85%)", "13/14",
                  "13/78 = 17% (10-26%)"):
            self.assertIn(s, scores)


if __name__ == "__main__":
    unittest.main()
