"""Tests for WASHU-HISTORY-RESULT.md (no network). Apache-2.0.

Rebuilds the printed result from the saved result.json with washu_history 0.1.0, re-runs its
grading on the saved marks, and checks every figure the note quotes. The run and the note were
made by AI agents working for MV2; no person has checked them yet.
"""

import csv
import hashlib
import io
import json
import os
import re
import unittest

import washu_history as wh

HERE = os.path.dirname(os.path.abspath(__file__))
RESULT = os.path.join(HERE, "results", "washu-history")

# The sha256 printed in the sealed run (washu-history-v1).
RUN_SHA256 = {
    "washu_history.py": "76fd50842103c79b22ea5d143ca4219a2ac151e31a788ceabfdb8364d75b78cc",
    "test_washu_history.py": "aee3c3c1a464e7a56108f7fbc92954fe86a1383656c2ecb6081a5ebea7c03e20",
}


def text(name):
    with open(os.path.join(RESULT, name), "rb") as f:
        return f.read().decode("utf-8")


def saved():
    return json.loads(text("result.json"))


def read_ids(r):
    """Trials whose index queries were made (the rest were never reached)."""
    return [n for n, c in r["cdx"].items() if c["rows"]]


class WashuHistoryNoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = saved()
        cls.md = text("WASHU-HISTORY-RESULT.md")
        cls.flat = re.sub(r"\s+", " ", cls.md)

    def test_code_is_what_ran(self):
        for name, digest in RUN_SHA256.items():
            with open(os.path.join(HERE, name), "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), digest, name)
            self.assertIn(digest, self.md)
        self.assertEqual(self.r["script_sha256"], RUN_SHA256["washu_history.py"])
        self.assertIn("their 20 tests passed", self.md)

    def test_printed_result_rebuilds(self):
        self.assertEqual(wh.result_text(self.r), text("result.txt").rstrip("\n"))

    def test_status_and_gates(self):
        r, md = self.r, self.md
        self.assertEqual(r["status"], "gate failed; not graded")
        self.assertIsNone(r["predictions"])
        self.assertEqual(r["gates"], {"P0_prereg_public": True, "A1_table": True,
                                      "A2_coverage": True, "A3_complete": False})
        self.assertEqual(r["polls"], 1)
        self.assertIn("**Gate A3 failed, so nothing is graded: H1, H2 and H3 stay open.**", md)
        self.assertIn(r["fetched_utc"], md)
        self.assertIn("commit f9ae5eb", md)
        self.assertIn("at its first poll", md)

    def test_how_far_it_got(self):
        r, md = self.r, self.md
        done = read_ids(r)
        self.assertEqual(wh.DEADLINE_SECONDS, 150 * 60)
        self.assertGreater(r["elapsed_seconds"], wh.DEADLINE_SECONDS)
        self.assertIn("- The run stopped reading at its 150-minute limit ({:,} seconds elapsed) after "
                      "{} of the {} trials.".format(r["elapsed_seconds"], len(done), r["trials"]),
                      md)
        # Trials are read in table order; every trial after the last one queried was skipped.
        order = list(r["cdx"])
        self.assertEqual(order[:len(done)], done)
        self.assertTrue(all(not r["cdx"][n]["rows"] for n in order[len(done):]))
        self.assertEqual(r["cdx_queries"], 2 * len(done))
        errors = [x for n in done for x in r["cdx"][n]["rows"] if isinstance(x, str)]
        self.assertEqual(len(errors), r["cdx_errors"])
        self.assertTrue(all("503" in e for e in errors))
        self.assertIn("- Those {} trials took {} Internet Archive index queries; {} were not "
                      "answered (HTTP 503), and {} of {} page downloads failed.".format(
                          len(done), r["cdx_queries"], r["cdx_errors"], r["download_errors"],
                          r["downloaded"] + r["download_errors"]), md)
        self.assertEqual(len(r["boundary"]), 9)
        self.assertFalse(any(n in done for n in r["boundary"]))
        self.assertEqual(r["h2_graded"], [])
        self.assertIn("- None of the {} boundary trials".format(len(r["boundary"])), md)
        for n in wh.EARLY_SENTENCE:
            self.assertIn(n, md)
        self.assertIn("about %d seconds per trial on average" % round(r["elapsed_seconds"]
                                                                      / len(done)), md)

    def test_what_was_read(self):
        r, md = self.r, self.md
        pre = r["pre_pages"]
        self.assertEqual(len(pre), r["pre_usable"])
        self.assertEqual(r["pre_with_sentence"], [])
        self.assertFalse(any(w in ("sentence", "both") for _, w in pre.values()))
        self.assertIn("- %d trials had a usable page captured on or before 2022-07-09; none of the "
                      "%d carries the sentence." % (len(pre), len(pre)), md)
        self.assertEqual(wh.CUTOFF_DAY, "20220709")
        self.assertEqual(r["clause_today"], r["clause_kept"])
        other = r["pre_usable"] - r["clause_today"]
        self.assertEqual(r["described"]["pre_to_today"],
                         {"clause->clause": r["clause_today"], "neither->neither": other})
        self.assertIn("- All %d of them that carry WashU's clause today carried it on that page "
                      "too; the other %d carry neither wording, then and now." % (
                          r["clause_today"], other), md)
        ids = sorted(pre)
        self.assertTrue(all(n < "NCT04" for n in ids))
        self.assertIn("- Every one of the %d was registered before NCT04 (%s to %s)" % (
            len(ids), ids[0], ids[-1]), md)

    def test_pages_table(self):
        rows = list(csv.DictReader(io.StringIO(text("washu-history-pages.csv"))))
        self.assertEqual(len(rows), self.r["downloaded"] + self.r["download_errors"])
        self.assertEqual(sum(1 for x in rows if x["error"]), self.r["download_errors"])
        self.assertEqual({x["role"] for x in rows}, {"pre"})
        self.assertFalse(any(x["sentence"] == "True" for x in rows))

    def test_wording(self):
        self.assertIn("not yet checked by a person", self.flat)
        self.assertIn("results/sentence-origin", self.md)
        self.assertEqual(re.findall(r"by\s+hand|by\s+eye|hand[- ]check", self.md, re.I), [])
        self.assertNotIn("MIT", self.md)


if __name__ == "__main__":
    unittest.main()
