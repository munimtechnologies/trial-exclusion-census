"""Tests for CONSENT-SPONSOR-RESULT.md (no network). Apache-2.0.

Recomputes the saved analysis of consent_sponsor 0.1.0 from its per-trial table, checks the saved
text output against it, and checks every figure the note quotes. The run and the note were made by
AI agents working for MV2; no person has checked them yet.
"""

import csv
import hashlib
import json
import os
import re
import unittest

import consent_sponsor as cs

HERE = os.path.dirname(os.path.abspath(__file__))
RESULT = os.path.join(HERE, "results", "consent-sponsor")

# The sha256 printed in the sealed run, before the fetch.
RUN_SHA256 = {
    "consent_sponsor.py": "db510fa197b561a4b2f3c4631fdcc24e0d82c9c59485a87a22f7d24e72297176",
    "test_consent_sponsor.py": "1c1576efd26822056e3da3f074ba7f6e5472231567650fd42af02fd35e861413",
}
ORGANISATION_WORDS = ("Institute", "University", "Center", "Group", "Hospital", "Inc.")


def read(name):
    with open(os.path.join(RESULT, name), encoding="utf-8") as f:
        return f.read()


def plain(x):
    return json.loads(json.dumps(x))


def labelled():
    """The labelled rows consent_sponsor.analyse() saw, rebuilt from the saved per-trial table."""
    with open(os.path.join(RESULT, "consent-sponsor-trials.csv"), encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    lab = []
    for r in rows:
        nci, washu = cs.truthy(r["nci_linked"]), cs.truthy(r["washu_led"])
        lab.append({"nct_id": r["nct_id"], "start_year": r["start_year"],
                    "adult_only": r["adult_only"], "adult_path": r["adult_path"],
                    "nci_linked": nci, "washu_led": washu, "template_owner": nci or washu,
                    "lead_bucket": cs.lead_bucket({"lead_class": r["lead_class"]}),
                    "lead": r["lead_sponsor"]})
    return lab


def pc(c):
    return "%s of %s (%.1f%%)" % ("{:,}".format(c["with_path"]), "{:,}".format(c["trials"]),
                                  100 * c["share"])


def rr(x):
    return "%.2f (%.2f-%.2f)" % (x["rr"], x["low"], x["high"])


class SavedRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = json.loads(read("consent-sponsor.json"))
        cls.lab = labelled()

    def test_saved_run(self):
        s = self.saved
        self.assertEqual(s["version"], cs.__version__)
        self.assertEqual(s["csv_url"], cs.CSV_URL)
        self.assertTrue(s["csv_sha256"].startswith("c7f87d926976"))
        self.assertTrue(all(s["gates"].values()), s["gates"])
        self.assertEqual((s["counts"]["rows"], s["counts"]["population"], s["counts"]["covered"]),
                         (5473, 5436, 5436))
        self.assertEqual(len(self.lab), 5436)
        self.assertEqual(len({r["nct_id"] for r in self.lab}), 5436)

    def test_analysis_follows_from_the_table(self):
        self.assertEqual(plain(cs.analyse(self.lab)), self.saved["analysis"])
        adult = [r for r in self.lab if cs.truthy(r["adult_only"])]
        self.assertEqual(plain(cs.analyse(adult)), self.saved["secondary_adult_only"])
        self.assertEqual(plain(cs.top_leads(self.lab)), self.saved["top_leads"])
        self.assertEqual(cs.predictions(self.saved["analysis"]), self.saved["predictions"])

    def test_text_output(self):
        self.assertEqual(cs.markdown(self.saved), read("consent-sponsor.txt").rstrip("\n"))

    def test_code_is_what_ran(self):
        for name, digest in RUN_SHA256.items():
            with open(os.path.join(HERE, name), "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), digest, name)


class NoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = json.loads(read("consent-sponsor.json"))
        cls.a = cls.saved["analysis"]
        cls.md = read("CONSENT-SPONSOR-RESULT.md")

    def test_predictions(self):
        self.assertEqual(self.saved["predictions"],
                         {"P1": True, "P2": True, "P3": False, "P4": False, "P5": False})
        for p, name in (("P1", "P1"), ("P2", "P2"), ("P3", "P3 (main)"), ("P4", "P4"), ("P5", "P5")):
            verdict = "holds" if self.saved["predictions"][p] else "fails"
            self.assertIn("**%s: %s.**" % (name, verdict), self.md)

    def test_quoted_shares(self):
        a = self.a
        cells = (list(a["groups"].values()) + list(a["lead_class"].values())
                 + list(a["neither_lead_class"].values()) + list(a["neither_period"].values()))
        for p in a["by_period"].values():
            cells += list(p.values())
        for c in cells:
            self.assertIn(pc(c), self.md)

    def test_quoted_ratios_and_owner_shares(self):
        a, s = self.a, self.saved["secondary_adult_only"]
        for x in (a["rr_nci_vs_neither"], a["rr_washu_vs_neither"], a["rr_neither_late_vs_early"],
                  s["rr_nci_vs_neither"], s["rr_washu_vs_neither"]):
            self.assertIn(rr(x), self.md)
        for share in (a["template_owner_share_of_paths"], a["template_owner_share_of_trials"],
                      s["template_owner_share_of_paths"]):
            self.assertIn("%.1f%%" % (100 * share), self.md)
        self.assertIn("{:,} of the {:,} trials that name".format(a["template_owner_paths"], a["paths"]),
                      self.md)
        self.assertIn("{:,} of {:,} trials (".format(a["groups"]["template_owner"]["trials"],
                                                     a["groups"]["all"]["trials"]), self.md)

    def test_top_leads_organisations_only(self):
        tops = self.saved["top_leads"]
        orgs = [t for t in tops if any(w in t["lead"] for w in ORGANISATION_WORDS)]
        self.assertEqual((len(tops), len(orgs)), (15, 14))
        for t in orgs:
            self.assertIn("| %s | %d | %d |" % (t["lead"], t["trials"], t["with_path"]), self.md)
        other = [t for t in tops if t not in orgs][0]
        self.assertNotIn(other["lead"], self.md)
        self.assertIn("one individual investigator listed as lead sponsor (%d of %d trials)" % (
            other["with_path"], other["trials"]), self.md)

    def test_timing_and_wording(self):
        self.assertIn(self.saved["started_utc"], self.md)
        self.assertIn("committed at 06:52 UTC", self.md)
        self.assertIn("not yet checked by a person", self.md)
        self.assertEqual(re.findall(r"by\s+hand|by\s+eye|hand[- ]check", self.md, re.I), [])
        for digest in RUN_SHA256.values():
            self.assertIn(digest, self.md)


if __name__ == "__main__":
    unittest.main()
