"""Tests for WASHU-SWITCH-RESULT.md (no network). Apache-2.0.

Re-grades the saved per-trial table with washu_switch 0.1.0, checks it against the run's saved
result, and checks every figure the note quotes. The run and the note were made by AI agents
working for MV2; no person has checked them yet.
"""

import hashlib
import json
import os
import re
import unittest

import washu_switch as ws

HERE = os.path.dirname(os.path.abspath(__file__))
RESULT = os.path.join(HERE, "results", "washu-switch")

# The sha256 printed in the sealed run (washu-switch-v1).
RUN_SHA256 = {
    "washu_switch.py": "069ddbe740aa8dca5f302dbd9a1ca2c3435b03c103c80f4d2f78b8eedfe2807d",
    "test_washu_switch.py": "afc97784ea3defec9d69b402be40922f25da7ae4d913b9e1f088c41b015ad2e7",
}
COLS = ["nct_id", "period", "start_year", "seen", "nci_linked", "path_2026_10_16", "fetched",
        "clause", "sentence"]
FLAGS = ("seen", "nci_linked", "path_2026_10_16", "fetched", "clause", "sentence")


def raw(name):
    with open(os.path.join(RESULT, name), "rb") as f:
        return f.read()


def text(name):
    return raw(name).decode("utf-8")


def plain(x):
    return json.loads(json.dumps(x))


def recs():
    header, rows = ws.read_csv(raw("washu-switch-trials.csv"))
    out = []
    for r in rows:
        r = dict(r)
        for k in FLAGS:
            r[k] = ws.truthy(r[k])
        out.append(r)
    return header, out


def wording_counts(rows):
    return (sum(1 for r in rows if r["clause"]), sum(1 for r in rows if r["sentence"]),
            sum(1 for r in rows if not r["clause"] and not r["sentence"]))


class SavedRunTests(unittest.TestCase):
    def test_code_is_what_ran(self):
        for name, digest in RUN_SHA256.items():
            with open(os.path.join(HERE, name), "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), digest, name)
        self.assertEqual(json.loads(text("result.json"))["script_sha256"],
                         RUN_SHA256["washu_switch.py"])

    def test_table(self):
        header, rows = recs()
        self.assertEqual(header, COLS)
        self.assertEqual(len(rows), ws.WASHU_COUNTS[1])
        self.assertEqual([r["nct_id"] for r in rows], sorted(r["nct_id"] for r in rows))
        self.assertTrue(all(r["fetched"] for r in rows))
        self.assertEqual({r["nct_id"] for r in rows if r["seen"]}, set(ws.SEEN))
        self.assertEqual(sum(1 for r in rows if r["path_2026_10_16"]), ws.WASHU_COUNTS[0])
        self.assertTrue(all(r["period"] == ws.period(r["nct_id"]) for r in rows))

    def test_grade_follows_from_the_table(self):
        _, rows = recs()
        saved = json.loads(text("result.json"))
        g = plain(ws.grade(rows))
        for k in ("unseen", "predictions", "diff_clause_early_minus_late"):
            self.assertEqual(g[k], saved[k], k)
        for k, v in g["gates"].items():
            self.assertEqual(saved["gates"][k], v, k)
        self.assertEqual(plain(ws.described(rows)), saved["described"])
        self.assertEqual(saved["fetched"], len(rows))
        self.assertEqual(ws.result_text(saved), text("result.txt").rstrip("\n"))

    def test_saved_status(self):
        saved = json.loads(text("result.json"))
        self.assertEqual(saved["status"], "graded")
        self.assertTrue(all(saved["gates"].values()), saved["gates"])
        self.assertEqual(sorted(saved["gates"]), ["P0_prereg_public", "S1_table",
                                                  "S2_washu_counts", "S3_seen", "S4_fetched",
                                                  "S5_enough"])
        self.assertEqual(saved["polls"], 1)
        self.assertEqual(saved["predictions"], {"W1": True, "W2": False, "W3": False,
                                                "W4": True, "W5": True})


class NoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = json.loads(text("result.json"))
        cls.md = text("WASHU-SWITCH-RESULT.md")
        cls.rows = recs()[1]
        cls.e, cls.l = cls.r["unseen"]["early"], cls.r["unseen"]["late"]

    def share(self, t, w):
        k, _, ci = t[w]
        return "%d (%.1f%%; 95%% interval %.2f-%.2f%%)" % (k, 100 * k / t["trials"],
                                                          100 * ci[0], 100 * ci[1])

    def test_in_short(self):
        e, l = self.e, self.l
        self.assertIn("- Before NCT06 (%d trials): the WashU clause in %s, the sentence in %s." % (
            e["trials"], self.share(e, "clause"), self.share(e, "sentence")), self.md)
        self.assertIn("- From NCT06 on (%d trials): the sentence in %s, the clause in %s." % (
            l["trials"], self.share(l, "sentence"), self.share(l, "clause")), self.md)
        self.assertIn("Among the %d WashU-led trials not read before:" % (
            e["trials"] + l["trials"]), self.md)
        self.assertEqual((e["both_wordings"], l["both_wordings"]), (0, 0))
        self.assertEqual(sum(1 for r in self.rows if r["clause"] and r["sentence"]), 0)
        self.assertIn("No trial carries both wordings.", self.md)

    def test_predictions(self):
        p = self.r["predictions"]
        for w, name in (("W1", "W1 (main)"), ("W2", "W2"), ("W3", "W3"), ("W4", "W4"),
                        ("W5", "W5")):
            self.assertIn("- **%s: %s.**" % (name, "holds" if p[w] else "fails"), self.md)
        self.assertEqual(sum(p.values()), 3)
        self.assertIn("**Three of five predictions hold.**", self.md)

    def test_prediction_lines(self):
        e, l = self.e, self.l
        ke, ne, kl, nl = e["clause"][0], e["trials"], l["clause"][0], l["trials"]
        d = self.r["diff_clause_early_minus_late"]
        self.assertIn("is %.1f percentage points (Newcombe 95%% interval %.2f to %.2f points); "
                      "needed at least %d" % (100 * (ke / ne - kl / nl), 100 * d[1], 100 * d[2],
                                              round(100 * ws.W1_MIN_DIFF)), self.md)
        sl = l["sentence"][0]
        need2 = min(k for k in range(nl + 1) if k / nl >= ws.W2_MIN_LATE_SENTENCE)
        self.assertIn("The sentence is in %d of %d late trials (%.1f%%); needed at least %d%% "
                      "(%d of %d)." % (sl, nl, 100 * sl / nl, round(100 * ws.W2_MIN_LATE_SENTENCE),
                                       need2, nl), self.md)
        max3 = max(k for k in range(nl + 1) if k / nl <= ws.W3_MAX_LATE_CLAUSE)
        self.assertIn("The clause is in %d of %d late trials (%.1f%%); needed at most %d%% "
                      "(%d of %d)." % (kl, nl, 100 * kl / nl, round(100 * ws.W3_MAX_LATE_CLAUSE),
                                       max3, nl), self.md)
        self.assertEqual((need2 - sl, kl - max3), (1, 1))
        self.assertIn("each miss their bound by one trial", self.md)
        se = e["sentence"][0]
        self.assertIn("The sentence is in %d of %d early trials (%.1f%%); needed at most %d%%." % (
            se, ne, 100 * se / ne, round(100 * ws.W4_MAX_EARLY_SENTENCE)), self.md)
        self.assertIn("The clause is in %d of %d early trials (%.1f%%); needed at least %d%%." % (
            ke, ne, 100 * ke / ne, round(100 * ws.W5_MIN_EARLY_CLAUSE)), self.md)

    def test_gate_figures(self):
        self.assertIn("reproduce %d naming a path of %d" % ws.WASHU_COUNTS, self.md)
        self.assertIn("has its {:,} rows".format(ws.TABLE_ROWS), self.md)
        self.assertIn("the API returned %d of %d" % (self.r["fetched"], len(self.rows)), self.md)
        self.assertIn("S5: %d early and %d late unseen trials" % (self.e["trials"],
                                                                  self.l["trials"]), self.md)
        self.assertIn("sha256 begins %s" % self.r["sponsor_sha256"][:12], self.md)
        self.assertIn("commit %s" % ws.SPONSOR_COMMIT[:7], self.md)

    def test_missed_check(self):
        unseen = [r for r in self.rows if not r["seen"]]
        for period, label, n in (("late", "late", self.l["trials"]),
                                 ("early", "early", self.e["trials"])):
            no_path = [r for r in unseen if r["period"] == period and not r["path_2026_10_16"]]
            self.assertTrue(all(not r["clause"] and not r["sentence"] for r in no_path))
            self.assertIn("%d of the %d %s trials" % (len(no_path), n, label), self.md)
        path = [r for r in unseen if r["path_2026_10_16"]]
        early = [r for r in path if r["period"] == "early"]
        late = [r for r in path if r["period"] == "late"]
        c, s, _ = wording_counts(early)
        n = len(early)
        self.assertIn("- Before NCT06: the clause in %d of %d (%.1f%%), the sentence in %d of %d "
                      "(%.1f%%)." % (c, n, 100 * c / n, s, n, 100 * s / n), self.md)
        c, s, _ = wording_counts(late)
        n = len(late)
        self.assertIn("- From NCT06 on: the sentence in %d of %d (%.1f%%), the clause in %d of %d "
                      "(%.1f%%)." % (s, n, 100 * s / n, c, n, 100 * c / n), self.md)
        self.assertEqual(c, self.l["clause"][0])

    def test_switch_timing(self):
        d = self.r["described"]
        self.assertIn("The first trial with the sentence is %s and the last with the clause is %s; "
                      "%d fetched WashU-led trials from one to the other" % (
                          d["first_sentence_id"], d["last_clause_id"], d["ids_in_overlap"]),
                      self.md)
        last = d["last_clause_id"]
        late = [r for r in self.rows if not r["seen"] and r["period"] == "late"
                and r["path_2026_10_16"]]
        upto = [r for r in late if r["nct_id"] <= last]
        after = [r for r in late if r["nct_id"] > last]
        c, s, x = wording_counts(upto)
        c2, s2, x2 = wording_counts(after)
        self.assertEqual(c2, 0)
        self.assertIn("the %d up to %s split %d clause, %d sentence and %d neither; of the %d "
                      "after it, %d carry the sentence and %d neither." % (
                          len(upto), last, c, s, x, len(after), s2, x2), self.md)
        seen = [r for r in self.rows if r["seen"]]
        old = [r for r in seen if r["period"] == "early"]
        new = [r for r in seen if r["period"] == "late"]
        self.assertTrue(all(r["clause"] and not r["sentence"] for r in old))
        self.assertTrue(all(r["sentence"] and not r["clause"] for r in new))
        self.assertIn("The %d trials read before: clause %d, sentence %d (all %d before NCT06 with "
                      "the clause, all %d from NCT06 on with the sentence)" % (
                          len(seen), d["seen"]["clause"][0], d["seen"]["sentence"][0],
                          len(old), len(new)), self.md)
        n = d["nci_linked"]
        self.assertIn("The %d WashU-led trials that are also NCI-linked: clause %d, sentence %d, "
                      "neither %d." % (n["trials"], n["clause"][0], n["sentence"][0],
                                       n["neither_wording"]), self.md)
        for nct in ("NCT04462328", "NCT04852328", "NCT05521984"):
            r = [x for x in self.rows if x["nct_id"] == nct][0]
            self.assertTrue(r["sentence"] and r["period"] == "early", nct)
        for nct in ("NCT06063564", "NCT06648434"):
            r = [x for x in self.rows if x["nct_id"] == nct][0]
            self.assertTrue(r["clause"] and r["period"] == "late", nct)
        self.assertEqual(sum(1 for r in self.rows if r["clause"] and r["period"] == "late"), 6)

    def test_prefix_table(self):
        self.assertIn("All %d fetched trials (seen included) by NCT prefix:" % len(self.rows),
                      self.md)
        for p, t in self.r["described"]["by_prefix"].items():
            self.assertIn("| %s | %d | %d | %d | %d |" % (
                p, t["trials"], t["clause"][0], t["sentence"][0], t["neither_wording"]), self.md)

    def test_timing_hashes_and_wording(self):
        self.assertIn(self.r["fetched_utc"], self.md)
        self.assertIn("commit f7944ec", self.md)
        self.assertIn("at its first poll", self.md)
        self.assertIn("not yet checked by a person", self.md)
        for digest in RUN_SHA256.values():
            self.assertIn(digest, self.md)
        self.assertIn("their 15 tests passed", self.md)
        self.assertEqual(re.findall(r"by\s+hand|by\s+eye|hand[- ]check", self.md, re.I), [])
        self.assertNotIn("MIT", self.md)


if __name__ == "__main__":
    unittest.main()
