"""Offline tests for recall_sample (no network). Apache-2.0."""

import csv
import os
import tempfile
import unittest

import recall_sample as rs

RECORDS = [
    {"nct": "A", "title": "Insulin", "conditions": ["Diabetes"],
     "criteria": "Exclusion Criteria:\n* Legally blind"},
    {"nct": "B", "title": "Inhaler", "conditions": ["Asthma"],
     "criteria": "Exclusion Criteria:\n* Pregnancy"},
    {"nct": "C", "title": "Exercise", "conditions": ["Heart Failure"],
     "criteria": "Inclusion Criteria:\n* Able to walk 100 m\nExclusion Criteria:\n* Pregnancy"},
    {"nct": "D", "title": "Diet", "conditions": ["Obesity"], "criteria": "Adults with obesity."},
]


def by_nct(rows):
    return {r["nct"]: r for r in rows}


class DrawTests(unittest.TestCase):
    def test_all_with_exclusion_section(self):
        rows, seen = rs.draw(RECORDS, n_random=10, n_broad=10)
        self.assertEqual(sorted(r["nct"] for r in rows), ["A", "B", "C"])
        self.assertEqual({r["stratum"] for r in rows}, {"random"})
        self.assertEqual(seen, {"random": 3, "broad": 1})
        self.assertEqual(sorted(r["label"] for r in rows), ["R001", "R002", "R003"])

    def test_broad_pool(self):
        rows, _ = rs.draw(RECORDS, n_random=0, n_broad=5)
        self.assertEqual([(r["nct"], r["stratum"], r["label"]) for r in rows], [("C", "broad", "R001")])

    def test_seeded(self):
        a, _ = rs.draw(RECORDS, n_random=2, n_broad=1, seed=7)
        b, _ = rs.draw(RECORDS, n_random=2, n_broad=1, seed=7)
        self.assertEqual([(r["nct"], r["label"]) for r in a], [(r["nct"], r["label"]) for r in b])
        self.assertEqual(sum(r["stratum"] == "random" for r in a), 2)


class ScoreTests(unittest.TestCase):
    def labelled(self):
        rows, _ = rs.draw(RECORDS, n_random=10, n_broad=10)
        lab = {r["nct"]: r["label"] for r in rows}
        labels = {
            lab["A"]: {"label": lab["A"], "done": "1", "visual": "x"},
            lab["B"]: {"label": lab["B"], "done": "1", "hearing": "x", "notes": "deaf, worded oddly"},
            lab["C"]: {"label": lab["C"], "done": "1", "mobility": "i"},
        }
        return rows, labels, lab

    def test_counts(self):
        rows, labels, lab = self.labelled()
        res = rs.score(rows, labels)
        self.assertEqual(res["labelled"], {"random": 3, "broad": 0})
        self.assertEqual(res["counts"]["visual"], {"tp": 1, "fp": 0, "fn": 0})
        self.assertEqual(res["counts"]["hearing"], {"tp": 0, "fp": 0, "fn": 1})
        self.assertEqual(res["counts"]["any"], {"tp": 1, "fp": 0, "fn": 1})
        self.assertEqual(res["inclusion_any"], 1)
        self.assertEqual(res["inclusion_only"], 1)
        self.assertEqual([(m["nct"], m["category"]) for m in res["misses"]], [("B", "hearing")])

    def test_unlabelled_rows_skipped(self):
        rows, labels, lab = self.labelled()
        del labels[lab["B"]]
        res = rs.score(rows, labels)
        self.assertEqual(res["labelled"]["random"], 2)
        self.assertEqual(res["misses"], [])

    def test_report(self):
        rows, labels, _ = self.labelled()
        md = rs.score_md(rs.score(rows, labels))
        self.assertIn("| visual | 1 | 1 | 1/1 = 100%", md)
        self.assertIn("| hearing | 1 | 0 | n/a | 0/1 = 0%", md)
        self.assertIn("deaf, worded oddly", md)

    def test_marks(self):
        self.assertEqual(rs.marks("x"), (True, False))
        self.assertEqual(rs.marks(" XI "), (True, True))
        self.assertEqual(rs.marks(""), (False, False))
        self.assertEqual(rs.marks(None), (False, False))


class WilsonTests(unittest.TestCase):
    def test_interval(self):
        self.assertIsNone(rs.wilson(0, 0))
        lo, hi = rs.wilson(5, 10)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)
        self.assertAlmostEqual(rs.wilson(10, 10)[1], 1.0)
        self.assertAlmostEqual(rs.wilson(0, 10)[0], 0.0)


class FileTests(unittest.TestCase):
    def test_round_trip(self):
        rows, seen = rs.draw(RECORDS, n_random=10, n_broad=10)
        with tempfile.TemporaryDirectory() as d:
            rs.write_sample(rows, seen, d)
            for name in ("sample.jsonl", "blind.md", "labels.csv", "flags.csv", "sample_info.json"):
                self.assertTrue(os.path.exists(os.path.join(d, name)), name)
            with open(os.path.join(d, "blind.md"), encoding="utf-8") as f:
                blind = f.read()
            self.assertIn("Legally blind", blind)
            self.assertNotIn("stratum", blind)
            labels_path = os.path.join(d, "labels.csv")
            with open(labels_path, newline="", encoding="utf-8") as f:
                table = list(csv.reader(f))
            self.assertEqual(table[0][:3], ["label", "nct", "done"])
            self.assertEqual(len(table), 4)
            table[1][2] = "1"
            with open(labels_path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(table)
            self.assertEqual(list(rs.read_labels(labels_path)), [table[1][0]])
            again = rs.read_sample(os.path.join(d, "sample.jsonl"))
            self.assertEqual(by_nct(again).keys(), by_nct(rows).keys())
            with open(os.path.join(d, "flags.csv"), newline="", encoding="utf-8") as f:
                flags = {row["nct"]: row for row in csv.DictReader(f)}
            self.assertEqual(flags["A"]["visual"], "1")
            self.assertEqual(flags["C"]["mobility"], "0")


if __name__ == "__main__":
    unittest.main()
