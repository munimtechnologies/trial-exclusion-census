"""Offline tests for phone_marks (no network). Apache-2.0.

Checks the item splitting and the two marks on made-up records, the rules against the
pre-registration, and the marks against the 40 items PHONE-HEARING-READ marked by eye.
"""

import json
import os
import tempfile
import unittest
from unittest import mock

import phone_marks as pk

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "results", "phone-check")
R1 = ("Inclusion Criteria:\n\n* Age 18 or older\n* Has access to a telephone\n\n"
      "Exclusion Criteria:\n\n* Significant hearing loss\n* Heart failure")
R2 = ("Inclusion Criteria:\n\n1. Adults with diabetes\n\nExclusion Criteria:\n\n"
      "1. Hearing impairment that prevents telephone calls\n2. Unable to use a smartphone")
R3 = "Exclusion criteria:\n- Deaf or unable to take\n  part in calls\n- Pregnant"
R4 = "Inclusion Criteria:\n* Able to speak English"
R5 = "Hearing loss\nPregnancy"
ROWS = [{"nct": "NCT01", "title": "one", "criteria": R1}, {"nct": "NCT02", "title": "two", "criteria": R2},
        {"nct": "NCT03", "title": "three", "criteria": R3}, {"nct": "NCT04", "title": "four", "criteria": R4}]
READ = {"groups": {"telephone": {"rows": [{"nct": "NCT02"}]}, "other": {"rows": [{"nct": "NCT09"}]}}}


class SplitTests(unittest.TestCase):
    def test_headings(self):
        self.assertEqual(pk.heading("Inclusion Criteria:"), "inclusion")
        self.assertEqual(pk.heading("**Exclusion criteria**"), "exclusion")
        self.assertEqual(pk.heading("Key Inclusion Criteria"), "inclusion")
        self.assertEqual(pk.heading("Exclusion:"), "exclusion")
        self.assertEqual(pk.heading("Inclusion and Exclusion Criteria:"), "unknown")
        self.assertIsNone(pk.heading("* Does not meet inclusion criteria"))
        self.assertIsNone(pk.heading("Patients with hearing loss"))

    def test_items(self):
        self.assertEqual(pk.items(R1), [["inclusion", "Age 18 or older"],
                                        ["inclusion", "Has access to a telephone"],
                                        ["exclusion", "Significant hearing loss"],
                                        ["exclusion", "Heart failure"]])
        self.assertEqual(pk.items(R3), [["exclusion", "Deaf or unable to take part in calls"],
                                        ["exclusion", "Pregnant"]])
        self.assertEqual(pk.items(None), [])


class MarkTests(unittest.TestCase):
    def test_requirement_without_tie(self):
        m = pk.mark(ROWS[0])
        self.assertEqual(m["hearing_items"], [["exclusion", "Significant hearing loss"]])
        self.assertEqual(m["inclusion_phone_items"], ["Has access to a telephone"])
        self.assertEqual((m["a_requirement"], m["b_phone_tied"], m["check_by_eye"]), (True, False, []))

    def test_tie_without_requirement(self):
        # The smartphone item is an exclusion, so it is not (a).
        m = pk.mark(ROWS[1])
        self.assertEqual((m["a_requirement"], m["b_phone_tied"]), (False, True))
        self.assertTrue(pk.mark(ROWS[2])["b_phone_tied"])

    def test_flags(self):
        self.assertEqual(pk.mark(ROWS[3])["check_by_eye"], ["no hearing item found"])
        m = pk.mark({"nct": "NCT05", "criteria": R5})
        self.assertEqual(m["check_by_eye"], ["no inclusion or exclusion heading"])
        self.assertFalse(m["b_phone_tied"])

    def test_summary_and_markdown(self):
        marks = [pk.mark(r) for r in ROWS]
        self.assertEqual(pk.summary(marks), {"trials": 4, "a_requirement": 1, "b_phone_tied": 2,
                                             "check_by_eye": 1, "a_prediction_met": False,
                                             "b_tied_rule_met": False})
        md = pk.markdown(marks, pk.overlaps(marks, READ))
        self.assertIn("| NCT01 | yes | no | - |", md)
        self.assertIn("| NCT02 | no | yes | - |", md)
        self.assertIn("| NCT04 | no | no | no hearing item found |", md)
        self.assertIn("By pattern: (a) in 1 of 4 (predicted at least 12: not met); (b) in 2 of 4 "
                      "(at least 11 would make HP1 mostly the hearing items' own wording: no); "
                      "1 to check by eye.", md)
        self.assertIn("Also read for PHONE-HEARING-READ: NCT02 (telephone).", md)
        self.assertNotIn("Also read", pk.markdown(marks))

    def test_main_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            lst, rd, out = (os.path.join(d, n) for n in ("list.json", "read.json", "out.json"))
            with open(lst, "w", encoding="utf-8") as f:
                json.dump({"query": "q", "total": 279, "rows": ROWS}, f)
            with open(rd, "w", encoding="utf-8") as f:
                json.dump(READ, f)
            with mock.patch("builtins.print"):
                self.assertEqual(pk.main([lst, "--read", rd, "--json", out]), 0)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual((data["total"], data["summary"]["a_requirement"]), (279, 1))
            self.assertEqual(data["overlaps"], [{"nct": "NCT02", "group": "telephone"}])
            with mock.patch("builtins.print"):
                pk.main([lst, "--read", "", "--json", out])
            with open(out, encoding="utf-8") as f:
                self.assertIsNone(json.load(f)["overlaps"])


class RuleTests(unittest.TestCase):
    def test_rules_are_the_preregistered_ones(self):
        path = os.path.join(CHECK, "prereg-phone-requirement.json")
        if not os.path.exists(path):
            self.skipTest("PREREG-PHONE-REQUIREMENT not published yet")
        with open(path, encoding="utf-8") as f:
            p = json.load(f)
        s2 = p["secondary"][1]
        self.assertIn("matches 'phone' (case-insensitive)", s2)
        self.assertEqual(pk.REQUIREMENT.pattern, "phone")
        self.assertIn(pk.TIED.pattern, s2)
        self.assertEqual(p["s2_requirement_prediction_at_least"], pk.PREDICTED_A)
        self.assertEqual(p["s2_tied_reading_rule_at_least"], pk.TIED_RULE)

    def test_marks_agree_with_the_earlier_reading_by_eye(self):
        # PHONE-HEARING-READ marked 40 hearing items by eye on 2026-10-15 (4 + 1 phone-tied).
        with open(os.path.join(CHECK, "phone-hearing-read.json"), encoding="utf-8") as f:
            read = json.load(f)
        n = tied = 0
        for g in read["groups"].values():
            for r in g["rows"]:
                n += 1
                self.assertTrue(all(pk.HEARING.search(t) for _, t in r["items"]), r["nct"])
                got = any(pk.TIED.search(t) for _, t in r["items"])
                self.assertEqual(got, r["phone_tied"], r["nct"])
                tied += got
        self.assertEqual((n, tied), (40, 5))


if __name__ == "__main__":
    unittest.main()
