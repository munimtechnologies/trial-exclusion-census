"""Tests for SENTENCE-ORIGIN-RESULT.md (no network). Apache-2.0.

Re-grades every prediction with sentence_origin 0.1.0 from the saved page table and the
ctep-spread trial table, rebuilds the run's printed result, and checks every figure the note
quotes. The run and the note were made by AI agents working for MV2; no person has checked them
yet.
"""

import csv
import hashlib
import io
import json
import os
import re
import unittest

import sentence_origin as so

HERE = os.path.dirname(os.path.abspath(__file__))
RESULT = os.path.join(HERE, "results", "sentence-origin")
TABLE = os.path.join(HERE, "results", "ctep-spread", "ctep-spread-trials.csv")

# The sha256 printed in the sealed run (sentence-origin-v1).
RUN_SHA256 = {
    "sentence_origin.py": "489fec512f157f44b9283ea24757060b620fbf8f960611a7f80f0007d34a2607",
    "test_sentence_origin.py": "56ea8d78278e86f0ba08903ccec799279da3b2d152f908d8260fd32c974d99cc",
}
NCI = "National Cancer Institute (NCI)"
SWOG = "SWOG Cancer Research Network"
LABEL = {"washu": "WashU-led", "swog": "SWOG-led", "nci": "NCI-led"}
WORD = {"sentence": "sentence", "clause": "WashU clause", "neither": "neither"}
ROLES = (("oldest", "oldest"), ("newest_pre", "last by 2022-07-09"),
         ("newest_early", "last by 2023-08-03"))
# Predictions held in the chain's earlier graded tests, as each result note states them.
CHAIN = (("consent-sponsor", 2, 5), ("consent-permission", 5, 5), ("washu-switch", 3, 5),
         ("ctep-template", 4, 4), ("ctep-spread", 3, 5))


def raw(path):
    with open(path, "rb") as f:
        return f.read()


def saved():
    return json.loads(raw(os.path.join(RESULT, "result.json")).decode("utf-8"))


def plain(x):
    return json.loads(json.dumps(x))


def day(ts):
    return "%s-%s-%s" % (ts[:4], ts[4:6], ts[6:8])


def listing(ids):
    ids = list(ids)
    return ids[0] if len(ids) == 1 else "%s and %s" % (", ".join(ids[:-1]), ids[-1])


def table_rows():
    return so.read_table(raw(TABLE))


def trials():
    return so.cohort(table_rows())


def pages():
    data = raw(os.path.join(RESULT, "sentence-origin-pages.csv")).decode("utf-8")
    return list(csv.DictReader(io.StringIO(data)))


def marks_from_pages(ts, rows):
    """Each trial's usable page per list, as the run kept it (the first usable page tried)."""
    marks = {t["nct_id"]: {"oldest": None, "newest_pre": None, "newest_early": None} for t in ts}
    for r in rows:
        if r["usable"] != "True":
            continue
        m = marks[r["nct_id"]]
        assert m[r["role"]] is None, (r["nct_id"], r["role"])  # the run stops at the first one
        m[r["role"]] = {k: r[k] == "True" for k in ("usable", "sentence", "clause", "stock")}
        m[r["role"]]["ts"] = r["ts"]
    return marks


class SavedRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = saved()
        cls.t = trials()
        cls.rows = pages()
        cls.marks = marks_from_pages(cls.t, cls.rows)

    def test_code_is_what_ran(self):
        for name, digest in RUN_SHA256.items():
            self.assertEqual(hashlib.sha256(raw(os.path.join(HERE, name))).hexdigest(), digest,
                             name)
        self.assertEqual(self.r["script_sha256"], RUN_SHA256["sentence_origin.py"])
        self.assertEqual(self.r["version"], so.__version__)

    def test_printed_result_rebuilds(self):
        text = raw(os.path.join(RESULT, "result.txt")).decode("utf-8")
        self.assertEqual(so.result_text(self.r), text.rstrip("\n"))

    def test_table_is_what_the_run_read(self):
        rows = table_rows()
        self.assertEqual(hashlib.sha256(raw(TABLE)).hexdigest(), self.r["table_sha256"])
        self.assertTrue(so.table_ok(rows, self.t))
        self.assertEqual([x["nct_id"] for x in self.t], self.r["order"])

    def test_grade_follows_from_the_pages(self):
        r = self.r
        g = so.grade(self.t, self.marks, r["complete"])
        gates = g.pop("gates")
        for k, v in gates.items():
            self.assertEqual(v, r["gates"][k], k)
        for k in ("usable_trials", "complete_trials", "S1", "S2", "S3", "S4", "predictions"):
            self.assertEqual(plain(g[k]), r[k], k)
        self.assertEqual(plain(so.described(self.t, self.marks)), r["described"])
        self.assertEqual(r["predictions"], {"S1": True, "S2": True, "S3": True, "S4": True})
        self.assertEqual(r["status"], "graded")
        self.assertTrue(all(r["gates"].values()))
        self.assertEqual(r["polls"], 1)

    def test_page_rows_are_consistent(self):
        r = self.r
        self.assertEqual(r["download_errors"], 0)
        self.assertTrue(all(x["downloaded"] == "True" for x in self.rows))
        self.assertTrue(all(x["nct_id"] in r["complete"] for x in self.rows))


class NoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = saved()
        cls.t = {x["nct_id"]: x for x in trials()}
        cls.d = cls.r["described"]["trials"]
        cls.md = raw(os.path.join(RESULT, "SENTENCE-ORIGIN-RESULT.md")).decode("utf-8")
        cls.flat = re.sub(r"\s+", " ", cls.md)
        cls.with_page = [n for n in cls.r["order"] if any(cls.d[n]["pages"].values())]
        cls.no_page = [n for n in cls.r["order"] if n not in cls.with_page]

    def test_in_short(self):
        r, md, d = self.r, self.md, self.d
        n, ts = r["described"]["earliest_sentence_page"]
        self.assertEqual(d[n]["kind"], "swog")
        self.assertIn("- The earliest archived page with the sentence is %s, a SWOG-led trial, "
                      "captured on %s, a week after it was first submitted on %s."
                      % (n, day(ts), d[n]["submitted"]), md)
        s1 = r["S1"]
        self.assertIn("- %d of the %d trials with a usable page captured on or before 2022-07-09 "
                      "already carry it there." % (len(s1["with_sentence"]), len(s1["graded_on"])),
                      md)
        self.assertIn("- SWOG-led trials carried it from registration (%d of %d on their oldest "
                      "page); NCI-led trials mostly gained it later (%d of %d on their oldest page)."
                      % (len(r["S2"]["with_sentence"]), len(r["S2"]["graded_on"]),
                         len(r["S3"]["with_sentence"]), len(r["S3"]["graded_on"])), md)
        gained = r["described"]["gained_before_cutoff"]
        early = sorted(d[x]["pages"]["newest_pre"][0] for x in gained
                       if d[x]["pages"]["newest_pre"]
                       and d[x]["pages"]["newest_pre"][1] == "sentence")
        self.assertTrue(all(x <= so.CUTOFF_PRE for x in early))
        self.assertTrue(all(self.t[x]["lead_sponsor"] == NCI for x in gained))
        self.assertIn("- %d NCI-led trials that lacked it on their oldest page show it on pages "
                      "captured between %s and %s, before any archived CTEP template has it."
                      % (len(early), day(early[0]), day(early[-1])), md)
        self.assertIn("**All 4 predictions hold.**", md)

    def test_gates(self):
        r, md = self.r, self.md
        kinds = [so.kind(self.t[n]) for n in r["order"]]
        self.assertIn("A1: the ctep-spread table has %d trials; the cohort is its %d trials first "
                      "submitted on or before 2023-08-03 (%d WashU-led, %d SWOG-led, %d other "
                      "NCI-linked)." % (so.TABLE_ROWS, len(r["order"]), kinds.count("washu"),
                                        kinds.count("swog"), kinds.count("nci")), md)
        self.assertEqual(so.CUTOFF_EARLY, "20230803")
        self.assertIn("A2: %d of the %d trials have a usable page (at least %d needed)."
                      % (r["usable_trials"], r["trials"], so.MIN_USABLE_TRIALS), md)
        bad = [n for n in r["order"] if not r["complete"][n]]
        for n in bad:
            self.assertTrue(any("503" in str(x) for x in r["cdx"][n]["rows"]), n)
        self.assertIn("A3: %d of the %d were read completely (at least %d needed); index queries "
                      "for %s were answered with HTTP 503." % (
                          r["complete_trials"], r["trials"], so.MIN_COMPLETE_TRIALS, listing(bad)),
                      md)
        self.assertIn("Archive reading: {} index queries ({} errors), {} pages downloaded ({} "
                      "errors), {:,} seconds.".format(r["cdx_queries"], r["cdx_errors"],
                                                      r["downloaded"], r["download_errors"],
                                                      r["elapsed_seconds"]), md)

    def test_predictions(self):
        r, md, d = self.r, self.md, self.d
        s1 = r["S1"]
        self.assertIn("- **S1 (main): holds.** %d of the %d trials with a usable page captured on or "
                      "before 2022-07-09 carry the sentence on such a page: %s (at least 1 "
                      "predicted; graded only with at least %d trials)." % (
                          len(s1["with_sentence"]), len(s1["graded_on"]),
                          listing(s1["with_sentence"]), so.S1_MIN_GRADED), md)
        s2 = r["S2"]
        miss = [n for n in s2["graded_on"] if n not in s2["with_sentence"]]
        self.assertEqual(len(miss), 1)
        m = miss[0]
        self.assertTrue(all(v is None or v[1] != "sentence" for v in d[m]["pages"].values()))
        self.assertIn("- **S2: holds.** %d of the %d SWOG-led trials with a usable oldest page "
                      "carry the sentence on it (at least half predicted). The fifth, %s (first "
                      "submitted %s), lacks it on every page read, the last captured %s."
                      % (len(s2["with_sentence"]), len(s2["graded_on"]), m, d[m]["submitted"],
                         day(d[m]["pages"]["newest_early"][0])), md)
        s3 = r["S3"]
        self.assertTrue(all(self.t[n]["lead_sponsor"] == NCI for n in s3["graded_on"]))
        self.assertIn("- **S3: holds.** %d of the %d other NCI-linked trials with a usable oldest "
                      "page carry the sentence on it (at most half predicted): %s." % (
                          len(s3["with_sentence"]), len(s3["graded_on"]),
                          listing(s3["with_sentence"])), md)
        s4 = r["S4"]
        self.assertEqual(s4["with_sentence"], [])
        self.assertEqual(len(s4["graded_on"]), 2)
        absent = [n for n in so.EARLY_WASHU if n not in s4["graded_on"]]
        self.assertEqual(absent, ["NCT05521984"])
        self.assertEqual(r["cdx"]["NCT05521984"]["captures"], 0)
        self.assertIn("- **S4: holds.** Neither of the 2 early WashU-led trials with a usable oldest "
                      "page carries the sentence on it (it holds only if none does). NCT05521984 "
                      "has no archived page before 2023-08-04.", md)

    def test_per_trial_lines(self):
        md, d = self.md, self.d
        for n in self.with_page:
            x = d[n]
            if x["kind"] == "nci":
                self.assertEqual(self.t[n]["lead_sponsor"], NCI, n)
            if x["kind"] == "swog":
                self.assertEqual(self.t[n]["lead_sponsor"], SWOG, n)
            parts = []
            for role, label in ROLES:
                p = x["pages"][role]
                parts.append("%s %s (%s)" % (day(p[0]), WORD[p[1]], label) if p
                             else "none (%s)" % label)
            self.assertIn("- %s (%s, first submitted %s): %s." % (
                n, LABEL[x["kind"]], x["submitted"], "; ".join(parts)), md)
        self.assertEqual(len(self.with_page), self.r["usable_trials"])
        for n in self.r["order"]:
            self.assertEqual(n in self.with_page, self.r["cdx"][n]["captures"] > 0, n)
        kinds = [d[n]["kind"] for n in self.no_page]
        washu = [n for n in self.no_page if d[n]["kind"] == "washu"]
        first = min(d[n]["submitted"] for n in self.no_page)
        self.assertIn("- The other %d trials have no archived study page up to 2023-08-03: %s "
                      "(WashU-led), %d SWOG-led and %d NCI-linked, all first submitted on or after "
                      "%s." % (len(self.no_page), listing(washu), kinds.count("swog"),
                               kinds.count("nci"), first), md)
        self.assertTrue(all(d[n]["submitted"] >= first for n in self.r["order"]
                            if n in self.no_page))
        self.assertTrue(all(n in self.with_page for n in self.r["order"]
                            if d[n]["submitted"] < first))
        self.assertIn("all first submitted on or after %s, so every trial first submitted before "
                      "that date was read." % first, self.flat)
        gained = self.r["described"]["gained_before_cutoff"]
        self.assertIn("- %d trials lack the sentence on their oldest page and carry it on their "
                      "last page by 2023-08-03: %s." % (len(gained), listing(gained)), md)
        self.assertIn("Every trial with an archived study page had a usable one.", md)

    def test_what_it_means(self):
        flat, d = self.flat, self.d
        nct = "NCT04989283"
        self.assertEqual(d[nct]["pages"]["oldest"], ["20210804", "sentence"])
        self.assertEqual(d[nct]["submitted"], "2021-08-03")
        self.assertIn("An NCI-led trial (NCT04989283) carried it the day after its first "
                      "submission in August 2021", flat)
        swog = [x for x in table_rows() if x["lead_sponsor"] == SWOG]
        self.assertEqual(len(swog), 25)
        self.assertFalse(any(x["stock"] for x in swog))
        self.assertIn("none of the 25 SWOG-led trials that carry it today has CTEP's stock consent "
                      "line", flat)

    def test_chain(self):
        held = sum(k for _, k, _ in CHAIN) + sum(1 for v in self.r["predictions"].values() if v)
        total = sum(n for _, _, n in CHAIN) + len(self.r["predictions"])
        self.assertEqual((held, total), (21, 28))
        self.assertIn("%d of %d predictions held" % (held, total), self.flat)
        for name, k, n in CHAIN:
            self.assertIn("%s %d of %d" % (name, k, n), self.flat)

    def test_timing_hashes_and_wording(self):
        md = self.md
        self.assertIn(self.r["fetched_utc"], md)
        self.assertIn("commit 0500b7c", md)
        self.assertIn("at the first poll", md)
        self.assertIn("not yet checked by a person", self.flat)
        for digest in RUN_SHA256.values():
            self.assertIn(digest, md)
        self.assertIn("their 19 tests passed", md)
        self.assertEqual(re.findall(r"by\s+hand|by\s+eye|hand[- ]check", md, re.I), [])
        self.assertNotIn("MIT", md)
        self.assertNotIn("@", md)


if __name__ == "__main__":
    unittest.main()
