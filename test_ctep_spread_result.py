"""Tests for CTEP-SPREAD-RESULT.md (no network). Apache-2.0.

Re-grades the saved per-trial table with ctep_spread 0.1.0, rebuilds the run's table and printed
result, and checks every figure the note quotes. The run and the note were made by AI agents
working for MV2; no person has checked them yet.
"""

import csv
import hashlib
import io
import json
import os
import re
import tempfile
import unittest

import ctep_spread as cs

HERE = os.path.dirname(os.path.abspath(__file__))
RESULT = os.path.join(HERE, "results", "ctep-spread")

# The sha256 printed in the sealed run (ctep-spread-v1).
RUN_SHA256 = {
    "ctep_spread.py": "38234e4c87b44ff89fc51726fcbf12e740163e67475d9a4a247d3a7bd94e5651",
    "test_ctep_spread.py": "03cdb356cea67b719535a3a35569ce0428c51c2f6c437e7edd0fd1cfa7a4ddd4",
}
BOOLS = ("nci_linked", "washu_led", "stock", "clause", "in_frame", "anchor")
SWOG = "SWOG Cancer Research Network"
# Organisations named in the note; the other Neither lead sponsors are individual investigators.
ORGS = ("Fred Hutchinson Cancer Center", "Montefiore Medical Center", SWOG, "Curis, Inc.",
        "University of Cincinnati", "University of Florida", "University of Kentucky",
        "Virginia Commonwealth University")


def raw(name):
    with open(os.path.join(RESULT, name), "rb") as f:
        return f.read()


def text(name):
    return raw(name).decode("utf-8")


def plain(x):
    return json.loads(json.dumps(x))


def saved():
    return json.loads(text("result.json"))


def rows():
    out = list(csv.DictReader(io.StringIO(text("ctep-spread-trials.csv"))))
    for r in out:
        for k in BOOLS:
            assert r[k] in ("True", "False"), (k, r[k])
            r[k] = r[k] == "True"
    return out


def pct(x):
    return "%.2f" % (100 * x)


def one_line(md):
    return re.sub(r"\s+", " ", md)


class SavedRunTests(unittest.TestCase):
    def test_code_is_what_ran(self):
        for name, digest in RUN_SHA256.items():
            with open(os.path.join(HERE, name), "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), digest, name)
        self.assertEqual(saved()["script_sha256"], RUN_SHA256["ctep_spread.py"])

    def test_table_rebuilds_byte_for_byte(self):
        out = os.path.join(tempfile.mkdtemp(), "trials.csv")
        cs.write_trials(out, rows())
        with open(out, "rb") as f:
            self.assertEqual(f.read(), raw("ctep-spread-trials.csv"))

    def test_grade_and_description_follow_from_the_table(self):
        r, t = saved(), rows()
        self.assertEqual(len(t), r["sentence_trials"])
        measures, preds = cs.grade(t)
        self.assertEqual(plain(measures), r["measures"])
        self.assertEqual(plain(preds), r["predictions"])
        self.assertEqual(plain(cs.described(t)), r["described"])
        self.assertEqual(cs.result_text(r), text("result.txt").rstrip("\n"))

    def test_saved_status(self):
        r = saved()
        self.assertEqual(r["status"], "graded")
        self.assertEqual(sorted(r["gates"]), ["A1_table", "A2_searches_complete", "A3_recall",
                                              "P0_prereg_public"])
        self.assertTrue(all(r["gates"].values()), r["gates"])
        self.assertEqual(r["polls"], 1)
        self.assertEqual(r["predictions"],
                         {"R1": False, "R2": True, "R3": True, "R4": False, "R5": True})
        for row in rows():
            self.assertTrue(row["period"] in ("pre", "gap", "post"), row["nct_id"])
            self.assertEqual(row["period"], cs.period(row["submitted"]), row["nct_id"])


class NoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = saved()
        cls.t = rows()
        cls.md = text("CTEP-SPREAD-RESULT.md")
        cls.flat = one_line(cls.md)
        cls.neither = [x for x in cls.t if x["group"] == "neither"]
        cls.swog = [x for x in cls.t if x["lead_sponsor"] == SWOG]

    def test_in_short(self):
        r, md, t = self.r, self.md, self.t
        g = r["described"]["by_group"]
        self.assertIn("is in the eligibility text of %d ClinicalTrials.gov trials today."
                      % len(t), md)
        self.assertIn("- %d of the %d are linked to the National Cancer Institute (NCI) or led by "
                      "Washington University School of Medicine (WashU): %d NCI-linked, %d "
                      "WashU-led, %d both." % (g["nci"] + g["washu"] + g["both"], len(t), g["nci"],
                                               g["washu"], g["both"]), md)
        first = min(x["submitted"] for x in self.neither)
        self.assertEqual(first, r["described"]["first_submitted"]["neither"])
        self.assertIn("- Only %d trials (Neither) carry it without listing NCI or WashU, and every "
                      "one of them was first submitted on or after %s." % (len(self.neither),
                                                                           first), md)
        k, n, share, ci = r["measures"]["R1_neither_of_post"]
        self.assertEqual(n, sum(1 for x in t if x["period"] == "post"))
        self.assertIn("- Of the %d trials first submitted on or after %s, %d are Neither (%s%%, 95%% "
                      "CI %s%% to %s%%), about half the 25%% predicted." % (
                          n, cs.FIRST_WITH, k, pct(k / n), pct(ci[0]), pct(ci[1])), md)
        self.assertEqual(cs.R1_MIN_NEITHER_POST, 0.25)
        self.assertIn("**3 of 5 predictions hold; the main one (R1) does not.**", md)

    def test_gates(self):
        r, md = self.r, self.md
        self.assertTrue(cs.PHRASE_COMMIT.startswith("c4c0ded"))
        self.assertIn("A1: the consent-phrase table (commit c4c0ded) has {:,} rows and {} anchors."
                      .format(r["phrase_rows"], r["anchors"]), md)
        s = r["searches"]
        self.assertEqual([x["term"] for x in s], list(cs.SEARCHES))
        self.assertIn("A2: the three searches returned %d, %d and %d studies, each read in full "
                      "(%d, %d and %d received)." % tuple([x["total"] for x in s]
                                                          + [x["received"] for x in s]), md)
        rc = r["recall"]
        self.assertEqual(rc["missed"], [])
        self.assertEqual(rc["anchors_current"], rc["anchors"])
        self.assertIn("A3: all %d anchors still carry the sentence today and all %d were found by "
                      "the searches (recall %s)." % (rc["anchors_current"], rc["anchors_found"],
                                                     rc["recall"]), md)
        self.assertIn("Of the studies each search returned, %d, %d and %d carry the sentence."
                      % tuple(x["sentence"] for x in s), md)

    def test_predictions(self):
        m, md, p = self.r["measures"], self.md, self.r["predictions"]
        k, n = m["R1_neither_of_post"][:2]
        self.assertIn("- **R1 (main): %s.** %d of %d post-period trials are Neither (%s%%); at "
                      "least 25%% was predicted." % ("holds" if p["R1"] else "fails", k, n,
                                                     pct(k / n)), md)
        k, n = m["R2_pre_of_dated_neither"][:2]
        self.assertIn("- **R2: %s.** %d of %d dated Neither trials were first submitted on or "
                      "before %s (at most 10%% predicted)." % ("holds" if p["R2"] else "fails",
                                                              k, n, cs.LAST_WITHOUT), md)
        k, n = m["R3_industry_of_all"][:2]
        self.assertIn("- **R3: %s.** %d of %d trials has an industry lead sponsor (%s%%; at most "
                      "5%% predicted)." % ("holds" if p["R3"] else "fails", k, n, pct(k / n)), md)
        k, n, share, ci = m["R4_stock_of_neither"]
        self.assertIn("- **R4: %s.** %d of %d Neither trials also carry CTEP's stock consent line "
                      "(%s%%, 95%% CI %s%% to %s%%); at least 80%% was predicted." % (
                          "holds" if p["R4"] else "fails", k, n, pct(k / n), pct(ci[0]),
                          pct(ci[1])), md)
        self.assertIn("- **R5: %s.** The %d Neither trials have %d distinct lead sponsors (at least "
                      "10 predicted)." % ("holds" if p["R5"] else "fails", len(self.neither),
                                          m["R5_neither_lead_sponsors"]), md)
        self.assertEqual((cs.R2_MAX_NEITHER_PRE, cs.R3_MAX_INDUSTRY, cs.R4_MIN_NEITHER_STOCK,
                          cs.R5_MIN_NEITHER_SPONSORS), (0.10, 0.05, 0.80, 10))
        self.assertEqual(sum(1 for v in p.values() if v), 3)

    def test_neither_sponsors(self):
        md = self.md
        counts = {}
        for x in self.neither:
            counts[x["lead_sponsor"]] = counts.get(x["lead_sponsor"], 0) + 1
        orgs = sorted(((c, s) for s, c in counts.items() if s in ORGS), key=lambda cs_: (-cs_[0],
                                                                                         cs_[1]))
        self.assertEqual({s for _, s in orgs}, set(ORGS))
        many = ", ".join("%s %d" % (s, c) for c, s in orgs if c > 1)
        ones = [s for c, s in orgs if c == 1]
        self.assertIn("- Lead sponsors: %s, and one each for %s and %s." % (
            many, ", ".join(ones[:-1]), ones[-1]), md)
        people = [x for x in self.neither if x["lead_sponsor"] not in ORGS]
        self.assertEqual(len({x["lead_sponsor"] for x in people}), len(people))
        self.assertIn("- %d Neither trials name an individual investigator as lead sponsor (not "
                      "listed here)." % len(people), md)
        for x in people:
            self.assertNotIn(x["lead_sponsor"], md)
        years = {}
        for x in self.neither:
            years[x["submitted"][:4]] = years.get(x["submitted"][:4], 0) + 1
        self.assertEqual(sorted(years), ["2025", "2026"])
        self.assertIn("- By first-submitted year: %d in 2025 and %d in 2026." % (
            years["2025"], years["2026"]), md)
        self.assertIn("first Neither trial was submitted nearly two years after the first CTEP "
                      "template version with the sentence (August 4, 2023)", self.flat)

    def test_swog(self):
        md, t = self.md, self.t
        self.assertEqual(sum(1 for x in self.swog if x["stock"]), 0)
        self.assertIn("- %d trials led by %s carry the sentence, and none of the %d carries CTEP's "
                      "stock consent line." % (len(self.swog), SWOG, len(self.swog)), md)
        no_stock = [x for x in t if not x["stock"]]
        self.assertEqual(len(t) - len(no_stock), self.r["described"]["with_stock"])
        other_nci = [x for x in no_stock if x["lead_sponsor"] != SWOG and x["nci_linked"]]
        washu = [x for x in no_stock if x["group"] == "washu"]
        rest = [x for x in no_stock if x["group"] == "neither" and x["lead_sponsor"] != SWOG]
        self.assertFalse(any(x["group"] == "both" for x in no_stock))
        self.assertEqual(len(self.swog) + len(other_nci) + len(washu) + len(rest), len(no_stock))
        self.assertIn("- %d of the %d trials lack the stock line: %d SWOG-led, %d others linked to "
                      "NCI, %d WashU-led and %d other Neither trials." % (
                          len(no_stock), len(t), len(self.swog), len(other_nci), len(washu),
                          len(rest)), md)
        first = min(t, key=lambda x: x["submitted"])
        self.assertEqual(first["lead_sponsor"], SWOG)
        self.assertEqual(first["submitted"], min(self.r["described"]["first_submitted"].values()))
        self.assertIn("- The earliest first-submitted date among the %d is %s, a SWOG-led trial."
                      % (len(t), first["submitted"]), md)

    def test_before_the_template(self):
        md, t = self.md, self.t

        def split(period):
            sel = [x for x in t if x["period"] == period]
            self.assertTrue(all(x["group"] in ("nci", "washu") for x in sel))
            nci = [x for x in sel if x["group"] == "nci"]
            return (len(sel), len(nci), sum(1 for x in nci if x["lead_sponsor"] == SWOG),
                    sum(1 for x in sel if x["group"] == "washu"))

        self.assertIn("- %d trials first submitted on or before %s carry the sentence today: %d "
                      "NCI-linked (%d of them SWOG-led) and %d WashU-led."
                      % ((split("pre")[0], cs.LAST_WITHOUT) + split("pre")[1:]), md)
        self.assertIn("- %d more were first submitted between 2022-07-10 and 2023-08-03: %d "
                      "NCI-linked (%d SWOG-led) and %d WashU-led." % split("gap"), md)
        self.assertEqual(cs.FIRST_WITH, "2023-08-04")
        n = split("pre")[0] + split("gap")[0]
        self.assertIn("these %d trials may have gained the sentence" % n, self.flat)

    def test_also_reported(self):
        d, md, t = self.r["described"], self.md, self.t
        self.assertIn("- %d of the %d trials lie outside the 2026-10-16 stock-line frame"
                      % (d["outside_frame"], len(t)), md)
        self.assertEqual(d["with_clause"], 0)
        self.assertIn("- None of the %d carries WashU's older clause" % len(t), md)
        cls_ = sorted(d["by_lead_class"].items(), key=lambda kv: (-kv[1], kv[0]))
        self.assertIn("- Lead-sponsor class: %s." % ", ".join("%s %d" % kv for kv in cls_), md)
        self.assertIn("%d trials outside NCI and WashU in the whole registry" % len(self.neither),
                      self.flat)
        self.assertIn("3,666 frame trials outside the two owners", self.flat)

    def test_timing_hashes_and_wording(self):
        md = self.md
        self.assertIn(self.r["fetched_utc"], md)
        self.assertIn("commit 9ee0ec0", md)
        self.assertIn("at the first poll", md)
        self.assertIn("not yet checked by a person", self.flat)
        for digest in RUN_SHA256.values():
            self.assertIn(digest, md)
        self.assertIn("their 21 tests passed", md)
        self.assertEqual(re.findall(r"by\s+hand|by\s+eye|hand[- ]check", md, re.I), [])
        self.assertNotIn("MIT", md)


if __name__ == "__main__":
    unittest.main()
