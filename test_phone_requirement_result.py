"""Tests for PHONE-REQUIREMENT-RESULT.md (no network). Apache-2.0.

Recomputes every number the note quotes from the saved counts, the S2 reading list, the pattern
marks and the reading by eye, and checks each mark by eye against its rule.
"""

import json
import os
import unittest

import phone_marks as pmk
import phone_requirement as pr
import va_matched as vm

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "results", "phone-check")


def load(name):
    with open(os.path.join(CHECK, name), encoding="utf-8") as f:
        return f.read() if name.endswith(".md") else json.loads(f.read())


def plain(x):
    return json.loads(json.dumps(x))


class CountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load("phone-requirement-counts.json")
        cls.saved = load("phone-requirement.json")
        cls.rows = pr.rows(cls.data)
        cls.by = {r["phrase"]: r for r in cls.rows}
        cls.md = load("PHONE-REQUIREMENT-RESULT.md")

    def test_saved_results_follow_from_the_counts(self):
        self.assertEqual(plain(self.rows), self.saved["rows"])
        self.assertEqual(plain(pr.verdicts(self.rows)), self.saved["verdicts"])
        self.assertEqual(plain(vm.test(self.rows)), self.saved["s1"])
        self.assertEqual(pr.checks(self.data), self.saved["checks"])
        self.assertTrue(all(pr.checks(self.data).values()))

    def test_verdicts(self):
        self.assertEqual(pr.verdicts(self.rows), {"HP1": True, "HP2": True, "rivals": 8})
        self.assertIn("**HP1 (primary): holds.**", self.md)
        self.assertIn("**HP2 (primary): holds.**", self.md)
        self.assertIn("(8 rivals;", self.md)
        self.assertIn("1 time in 9", self.md)
        t = vm.test(self.rows)
        self.assertIn("against %d kept controls, rank sum %s, p = %s." % (
            t["controls"], t["rank_sum"], t["p"]), self.md)

    def test_strata_and_base(self):
        t, w = self.data["trials"], self.data["wordings"]
        for s in self.data["strata"]:
            self.assertIn("| %s | %s | %s |" % (s, "{:,}".format(t[s]["phone"]),
                                                 "{:,}".format(t[s]["registry"] - t[s]["phone"])), self.md)
        before = load("prereg-phone-requirement.json")["wording_check_known_before"]["base"]
        self.assertIn("the base had {:,} trials ({:,} when".format(w["base"], before), self.md)
        share = round(100.0 * w["(phone OR telephone)"] / w["base"], 1)
        self.assertIn("{:,} name a phone ({}%)".format(w["(phone OR telephone)"], share), self.md)

    def test_ratio_table(self):
        for r in self.rows:
            line = "| %s | %s | %s | %s | %.2f (%.2f-%.2f) |" % (
                r["phrase"], r["kind"], r["va"], r["expected"], r["mh"], r["low"], r["high"])
            if r["kept"]:
                self.assertIn(line, self.md)
            else:
                self.assertNotIn("| %s |" % r["phrase"], self.md)
                self.assertIn("(%s phone-arm matches expected, fewer than %d)" % (
                    r["expected"], vm.MIN_EXPECTED), self.md)

    def test_quoted_ratios(self):
        h, v = self.by[pr.HEARING], self.by[pr.VISUAL]
        top = max((r for r in self.rows if r["kind"] == "control" and r["kept"]), key=lambda r: r["mh"])
        self.assertEqual(top["phrase"], "hernia")
        self.assertIn("%.2f times (%.2f-%.2f)" % (h["mh"], h["low"], h["high"]), self.md)
        self.assertIn("matched interval, %.2f-%.2f, lies above 1" % (h["low"], h["high"]), self.md)
        self.assertIn("visual wording rises %.2f times" % v["mh"], self.md)
        self.assertIn("no kept control more than %.2f times" % top["mh"], self.md)


class ReadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.list = load("s2-reading-list.json")
        cls.marks = [pmk.mark(r) for r in cls.list["rows"]]
        cls.read = load("phone-requirement-read.json")["rows"]
        cls.crit = {r["nct"]: r["criteria"] for r in cls.list["rows"]}
        cls.md = load("PHONE-REQUIREMENT-RESULT.md")

    def test_list_is_the_preregistered_query(self):
        self.assertEqual(self.list["query"], pr.reading_term())
        self.assertEqual(len(self.list["rows"]), 20)
        hearing = load("phone-requirement.json")["rows"]
        total = [r["va"] for r in hearing if r["phrase"] == pr.HEARING][0]
        self.assertEqual(self.list["total"], total)
        self.assertIn("20 of the %d phone-arm hearing trials" % total, self.md)

    def test_saved_marks_follow_from_the_list(self):
        self.assertEqual(plain(self.marks), load("s2-marks.json")["marks"])

    def test_reading_by_eye_agrees_with_the_patterns(self):
        self.assertEqual([r["nct"] for r in self.read], [m["nct"] for m in self.marks])
        for r, m in zip(self.read, self.marks):
            self.assertEqual((r["a"], r["b"]), (m["a_requirement"], m["b_phone_tied"]), r["nct"])
            self.assertEqual(m["check_by_eye"], [])
            self.assertIn("| %s | %s | %s |" % (r["nct"], "yes" if r["a"] else "no",
                                                 "yes" if r["b"] else "no"), self.md)
        self.assertIn("(%d of %d)" % (2 * len(self.read), 2 * len(self.read)), self.md)

    def test_s2_counts(self):
        p = load("prereg-phone-requirement.json")
        a = sum(r["a"] for r in self.read)
        b = sum(r["b"] for r in self.read)
        self.assertGreaterEqual(a, p["s2_requirement_prediction_at_least"])
        self.assertGreaterEqual(b, p["s2_tied_reading_rule_at_least"])
        self.assertIn("names a phone in %d of 20" % a, self.md)
        self.assertIn("names a phone or calls in %d of 20" % b, self.md)
        self.assertIn("in %d of 20 trials read" % b, self.md)
        self.assertIn("at least %d of 20 would make HP1" % p["s2_tied_reading_rule_at_least"], self.md)
        both = sum(r["a"] and r["b"] for r in self.read)
        a_only = sum(r["a"] and not r["b"] for r in self.read)
        b_only = sum(r["b"] and not r["a"] for r in self.read)
        neither = sum(not (r["a"] or r["b"]) for r in self.read)
        self.assertIn("Both marks in %d," % both, self.md)
        self.assertIn("doesn't name the phone in %d," % a_only, self.md)
        self.assertIn("a phone-tied hearing item only in %d, neither in %d." % (b_only, neither), self.md)

    def test_overlap(self):
        over = pmk.overlaps(self.marks, load("phone-hearing-read.json"))
        self.assertEqual(over, [{"nct": "NCT03060096", "group": "telephone"}])
        self.assertIn("NCT03060096 was also read for PHONE-HEARING-READ", self.md)

    def test_only_phone_item_is_a_hearing_item(self):
        only = []
        for r in self.list["rows"]:
            phone = [t for _, t in pmk.items(r["criteria"]) if pmk.REQUIREMENT.search(t)]
            if phone and all(pmk.HEARING.search(t) for t in phone):
                only.append(r["nct"])
        self.assertEqual(len(only), 6)
        for n in only:
            note = [r["note"] for r in self.read if r["nct"] == n][0]
            self.assertIn("the only item that names a phone", note)
        self.assertIn("In %d of 20 the hearing item is the only item" % len(only), self.md)

    def test_phone_access_as_exclusion(self):
        quoted = [r for r in self.read if r["phone_access_as_exclusion"]]
        for r in quoted:
            self.assertFalse(r["a"], r["nct"])
            self.assertIn(r["phone_access_as_exclusion"], self.crit[r["nct"]])
            self.assertTrue(pmk.REQUIREMENT.search(r["phone_access_as_exclusion"]))
        no_a = sum(not r["a"] for r in self.read)
        self.assertIn("%d of the %d trials without an inclusion phone item" % (len(quoted), no_a), self.md)
        written = sum(r["a"] or bool(r["phone_access_as_exclusion"]) for r in self.read)
        self.assertIn("condition appears in %d of 20" % written, self.md)

    def test_delivery_tied(self):
        other = [r for r in self.read if r["delivery_tied_other_words"]]
        self.assertEqual([r["nct"] for r in other], ["NCT05242575"])
        self.assertFalse(other[0]["b"])
        self.assertIn("mobile device", self.crit["NCT05242575"])
        tied = sum(r["b"] or r["delivery_tied_other_words"] for r in self.read)
        self.assertIn("so %d of 20 tie hearing" % tied, self.md)

    def test_earlier_reading_quoted(self):
        tel = load("phone-hearing-read.json")["groups"]["telephone"]["rows"]
        self.assertEqual(len(tel), 20)
        self.assertIn("named the phone in %d of 20 telephone trials" % sum(r["phone_tied"] for r in tel),
                      self.md)


if __name__ == "__main__":
    unittest.main()
