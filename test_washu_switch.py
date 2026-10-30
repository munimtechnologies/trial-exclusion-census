"""Tests for washu_switch (no network). Apache-2.0. Made by MV2 of Munim, Inc. with AI agents."""

import csv
import io
import json
import os
import tempfile
import unittest

import washu_switch as ws

CLAUSE_TEXT = ("Inclusion Criteria:\n\n* Ability to understand and willingness to sign an IRB "
               "approved written informed consent document \\(or that of legally authorized "
               "representative, if applicable\\).\n\nExclusion Criteria:\n\n* None")
SENTENCE_TEXT = ("Inclusion Criteria:\n\n* Ability to understand and willingness to sign an IRB "
                 "approved written informed consent document. Legally authorized\nrepresentatives "
                 "may sign and give informed consent on behalf of study participants.")
PLAIN_TEXT = "Inclusion Criteria:\n\n* Ability to understand and willingness to sign consent."


def row(nct, path, nci, washu):
    return {"nct_id": nct, "start_year": "20%s" % nct[4:6], "stock_exact": "True",
            "adult_only": "True", "adult_path": str(path), "lead_sponsor": "X",
            "lead_class": "OTHER", "nci_linked": str(nci), "washu_led": str(washu)}


def table_bytes(rows):
    f = io.StringIO()
    w = csv.writer(f, lineterminator="\r\n")
    w.writerow(ws.SPONSOR_HEADER)
    for r in rows:
        w.writerow([r[h] for h in ws.SPONSOR_HEADER])
    return f.getvalue().encode("utf-8")


def synthetic():
    """5,436 trials with the published WashU counts and the 20 seen ids as WashU-only paths."""
    rows = [row(i, True, False, True) for i in ws.SEEN]
    n = 0

    def nid(late):
        nonlocal n
        n += 1
        return "NCT%08d" % ((6100000 if late else 1000000) + n)
    for i in range(127):          # WashU-only naming a path: 60 early, 67 late
        rows.append(row(nid(i >= 60), True, False, True))
    for i in range(53):           # WashU-only naming none: all early
        rows.append(row(nid(False), False, False, True))
    for i in range(24):           # both NCI-linked and WashU-led; 18 name a path
        rows.append(row(nid(i % 2 == 0), i < 18, True, True))
    for i in range(1546):
        rows.append(row(nid(False), i < 260, True, False))
    for i in range(3666):
        rows.append(row(nid(False), i < 241, False, False))
    return rows


class FakeApi:
    """Late ids carry the sentence, early ids naming a path carry the clause, others neither."""

    def __init__(self, rows, drop=()):
        self.paths = {r["nct_id"] for r in rows if r["adult_path"] == "True"}
        self.drop = set(drop)
        self.calls = 0

    def __call__(self, url):
        self.calls += 1
        ids = url.split("filter.ids=")[1].split("&")[0].replace("%2C", ",").split(",")
        out = []
        for i in ids:
            if i in self.drop:
                continue
            text = (SENTENCE_TEXT if i >= ws.CUTOFF else
                    CLAUSE_TEXT if i in self.paths else PLAIN_TEXT)
            out.append({"protocolSection": {"identificationModule": {"nctId": i},
                                            "eligibilityModule": {"eligibilityCriteria": text}}})
        return {"studies": out}


class Constants(unittest.TestCase):
    def test_preregistered_values(self):
        self.assertEqual(ws.CUTOFF, "NCT06000000")
        self.assertEqual((ws.MIN_FETCHED, ws.MIN_EARLY, ws.MIN_LATE), (218, 40, 15))
        self.assertEqual((ws.W1_MIN_DIFF, ws.W2_MIN_LATE_SENTENCE, ws.W3_MAX_LATE_CLAUSE,
                          ws.W4_MAX_EARLY_SENTENCE, ws.W5_MIN_EARLY_CLAUSE),
                         (0.40, 0.60, 0.10, 0.10, 0.50))
        self.assertEqual(ws.WASHU_COUNTS, (165, 224))
        self.assertEqual(ws.SPONSOR_COMMIT, "dfa820661d6c06ec4eddee5e0ce1513c069a4dc6")
        self.assertIn(ws.SPONSOR_COMMIT, ws.SPONSOR_URL)

    def test_seen_ids(self):
        self.assertEqual(len(set(ws.SEEN)), 20)
        self.assertEqual(sum(1 for i in ws.SEEN if i >= ws.CUTOFF), 7)
        self.assertEqual(list(ws.SEEN), sorted(ws.SEEN))


class Wordings(unittest.TestCase):
    def test_clause(self):
        self.assertEqual(ws.wordings(CLAUSE_TEXT), (True, False))
        self.assertEqual(ws.wordings("(or that of their legally authorized representative)"),
                         (True, False))
        self.assertEqual(ws.wordings("or that of a legally-authorized representative"),
                         (True, False))

    def test_sentence(self):
        self.assertEqual(ws.wordings(SENTENCE_TEXT), (False, True))
        self.assertEqual(ws.wordings("Parents/Legally authorized representatives may sign and "
                                     "give informed consent on behalf of study participants"),
                         (False, True))

    def test_neither(self):
        self.assertEqual(ws.wordings(PLAIN_TEXT), (False, False))
        self.assertEqual(ws.wordings("signed by the patient or a legally authorized "
                                     "representative"), (False, False))
        self.assertEqual(ws.wordings(""), (False, False))

    def test_period(self):
        self.assertEqual(ws.period("NCT05999999"), "early")
        self.assertEqual(ws.period("NCT06000000"), "late")


class TableGates(unittest.TestCase):
    def test_pass(self):
        header, rows = ws.read_csv(table_bytes(synthetic()))
        g, washu = ws.table_gates(header, rows)
        self.assertTrue(all(g.values()), g)
        self.assertEqual(len(washu), 224)

    def test_fail_on_counts_and_seen(self):
        rows = synthetic()
        rows[0]["adult_path"] = "False"
        header, back = ws.read_csv(table_bytes(rows))
        g, _ = ws.table_gates(header, back)
        self.assertFalse(g["S2_washu_counts"])
        self.assertFalse(g["S3_seen"])


class Grading(unittest.TestCase):
    def recs(self, drop=()):
        rows = synthetic()
        header, back = ws.read_csv(table_bytes(rows))
        _, washu = ws.table_gates(header, back)
        fake = FakeApi(rows, drop)
        studies = ws.fetch_studies([r["nct_id"] for r in washu], fetch=fake)
        self.assertEqual(fake.calls, 1)
        return ws.records(washu, studies)

    def test_all_hold_on_a_clean_switch(self):
        r = ws.grade(self.recs())
        self.assertTrue(all(r["gates"].values()), r["gates"])
        early, late = r["unseen"]["early"], r["unseen"]["late"]
        self.assertEqual(early["trials"], 60 + 53 + 12)
        self.assertEqual(late["trials"], 67 + 12)
        self.assertEqual(early["clause"][0], 60 + 9)   # odd both rows are early; 9 name a path
        self.assertEqual(late["sentence"][0], 79)
        self.assertEqual(r["predictions"], {"W1": True, "W2": True, "W3": True, "W4": True,
                                            "W5": True})

    def test_seen_left_out(self):
        recs = self.recs()
        r = ws.grade(recs)
        self.assertEqual(r["unseen"]["early"]["trials"] + r["unseen"]["late"]["trials"], 204)
        d = ws.described(recs)
        self.assertEqual(d["seen"]["trials"], 20)
        self.assertEqual(d["seen"]["clause"][0], 13)
        self.assertEqual(d["ids_in_overlap"], 0)

    def test_all_fail_when_no_switch(self):
        recs = self.recs()
        for x in recs:
            x["clause"], x["sentence"] = x["period"] == "late", x["period"] == "early"
        r = ws.grade(recs)
        self.assertEqual(r["predictions"], {"W1": False, "W2": False, "W3": False, "W4": False,
                                            "W5": False})

    def test_fetch_gate(self):
        recs = self.recs(drop=[r for r in ws.SEEN][:7])
        r = ws.grade(recs)
        self.assertFalse(r["gates"]["S4_fetched"])
        self.assertIsNone(r["predictions"])

    def test_newcombe_published_example(self):
        d, lo, hi = ws.newcombe(56, 70, 48, 80)
        self.assertAlmostEqual(d, 0.2, places=6)
        self.assertAlmostEqual(lo, 0.0524, places=4)
        self.assertAlmostEqual(hi, 0.3339, places=4)


class Main(unittest.TestCase):
    def run_main(self, public):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "washu_switch.py"), "rb") as f:
            script = f.read()
        rows = synthetic()
        table = table_bytes(rows)

        def fetch(url):
            if url.startswith(ws.SPONSOR_URL):
                return table
            if not public:
                raise OSError("404")
            if ws.PREREG_PATH in url:
                return b"# PREREG\nW1 ...\n"
            if ws.SCRIPT_PATH in url:
                return script.replace(b"\n", b"\r\n")
            raise OSError("unexpected " + url)
        out = tempfile.mkdtemp()
        sleeps = []
        code = ws.main(["--out-dir", out], fetch=fetch, fetch_api=FakeApi(rows),
                       sleep=sleeps.append)
        with open(os.path.join(out, "result.json"), encoding="utf-8") as f:
            return code, json.load(f), out, sleeps

    def test_graded_when_public(self):
        code, result, out, sleeps = self.run_main(True)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "graded")
        self.assertEqual(result["polls"], 1)
        self.assertEqual(sleeps, [])
        self.assertTrue(all(result["predictions"].values()))
        with open(os.path.join(out, "washu-switch-trials.csv"), encoding="utf-8") as f:
            self.assertEqual(len(f.read().splitlines()), 225)

    def test_nothing_fetched_when_not_public(self):
        code, result, _, sleeps = self.run_main(False)
        self.assertEqual(code, 2)
        self.assertFalse(result["gates"]["P0_prereg_public"])
        self.assertEqual(len(sleeps), ws.TRIES - 1)
        self.assertNotIn("fetched", result)


if __name__ == "__main__":
    unittest.main()
