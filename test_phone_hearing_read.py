"""Offline tests for the S2 reading of the telephone test (no network). Apache-2.0.

Checks results/phone-check/phone-hearing-read.json against the pre-registered queries and marking
rule, and the numbers PHONE-HEARING-READ.md quotes against the data.
"""

import json
import math
import os
import re
import unittest

import phone_matched as pm
import trend_check as tc
import va_matched as vm

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "results", "phone-check", "phone-hearing-read.json")
NOTE = os.path.join(HERE, "results", "phone-check", "PHONE-HEARING-READ.md")
NOT_VA = "NOT AREA[LeadSponsorName](VA OR Veteran OR Veterans)"
PHONE_WORD = re.compile(r"phone|\bcalls?\b", re.I)


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def query(exposure):
    return " AND ".join(["AREA[StudyType]INTERVENTIONAL", "AREA[Phase]NA", exposure,
                         "AREA[EligibilityCriteria]" + tc.criteria(pm.HEARING),
                         "NOT AREA[ConditionSearch](%s)" % vm.OWN, NOT_VA])


def fisher_one_sided(a, n1, b, n0):
    """P(at least a of the K = a + b marked rows fall in the first group of n1), hypergeometric."""
    k, n = a + b, n1 + n0
    return sum(math.comb(k, i) * math.comb(n - k, n1 - i)
               for i in range(a, min(k, n1) + 1)) / math.comb(n, n1)


def tally(rows, key):
    return sum(1 for r in rows if r[key])


class QueryTests(unittest.TestCase):
    def test_queries_are_the_preregistered_ones(self):
        g = load()["groups"]
        self.assertEqual(g["telephone"]["query"], query(pm.PHONE))
        self.assertEqual(g["other"]["query"], query("NOT " + pm.PHONE))

    def test_telephone_total_matches_the_nonva_count(self):
        # phone-matched-nonva-counts.json: 279 non-VA telephone trials name a hearing wording.
        self.assertEqual(load()["groups"]["telephone"]["total"], 279)


class ReadingTests(unittest.TestCase):
    def test_twenty_distinct_trials_each(self):
        g = load()["groups"]
        ids = [r["nct"] for grp in g.values() for r in grp["rows"]]
        self.assertEqual([len(grp["rows"]) for grp in g.values()], [20, 20])
        self.assertEqual(len(set(ids)), 40)

    def test_phone_tied_follows_the_rule(self):
        for grp in load()["groups"].values():
            for r in grp["rows"]:
                text = " ".join(t for _, t in r["items"])
                self.assertEqual(r["phone_tied"], bool(PHONE_WORD.search(text)), r["nct"])

    def test_sections(self):
        for grp in load()["groups"].values():
            for r in grp["rows"]:
                self.assertTrue(r["items"])
                for section, _ in r["items"]:
                    self.assertIn(section, ("inclusion", "exclusion"))

    def test_counts(self):
        g = load()["groups"]
        tel, oth = g["telephone"]["rows"], g["other"]["rows"]
        self.assertEqual((tally(tel, "phone_tied"), tally(oth, "phone_tied")), (4, 1))
        self.assertEqual((tally(tel, "shuts_out"), tally(oth, "shuts_out")), (20, 20))
        self.assertEqual((tally(tel, "other_item_names_phone"),
                          tally(oth, "other_item_names_phone")), (12, 5))
        anywhere = [sum(1 for r in rows if r["phone_tied"] or r["other_item_names_phone"])
                    for rows in (tel, oth)]
        self.assertEqual(anywhere, [13, 5])


class TestTests(unittest.TestCase):
    def test_fisher_by_hand(self):
        # By symmetry (20 and 20), P(X >= 4) = P(X <= 1) = (C(35,15) + 5 C(35,16)) / C(40,20).
        self.assertAlmostEqual(fisher_one_sided(4, 20, 1, 20),
                               (3247943160 + 5 * 4059928950) / 137846528820, places=12)
        self.assertAlmostEqual(fisher_one_sided(0, 20, 5, 20), 1.0, places=12)
        self.assertAlmostEqual(fisher_one_sided(4, 20, 1, 20), 1 - fisher_one_sided(2, 20, 3, 20),
                               places=12)

    def test_published_result(self):
        d = load()
        res = d["result"]
        tel, oth = (d["groups"][k]["rows"] for k in ("telephone", "other"))
        a, b = tally(tel, "phone_tied"), tally(oth, "phone_tied")
        self.assertEqual(res["phone_tied"], {"telephone": a, "other": b})
        self.assertEqual(res["fisher_one_sided_p"], round(fisher_one_sided(a, 20, b, 20), 4))
        self.assertEqual(res["prediction_telephone_at_least_5"], a >= 5)
        self.assertEqual(res["prediction_other_at_most_2"], b <= 2)

    def test_note_quotes_the_data(self):
        with open(NOTE, encoding="utf-8") as f:
            note = f.read()
        for s in ("**4 of 20**", "**1 of 20**", "p = 0.17", "279", "3,150", "12 of 20", "13 of 20",
                  "5 of 20"):
            self.assertIn(s, note)
        for grp in load()["groups"].values():
            for r in grp["rows"]:
                self.assertIn(r["nct"], note)


if __name__ == "__main__":
    unittest.main()
