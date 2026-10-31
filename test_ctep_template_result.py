"""Tests for CTEP-TEMPLATE-RESULT.md (no network). Apache-2.0.

Re-grades the saved per-capture table and per-file marks with ctep_template 0.1.0, rebuilds the
run's table, file list and printed result, and checks every figure the note quotes. The run and the
note were made by AI agents working for MV2; no person has checked them yet.
"""

import csv
import datetime
import hashlib
import io
import json
import os
import re
import tempfile
import unittest

import ctep_template as ct

HERE = os.path.dirname(os.path.abspath(__file__))
RESULT = os.path.join(HERE, "results", "ctep-template")

# The sha256 printed in the sealed run (ctep-template-v2).
RUN_SHA256 = {
    "ctep_template.py": "9c49174bb2c868c788e3b1aeb03d5ddab5ede44bc00b2c0abe02979223464688",
    "test_ctep_template.py": "41cec9c40d8d25f4aef13a130e3426c191e1ab86c31b0e10155e29c643b7f7ad",
}
ROW_KEYS = ("digest", "first_ts", "last_ts", "captures", "original", "downloaded")
SHARED_DATE = "March 16, 2012"
GENERIC = "Generic Protocol Template for Cancer Treatment Trial"
ORGAN = "Organ Dysfunction Protocol Template"


def raw(name):
    with open(os.path.join(RESULT, name), "rb") as f:
        return f.read()


def text(name):
    return raw(name).decode("utf-8")


def plain(x):
    return json.loads(json.dumps(x))


def saved():
    return json.loads(text("result.json"))


def table():
    """The captures as ctep_template.captures() returned them, from the saved table."""
    rows = list(csv.DictReader(io.StringIO(text("ctep-template-captures.csv"))))
    return [{"ts": r["ts"], "original": r["original"], "digest": r["digest"],
             "fetchable": r["fetchable"] == "True"} for r in rows]


def files_of(result):
    """The per-file marks keyed by digest, as main() held them before file_rows()."""
    return {f["digest"]: {k: v for k, v in f.items() if k not in ROW_KEYS}
            for f in result["files"]}


def ymd(ts):
    return "%s-%s-%s" % (ts[:4], ts[4:6], ts[6:8])


def family(f):
    return ORGAN if "organ_dysfunction" in f["original"].lower() else GENERIC


def own_dates(f):
    return [d for d in f["version_dates"] if d != SHARED_DATE]


def parse(d):
    return datetime.datetime.strptime(d, "%B %d, %Y").date()


class SavedRunTests(unittest.TestCase):
    def test_code_is_what_ran(self):
        for name, digest in RUN_SHA256.items():
            with open(os.path.join(HERE, name), "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), digest, name)
        self.assertEqual(saved()["script_sha256"], RUN_SHA256["ctep_template.py"])

    def test_table_rebuilds_byte_for_byte(self):
        out = os.path.join(tempfile.mkdtemp(), "captures.csv")
        ct.write_captures(out, table(), files_of(saved()))
        with open(out, "rb") as f:
            self.assertEqual(f.read(), raw("ctep-template-captures.csv"))

    def test_plan_and_file_rows(self):
        r = saved()
        caps = table()
        todo = ct.plan(caps)
        self.assertEqual(len(caps), r["template_captures"])
        self.assertEqual(len(todo), r["distinct_files"])
        self.assertEqual(plain(ct.file_rows(todo, caps, files_of(r))), r["files"])

    def test_grade_follows_from_the_table(self):
        r = saved()
        g = plain(ct.grade(table(), files_of(r), r["live"]))
        for k, v in g.pop("gates").items():
            self.assertEqual(r["gates"][k], v, k)
        for k, v in g.items():
            self.assertEqual(r[k], v, k)
        self.assertEqual(ct.result_text(r), text("result.txt").rstrip("\n"))

    def test_saved_status(self):
        r = saved()
        self.assertEqual(r["status"], "graded")
        self.assertEqual(sorted(r["gates"]), ["G1_live_control", "G2_usable", "G3_both_sides",
                                              "G4_bracket_narrow", "P0_prereg_public"])
        self.assertTrue(all(r["gates"].values()), r["gates"])
        self.assertEqual(r["polls"], 1)
        self.assertEqual(r["predictions"], {"T1": True, "T2": True, "T3": True, "T4": True})
        self.assertEqual(r["download_errors"], [])
        self.assertEqual(r["downloaded"], r["distinct_files"])
        self.assertTrue(all(f["digest_match"] for f in r["files"]))


class NoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = saved()
        cls.md = text("CTEP-TEMPLATE-RESULT.md")
        cls.files = cls.r["files"]
        cls.with_s = [f for f in cls.files if f["sentence"]]
        cls.without = [f for f in cls.files if not f["sentence"]]

    def test_in_short(self):
        r, md = self.r, self.md
        self.assertTrue(all(f["usable"] for f in self.files))
        first = min(f["first_ts"] for f in self.files)
        last = max(f["last_ts"] for f in self.files)
        self.assertIn("- %d distinct template files (%d archived captures, %s to %s) were "
                      "downloaded, every one matched the archive's digest, and every one has the "
                      "stock consent line." % (len(self.files), r["template_captures"],
                                               ymd(first), ymd(last)), md)
        self.assertEqual(max(f["last_ts"] for f in self.without), r["last_without"])
        self.assertEqual(min(f["first_ts"] for f in self.with_s), r["first_with"])
        self.assertIn("- %d files (%d captures) do not have the sentence; the last of them was "
                      "captured on %s." % (len(self.without),
                                           sum(f["captures"] for f in self.without),
                                           ymd(r["last_without"])), md)
        self.assertIn("- %d files (%d captures) have it; the first was captured on %s, %d days "
                      "later." % (len(self.with_s), sum(f["captures"] for f in self.with_s),
                                  ymd(r["first_with"]), r["bracket_days"]), md)
        self.assertEqual(r["without_after_first_with"], [])
        self.assertIn("is not in any archived copy of CTEP's protocol templates up to %s, and is "
                      "in every copy from %s on." % (ymd(r["last_without"]),
                                                     ymd(r["first_with"])), md)
        self.assertIn("No capture without the sentence appears after %s." % ymd(r["first_with"]),
                      md)
        self.assertIn("**All four predictions hold.**", md)

    def test_gates(self):
        r, md = self.r, self.md
        self.assertEqual(r["live_source"], "direct")
        self.assertIn("fetched directly; sha256 begins %s" % r["live"]["sha256"][:12], md)
        newest = max(self.files, key=lambda f: f["last_ts"])
        self.assertEqual(newest["sha256"], r["live"]["sha256"])
        self.assertIn("byte for byte the Internet Archive's copy of %s" % ymd(newest["first_ts"]),
                      md)
        self.assertIn("G2: %d usable files (at least %d needed)" % (r["usable_files"],
                                                                   ct.MIN_USABLE), md)
        self.assertIn("G4: the bracket is %d days (at most %d allowed)" % (r["bracket_days"],
                                                                          ct.MAX_BRACKET_DAYS), md)
        cdx = [r["cdx"][p] for p in ct.PREFIXES]
        self.assertTrue(all(c["complete"] for c in cdx))
        self.assertIn("The two CDX prefixes returned {:,} and {:,} rows, both complete; no "
                      "download failed.".format(cdx[0]["rows"], cdx[1]["rows"]), md)

    def test_predictions(self):
        r, md = self.r, self.md
        p = r["predictions"]
        for t, name in (("T1", "T1 (main)"), ("T2", "T2"), ("T3", "T3"), ("T4", "T4")):
            self.assertIn("- **%s: %s.**" % (name, "holds" if p[t] else "fails"), md)
        self.assertIn("The last capture without the sentence is %s (on or after %s needed) and the "
                      "first with it is %s (on or before %s needed)." % (
                          ymd(r["last_without"]), ymd(ct.T1_EARLIEST), ymd(r["first_with"]),
                          ymd(ct.T1_LATEST)), md)
        self.assertFalse(any(f["clause"] for f in self.files) or r["live"]["clause"])
        self.assertIn("is in none of the %d files and not in today's template" % len(self.files),
                      md)
        self.assertTrue(all(f["adjacent"] for f in self.with_s))
        self.assertIn("In all %d files with the sentence it starts within %d characters after the "
                      "stock line." % (len(self.with_s), ct.ADJACENT_CHARS), md)
        self.assertFalse(any(f["lar_near"] for f in self.without))
        self.assertIn("None of the %d files without the sentence names" % len(self.without), md)
        self.assertIn("or a LAR, within %d characters after the stock line." % ct.NEAR_CHARS, md)

    def test_version_dates(self):
        md = self.md
        shared = [f for f in self.files if SHARED_DATE in f["version_dates"]]
        none = [f for f in self.files if not f["version_dates"]]
        self.assertEqual(len(shared) + len(none), len(self.files))
        self.assertEqual({f["first_ts"][:4] for f in none}, {"2011"})
        self.assertIn("%s is in %d of the %d files (the %s captured in 2011 print none)" % (
            SHARED_DATE, len(shared), len(self.files), {2: "two"}[len(none)]), md)
        for f in self.files:
            own = own_dates(f)
            self.assertLessEqual(len(own), 1, f["digest"])
            if own:
                self.assertLess(parse(own[0]), ct.day(f["first_ts"]), f["digest"])
        last_without = {}
        for f in sorted(self.without, key=lambda f: f["first_ts"]):
            if own_dates(f):
                last_without[family(f)] = own_dates(f)[0]
        self.assertTrue(all(own_dates(f) for f in self.with_s))
        self.assertIn("- Last versions without the sentence: %s (%s) and %s (%s)." % (
            last_without[GENERIC], GENERIC, last_without[ORGAN], ORGAN), md)
        first_with = {}
        for f in sorted(self.with_s, key=lambda f: f["first_ts"], reverse=True):
            first_with[family(f)] = own_dates(f)[0]
        self.assertEqual(first_with[GENERIC], first_with[ORGAN])
        self.assertIn("- First version with it: %s, in both templates." % first_with[GENERIC], md)
        self.assertIn("added in a version dated after %s and no later than %s." % (
            max(last_without.values(), key=parse), first_with[GENERIC]), md)

    def test_washu_section(self):
        for nct in ("NCT04462328", "NCT04852328", "NCT05521984"):
            self.assertIn(nct, self.md)
        self.assertIn("results/washu-switch", self.md)

    def test_timing_hashes_and_wording(self):
        md = self.md
        self.assertIn(self.r["fetched_utc"], md)
        self.assertIn("commit 219a278", md)
        self.assertIn("at its first poll", md)
        self.assertIn("not yet checked by a person", re.sub(r"\s+", " ", md))
        for digest in RUN_SHA256.values():
            self.assertIn(digest, md)
        self.assertIn("their 18 tests passed", md)
        self.assertEqual(re.findall(r"by\s+hand|by\s+eye|hand[- ]check", md, re.I), [])
        self.assertNotIn("MIT", md)


if __name__ == "__main__":
    unittest.main()
