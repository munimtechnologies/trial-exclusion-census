"""Tests for CONSENT-PERMISSION-RESULT.md (no network). Apache-2.0.

Rebuilds the key from the saved sample, re-grades the committed labels with consent_permission
0.1.0, re-runs the two checks on the unclear records and the wording count, and checks every
figure the note quotes. The run and the note were made by AI agents working for MV2; no person
has checked them yet.
"""

import hashlib
import json
import os
import re
import unittest

import consent_permission as cp
import grade_job as gj

HERE = os.path.dirname(os.path.abspath(__file__))
RESULT = os.path.join(HERE, "results", "consent-permission")

# The sha256 printed in the sealed runs (consent-permission-v1 and consent-permission-grade-v1).
RUN_SHA256 = {
    "consent_permission.py": "7674ee9f942d4182ed4a1090db3a33ae418d94fb7a57115487d518c37701c24f",
    "grade_job.py": "7f39453e6a0ac8a6227e652fbfbb0f090b9426d3b20b9facef8715f8228321b0",
    "test_grade_job.py": "6ebd85cf1b89b6bd572bc1e62e86e3e05fa6ce2346c487c81791adbdaf149463",
}
LABELS_SHA256 = "88af6bbc83c7f4fbaaa46b4123bc68406d704d329f749a441877bea1ae9072d7"
NAMES = (("nci", "NCI-linked"), ("washu", "WashU-led"), ("neither", "Neither"))
CLAUSE = "or that of legally authorized representative, if applicable"
SENTENCE = ("Legally authorized representatives may sign and give informed consent on behalf of "
            "study participants")


def raw(name):
    with open(os.path.join(RESULT, name), "rb") as f:
        return f.read()


def text(name):
    return raw(name).decode("utf-8")


def plain(x):
    return json.loads(json.dumps(x))


def key_rows():
    return cp.read_csv(raw("key.csv"))[1]


def labels():
    return cp.read_labels(raw("labels.csv"))


def regrade(change):
    """Grade again after change(group, row) -> new label (or None to keep it)."""
    header, rows = labels()
    group = {k["blind_id"]: k["group"] for k in key_rows()}
    new = []
    for r in rows:
        r = dict(r)
        r["label"] = change(group[r["blind_id"]], r) or r["label"]
        new.append(r)
    return cp.grade(key_rows(), header, new)


def owner_share(groups):
    """Owners' share of estimated permissions, from the counts (unrounded), as in PREREG.md R5."""
    m = cp.EXPECTED
    p = {g: groups[g]["adult_permission"] / groups[g]["read"] for g, _ in NAMES}
    owners = m["nci_linked"][0] * p["nci"] + (m["washu_led"][0] - m["both"][0]) * p["washu"]
    return owners / (owners + m["neither"][0] * p["neither"])


def blocks():
    """{blind id: its block of reading.txt}."""
    out, rid = {}, None
    for line in text("reading.txt").splitlines():
        if line.startswith("## R"):
            rid = line[3:].strip()
            out[rid] = []
        elif rid:
            out[rid].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


class SavedRunTests(unittest.TestCase):
    def test_code_is_what_ran(self):
        for name, digest in RUN_SHA256.items():
            with open(os.path.join(HERE, name), "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), digest, name)

    def test_sample(self):
        s = json.loads(text("sample.json"))
        self.assertEqual(s["version"], cp.__version__)
        self.assertEqual(s["sponsor_url"], cp.SPONSOR_URL)
        self.assertTrue(all(s["gates"].values()), s["gates"])
        self.assertEqual(plain(s["counts"]), plain({k: list(v) for k, v in cp.EXPECTED.items()
                                                    if k != "rows"}))
        self.assertEqual((s["fetched"], s["still_present"]), (100, 100))
        self.assertEqual(s["reading_sha256"], hashlib.sha256(raw("reading.txt")).hexdigest())

    def test_key_follows_from_the_sample(self):
        s = json.loads(text("sample.json"))
        ids = [i for g, _ in cp.GROUPS for i in s["sample"][g]]
        order = cp.blind_order(ids)
        key = sorted((order[i], i, g) for g, _ in cp.GROUPS for i in s["sample"][g])
        self.assertEqual(len(key), 100)
        self.assertEqual(gj.key_csv(key), raw("key.csv"))

    def test_gate(self):
        g = json.loads(text("gate.json"))
        self.assertEqual(g["status"], "graded")
        self.assertTrue(g["labels_public"] and g["reading_matches"] and g["script_matches"])
        self.assertTrue(all(g["sponsor_gates"].values()))
        self.assertEqual(g["labels_sha256"], LABELS_SHA256)
        self.assertEqual(g["public_sha256"], LABELS_SHA256)
        self.assertEqual(hashlib.sha256(raw("labels.csv")).hexdigest(), LABELS_SHA256)
        self.assertEqual(g["key_sha256"], hashlib.sha256(raw("key.csv")).hexdigest())
        self.assertEqual(g["script_sha256"], RUN_SHA256["consent_permission.py"])
        self.assertEqual(g["reading_sha256"], hashlib.sha256(raw("reading.txt")).hexdigest())

    def test_grade_follows_from_the_labels(self):
        header, rows = labels()
        result = plain(cp.grade(key_rows(), header, rows))
        result["labels_sha256"] = LABELS_SHA256
        saved = json.loads(text("grade.json"))
        self.assertEqual(result, saved)
        self.assertEqual(cp.grade_text(saved), text("grade.txt").rstrip("\n"))
        self.assertEqual(saved["predictions"], {"R1": True, "R2": True, "R3": True, "R4": True,
                                                "R5": True})


class NoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = json.loads(text("grade.json"))
        cls.md = text("CONSENT-PERMISSION-RESULT.md")

    def test_predictions(self):
        for p, name in (("R1", "R1 (main)"), ("R2", "R2"), ("R3", "R3"), ("R4", "R4"),
                        ("R5", "R5")):
            verdict = "holds" if self.g["predictions"][p] else "fails"
            self.assertIn("**%s: %s.**" % (name, verdict), self.md)
        self.assertIn("**All five predictions hold.**", self.md)

    def test_group_shares(self):
        for g, name in NAMES:
            c = self.g["groups"][g]
            k, n = c["adult_permission"], c["read"]
            self.assertIn("- %s: %d of %d (%.1f%%; 95%% interval %.1f-%.1f%%)" % (
                name, k, n, 100 * k / n, 100 * c["ci"][0], 100 * c["ci"][1]), self.md)
            self.assertIn("%s %.1f%%" % (name, 100 * k / n), self.md)

    def test_difference(self):
        a, x = self.g["groups"]["nci"], self.g["groups"]["neither"]
        self.assertEqual(a["read"], x["read"])
        d = self.g["diff_nci_minus_neither"]
        self.assertIn("is %.1f percentage points (Newcombe 95%% interval %.2f to %.2f points)" % (
            100 * (a["adult_permission"] - x["adult_permission"]) / a["read"],
            100 * d[1], 100 * d[2]), self.md)

    def test_estimate(self):
        e = self.g["estimated_permissions"]
        m = cp.EXPECTED
        self.assertIn("about %s of %s trials (%.1f%%)" % (e["total"], "{:,}".format(m["rows"]),
                                                        100 * e["of_all_trials"]), self.md)
        self.assertIn("hold %.1f%% of those" % (100 * e["owner_share"]), self.md)
        self.assertIn("hold %.1f%% of estimated real adult permissions" % (100 * e["owner_share"]),
                      self.md)
        self.assertAlmostEqual(owner_share(self.g["groups"]), e["owner_share"], places=4)
        owners_paths = m["nci_linked"][0] + m["washu_led"][0] - m["both"][0]
        self.assertIn("against %.1f%% of mentions" % (
            100 * owners_paths / (owners_paths + m["neither"][0])), self.md)
        self.assertIn("about %s of %s Neither trials (%.1f%%)" % (
            e["neither"], "{:,}".format(m["neither"][1]), 100 * e["neither_of_neither_trials"]),
            self.md)

    def test_label_table(self):
        for g, name in NAMES:
            c = self.g["groups"][g]
            self.assertIn("| %s | %d | %s |" % (name, c["read"], " | ".join(
                str(c["labels"][l]) for l in ("adult_permission", "physical_only", "minor_only",
                                              "unclear", "not_a_permission", "path_gone"))),
                self.md)
        x = self.g["groups"]["neither"]
        self.assertIn("(%d of %d) are routes for minors only" % (x["labels"]["minor_only"],
                                                                 x["read"]), self.md)

    def test_prohibitions(self):
        group = {k["blind_id"]: k["group"] for k in key_rows()}
        rows = [r for r in labels()[1] if r["reason"].startswith("prohibition")]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(group[r["blind_id"]] == "nci" and r["label"] == "not_a_permission"
                            and "guardian" in r["reason"] for r in rows))
        self.assertIn("Three NCI-linked records name a guardian only", self.md)

    def test_unclear_checks(self):
        header, rows = labels()
        self.assertEqual(sum(1 for r in rows if r["label"] == "unclear"), 15)
        best = regrade(lambda g, r: "adult_permission" if r["label"] == "unclear" else None)
        self.assertTrue(all(best["predictions"].values()))
        parts = []
        for g, name in NAMES:
            c = best["groups"][g]
            parts.append("%s %d of %d (%.1f%%)" % (name, c["adult_permission"], c["read"],
                                                   100 * c["adult_permission"] / c["read"]))
        self.assertIn("All 15 unclear records read as adult permissions: %s; owners hold %.1f%% "
                      "of the estimate. All five predictions hold." % (
                          ", ".join(parts), 100 * owner_share(best["groups"])), self.md)
        worst = regrade(lambda g, r: "adult_permission"
                        if r["label"] == "unclear" and g == "neither" else None)
        self.assertTrue(all(worst["predictions"].values()))
        self.assertGreater(worst["diff_nci_minus_neither"][1], 0)
        a, x = worst["groups"]["nci"], worst["groups"]["neither"]
        self.assertEqual(sum(1 for r in rows if r["label"] == "unclear"
                             and {k["blind_id"]: k["group"] for k in key_rows()}[r["blind_id"]]
                             == "neither"), 7)
        self.assertIn("Neither %d of %d (%.1f%%)" % (x["adult_permission"], x["read"],
                                                     100 * x["adult_permission"] / x["read"]),
                      self.md)
        self.assertIn("the gap is %.1f points with the interval's lower end still above 0; owners "
                      "hold %.1f%%. All five hold." % (
                          100 * (a["adult_permission"] - x["adult_permission"]) / a["read"],
                          100 * owner_share(worst["groups"])), self.md)

    def test_wording_seen_while_grading(self):
        b = blocks()
        self.assertEqual(len(b), 100)
        key = key_rows()
        washu = [k for k in key if k["group"] == "washu"]
        old = [k for k in washu if k["nct_id"] < "NCT06"]
        new = [k for k in washu if k["nct_id"] >= "NCT06"]
        self.assertEqual((len(old), len(new)), (13, 7))
        for k in old:
            self.assertIn(CLAUSE, b[k["blind_id"]], k)
            self.assertNotIn(SENTENCE, b[k["blind_id"]], k)
        for k in new:
            self.assertIn(SENTENCE, b[k["blind_id"]], k)
            self.assertNotIn(CLAUSE, b[k["blind_id"]], k)
        self.assertIn("all %d sampled WashU-led trials with ids before NCT06 carry the WashU "
                      "clause" % len(old), self.md)
        self.assertIn("all %d with ids from NCT06 on carry NCI's sentence" % len(new), self.md)
        self.assertIn('("%s")' % SENTENCE, self.md)
        self.assertIn('("%s")' % CLAUSE, self.md)
        neither = sum(1 for k in key if k["group"] == "neither" and CLAUSE in b[k["blind_id"]])
        nci = [k for k in key if k["group"] == "nci"]
        nci_sentence = sum(1 for k in nci if SENTENCE in b[k["blind_id"]])
        self.assertIn("%d Neither trials carry the WashU clause" % neither, self.md)
        self.assertIn("only %d of %d NCI-linked records carry NCI's sentence" % (
            nci_sentence, len(nci)), self.md)

    def test_timing_hashes_and_wording(self):
        s = json.loads(text("sample.json"))
        self.assertIn(s["started_utc"], self.md)
        self.assertIn("commit c628762", self.md)
        self.assertIn("commit 811c6bb", self.md)
        self.assertIn("not yet checked by a person", self.md)
        self.assertIn(LABELS_SHA256, self.md)
        self.assertIn(s["reading_sha256"][:12], self.md)
        for digest in RUN_SHA256.values():
            self.assertIn(digest, self.md)
        self.assertEqual(re.findall(r"by\s+hand|by\s+eye|hand[- ]check", self.md, re.I), [])
        self.assertNotIn("MIT", self.md)


if __name__ == "__main__":
    unittest.main()
