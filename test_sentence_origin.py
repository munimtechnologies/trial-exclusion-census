"""Tests for sentence_origin.py (no network). Apache-2.0.

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import io
import itertools
import json
import os
import tempfile
import unittest
import urllib.parse

import sentence_origin as so

SENT = ("Legally authorized representatives may sign and give informed consent on behalf of "
        "study participants.")
STOCK = "Ability to understand and the willingness to sign a written informed consent document."
COLS = ["nct_id", "submitted", "period", "group", "nci_linked", "washu_led", "lead_sponsor",
        "lead_class", "stock", "clause", "in_frame", "anchor", "searches"]


def html_page(nct, body, pad=2100):
    return ("<html><head><script>var x = 'Legally authorized representatives may sign and give "
            "informed consent';</script></head><body><h1>%s</h1><h2>Eligibility Criteria</h2>"
            "<p>%s</p><p>%s</p></body></html>" % (nct, body, "x " * pad)).encode("utf-8")


def make_rows():
    """A table like ctep-spread-trials.csv: 3 early WashU, 10 SWOG and 17 NCI pre/gap trials."""
    rows = []

    def add(n, period, group, lead, nci):
        rows.append({"nct_id": n, "submitted": "2021-01-01" if period == "pre" else
                     "2023-01-01" if period == "gap" else "2025-01-01", "period": period,
                     "group": group, "nci_linked": nci, "washu_led": group == "washu",
                     "lead_sponsor": lead, "lead_class": "OTHER", "stock": True, "clause": False,
                     "in_frame": True, "anchor": True, "searches": "1+2"})

    add("NCT04462328", "pre", "washu", "Washington University School of Medicine", False)
    add("NCT04852328", "pre", "washu", "Washington University School of Medicine", False)
    add("NCT05521984", "gap", "washu", "Washington University School of Medicine", False)
    for i in range(10):
        add("NCT0410%04d" % i, "pre" if i < 3 else "gap", "nci", "SWOG Cancer Research Network",
            True)
    for i in range(17):
        add("NCT0420%04d" % i, "pre" if i < 7 else "gap", "nci",
            "National Cancer Institute (NCI)", True)
    for i in range(117):
        add("NCT0700%04d" % i, "post", "nci", "National Cancer Institute (NCI)", True)
    return rows


def table_bytes(rows):
    f = io.StringIO()
    w = csv.writer(f, lineterminator="\n")
    w.writerow(COLS)
    for r in rows:
        w.writerow([r[c] for c in COLS])
    return f.getvalue().encode("utf-8")


def local_script():
    with open(so.__file__, "rb") as f:
        return f.read()


class FakeWeb:
    """GitHub raw files, the CDX index and archived pages, all in memory."""

    def __init__(self, rows, swog_from_start=True, prereg=True):
        self.rows = {r["nct_id"]: r for r in rows}
        self.table = table_bytes(rows)
        self.swog_from_start = swog_from_start
        self.prereg = prereg
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        if url.startswith(so.REPO_RAW):
            path = url[len(so.REPO_RAW):].split("?")[0]
            if path == so.PREREG_PATH and self.prereg:
                return b"# pre-registration\nS1 S2 S3 S4\n"
            if path == so.SCRIPT_PATH:
                return local_script()
            if path == so.TABLE_PATH:
                return self.table
            raise IOError("404 %s" % path)
        if url.startswith(so.CDX):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            assert q["to"] == [so.CUTOFF_EARLY] and q["filter"] == ["statuscode:200"]
            prefix = q["url"][0]
            nct = prefix.rsplit("/", 1)[1]
            out = [["timestamp", "original", "statuscode", "digest"]]
            if "/record/" not in prefix:
                orig = "https://clinicaltrials.gov/ct2/show/%s" % nct
                out += [["20200101000000", orig, "200", "A" + nct],
                        ["20200601000000", orig, "200", "A" + nct],
                        ["20230101000000", orig, "200", "B" + nct]]
            return json.dumps(out).encode("utf-8")
        if url.startswith("https://web.archive.org/web/"):
            ts = url.split("/web/")[1].split("id_")[0]
            nct = url.rsplit("/", 1)[1]
            swog = self.rows[nct]["lead_sponsor"].startswith("SWOG")
            with_s = ts.startswith("2023") or (swog and self.swog_from_start)
            return html_page(nct, STOCK + (" " + SENT if with_s else ""))
        raise IOError("unexpected %s" % url)


def run_main(web, clock=None):
    out = tempfile.mkdtemp()
    kw = {"fetch": web, "sleep": lambda s: None}
    if clock:
        kw["clock"] = clock
    code = so.main(["--out-dir", out], **kw)
    with open(os.path.join(out, "result.json"), encoding="utf-8") as f:
        result = json.load(f)
    with open(os.path.join(out, "result.txt"), encoding="utf-8") as f:
        text = f.read()
    return code, result, text, out


class ConstantsTests(unittest.TestCase):
    def test_pinned(self):
        self.assertEqual(so.__version__, "0.1.0")
        self.assertEqual((so.TABLE_ROWS, so.COHORT_SIZE, so.SWOG_IN_COHORT), (147, 30, 10))
        self.assertEqual(so.EARLY_WASHU, ("NCT04462328", "NCT04852328", "NCT05521984"))
        self.assertEqual((so.CUTOFF_PRE, so.CUTOFF_EARLY), ("20220709", "20230803"))
        self.assertEqual((so.TRIES, so.MIN_TEXT, so.MIN_USABLE_TRIALS, so.MIN_COMPLETE_TRIALS),
                         (3, 2000, 15, 27))
        self.assertEqual(so.DEADLINE_SECONDS, 200 * 60)
        self.assertEqual((so.S1_MIN_GRADED, so.S2_MIN_GRADED, so.S3_MIN_GRADED,
                          so.S4_MIN_GRADED), (6, 4, 4, 2))
        self.assertEqual(so.PATHS, ("clinicaltrials.gov/ct2/show/%s",
                                    "clinicaltrials.gov/ct2/show/record/%s"))
        self.assertEqual(so.TABLE_PATH, "results/ctep-spread/ctep-spread-trials.csv")


class ClassifyTests(unittest.TestCase):
    def test_sentence_in_visible_text_only(self):
        m = so.classify(html_page("NCT01", STOCK + " " + SENT), "NCT01")
        self.assertTrue(m["usable"] and m["sentence"] and m["stock"])
        m = so.classify(html_page("NCT01", STOCK), "NCT01")
        self.assertTrue(m["usable"])
        self.assertFalse(m["sentence"])  # the copy inside <script> does not count

    def test_variants_and_clause(self):
        for s in ("Legal authorized representatives (LAR) may sign and give written informed "
                  "consent", "legally-authorized representative may sign and give informed "
                  "consent"):
            self.assertTrue(so.classify(html_page("NCT01", s), "NCT01")["sentence"], s)
        m = so.classify(html_page("NCT01", "(or that of legally authorized representative, if "
                                           "applicable)"), "NCT01")
        self.assertTrue(m["clause"])
        self.assertFalse(m["sentence"])

    def test_unusable_pages(self):
        self.assertFalse(so.classify(html_page("NCT01", SENT), "NCT02")["usable"])
        self.assertFalse(so.classify(html_page("NCT01", SENT, pad=10), "NCT01")["usable"])
        page = ("<html><body>NCT01 %s %s</body></html>" % (SENT, "x " * 2100)).encode()
        self.assertFalse(so.classify(page, "NCT01")["usable"])  # no eligibility section
        self.assertFalse(so.classify(b"\x1f\x8bbroken", "NCT01")["usable"])


class CohortTests(unittest.TestCase):
    def test_order_and_gate(self):
        rows = so.read_table(table_bytes(make_rows()))
        trials = so.cohort(rows)
        self.assertEqual(len(trials), 30)
        self.assertEqual([t["nct_id"] for t in trials[:3]], list(so.EARLY_WASHU))
        self.assertEqual([so.kind(t) for t in trials], ["washu"] * 3 + ["swog"] * 10
                         + ["nci"] * 17)
        self.assertTrue(so.table_ok(rows, trials))
        self.assertFalse(so.table_ok(rows[:-1], trials))
        self.assertFalse(so.table_ok(rows, trials[1:]))

    def test_kind_other(self):
        r = {"nct_id": "NCT9", "group": "neither", "lead_sponsor": "Somewhere",
             "nci_linked": False}
        self.assertEqual(so.kind(r), "other")


class CdxTests(unittest.TestCase):
    def test_resume_key(self):
        pages = [json.dumps([["timestamp", "original", "statuscode", "digest"],
                             ["20200101000000", "u", "200", "D1"], [], ["KEY"]]).encode(),
                 json.dumps([["timestamp", "original", "statuscode", "digest"],
                             ["20210101000000", "u", "200", "D2"]]).encode()]
        seen = []

        def fetch(url):
            seen.append(url)
            return pages[len(seen) - 1]

        rows, done = so.cdx_rows("clinicaltrials.gov/ct2/show/NCT1", fetch)
        self.assertTrue(done)
        self.assertEqual([r["digest"] for r in rows], ["D1", "D2"])
        self.assertIn("resumeKey=KEY", seen[1])

    def test_empty_and_unfinished(self):
        self.assertEqual(so.cdx_rows("p", lambda u: b"[]"), ([], True))
        page = json.dumps([["timestamp", "original", "statuscode", "digest"],
                           ["20200101000000", "u", "200", "D"], [], ["K"]]).encode()
        rows, done = so.cdx_rows("p", lambda u: page)
        self.assertFalse(done)
        self.assertEqual(len(rows), so.MAX_CDX_PAGES)

    def test_plans(self):
        rows = [{"timestamp": "20230901000000", "original": "u", "statuscode": "200",
                 "digest": "Z"},
                {"timestamp": "20220801000000", "original": "u", "statuscode": "200",
                 "digest": "C"},
                {"timestamp": "20200101000000", "original": "u", "statuscode": "302",
                 "digest": "R"},
                {"timestamp": "20190101000000", "original": "u", "statuscode": "200",
                 "digest": "A"},
                {"timestamp": "20210101000000", "original": "u", "statuscode": "200",
                 "digest": "B"},
                {"timestamp": "20220101000000", "original": "u", "statuscode": "200",
                 "digest": "A"}]
        caps = so.captures(rows)
        self.assertEqual([c["digest"] for c in caps], ["A", "B", "A", "C"])
        p = so.plans(caps)
        self.assertEqual([(c["digest"], c["ts"][:4]) for c in p["oldest"]],
                         [("A", "2019"), ("B", "2021"), ("C", "2022")])
        self.assertEqual([(c["digest"], c["ts"][:4]) for c in p["newest_pre"]],
                         [("A", "2022"), ("B", "2021")])
        self.assertEqual([c["digest"] for c in p["newest_early"]], ["C", "A", "B"])


def mk(ts, sentence, stock=True):
    return {"ts": ts, "sentence": sentence, "stock": stock, "usable": True, "clause": False}


class GradeTests(unittest.TestCase):
    def setUp(self):
        self.trials = so.cohort(so.read_table(table_bytes(make_rows())))

    def marks(self, swog_old=True, nci_old=False, washu_old=False):
        out = {}
        for t in self.trials:
            k = so.kind(t)
            old = {"swog": swog_old, "nci": nci_old, "washu": washu_old}[k]
            out[t["nct_id"]] = {"oldest": mk("20200101000000", old),
                                "newest_pre": mk("20220101000000", old),
                                "newest_early": mk("20230101000000", True)}
        return out

    def test_all_hold(self):
        complete = {t["nct_id"]: True for t in self.trials}
        r = so.grade(self.trials, self.marks(), complete)
        self.assertTrue(all(r["gates"].values()))
        self.assertEqual(r["predictions"], {"S1": True, "S2": True, "S3": True, "S4": True})
        self.assertEqual(len(r["S2"]["graded_on"]), 10)
        self.assertEqual(len(r["S3"]["graded_on"]), 17)
        self.assertEqual(r["S4"]["graded_on"], list(so.EARLY_WASHU))

    def test_all_fail(self):
        complete = {t["nct_id"]: True for t in self.trials}
        r = so.grade(self.trials, self.marks(swog_old=False, nci_old=True, washu_old=True),
                     complete)
        self.assertEqual(r["predictions"], {"S1": True, "S2": False, "S3": False, "S4": False})
        r = so.grade(self.trials, self.marks(swog_old=False), complete)
        self.assertEqual(r["predictions"]["S1"], False)

    def test_half_boundaries(self):
        complete = {t["nct_id"]: True for t in self.trials}
        m = self.marks(swog_old=False)
        swog = [t["nct_id"] for t in self.trials if so.kind(t) == "swog"]
        for n in swog[:5]:
            m[n]["oldest"] = mk("20200101000000", True)
        self.assertTrue(so.grade(self.trials, m, complete)["predictions"]["S2"])  # 5 of 10
        m[swog[0]]["oldest"] = mk("20200101000000", False)
        self.assertFalse(so.grade(self.trials, m, complete)["predictions"]["S2"])  # 4 of 10

    def test_s1_ignores_pages_after_cutoff_and_small_counts(self):
        complete = {t["nct_id"]: True for t in self.trials}
        m = self.marks(swog_old=False)
        n = self.trials[3]["nct_id"]
        m[n]["oldest"] = mk("20220710000000", True)
        m[n]["newest_pre"] = None
        self.assertFalse(so.grade(self.trials, m, complete)["predictions"]["S1"])
        few = {t["nct_id"]: {"oldest": None, "newest_pre": None,
                             "newest_early": mk("20230101000000", True)} for t in self.trials}
        r = so.grade(self.trials, few, complete)
        self.assertEqual(r["predictions"], {"S1": None, "S2": None, "S3": None, "S4": None})

    def test_gates(self):
        m = self.marks()
        r = so.grade(self.trials, m, {t["nct_id"]: i >= 4 for i, t in enumerate(self.trials)})
        self.assertFalse(r["gates"]["A3_complete"])  # 26 of 30
        self.assertIsNone(r["predictions"])
        r = so.grade(self.trials, m, {t["nct_id"]: i >= 3 for i, t in enumerate(self.trials)})
        self.assertTrue(r["gates"]["A3_complete"])  # 27 of 30
        for t in self.trials:
            for p in m[t["nct_id"]].values():
                p["stock"] = False
        r = so.grade(self.trials, m, {t["nct_id"]: True for t in self.trials})
        self.assertFalse(r["gates"]["A4_stock_seen"])
        empty = {t["nct_id"]: {"oldest": None, "newest_pre": None, "newest_early": None}
                 for t in self.trials[:16]}
        r = so.grade(self.trials, empty, {t["nct_id"]: True for t in self.trials})
        self.assertFalse(r["gates"]["A2_usable"])


class MainTests(unittest.TestCase):
    def test_full_run(self):
        web = FakeWeb(make_rows())
        code, r, text, out = run_main(web)
        self.assertEqual(code, 0)
        self.assertEqual(r["status"], "graded")
        self.assertEqual(r["polls"], 1)
        self.assertTrue(all(r["gates"].values()), r["gates"])
        self.assertEqual(r["predictions"], {"S1": True, "S2": True, "S3": True, "S4": True})
        self.assertEqual(r["cdx_queries"], 60)
        self.assertEqual((r["downloaded"], r["download_errors"]), (60, 0))
        self.assertEqual(r["order"][:3], list(so.EARLY_WASHU))
        d = r["described"]
        self.assertEqual(d["earliest_sentence_page"][1], "20200101000000")
        self.assertEqual(len(d["gained_before_cutoff"]), 20)
        self.assertEqual(d["trials"]["NCT04462328"]["pages"],
                         {"oldest": ["20200101", "neither"], "newest_pre": ["20200601", "neither"],
                          "newest_early": ["20230101", "sentence"]})
        self.assertEqual(text.rstrip("\n"), so.result_text(r))
        with open(os.path.join(out, "sentence-origin-pages.csv"), encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 90)
        self.assertEqual({x["role"] for x in rows}, {"oldest", "newest_pre", "newest_early"})
        self.assertFalse(any(x["error"] for x in rows))

    def test_swog_without_sentence(self):
        code, r, _, _ = run_main(FakeWeb(make_rows(), swog_from_start=False))
        self.assertEqual(r["predictions"], {"S1": False, "S2": False, "S3": True, "S4": True})
        self.assertEqual(code, 0)

    def test_prereg_missing(self):
        web = FakeWeb(make_rows(), prereg=False)
        code, r, _, _ = run_main(web)
        self.assertEqual(code, 2)
        self.assertFalse(r["gates"]["P0_prereg_public"])
        self.assertEqual(r["polls"], so.POLLS)
        self.assertFalse(any(u.startswith("https://web.archive.org") for u in web.calls))

    def test_wrong_table(self):
        web = FakeWeb(make_rows()[:-1])
        code, r, _, _ = run_main(web)
        self.assertEqual(code, 2)
        self.assertFalse(r["gates"]["A1_table"])
        self.assertFalse(any(u.startswith("https://web.archive.org") for u in web.calls))

    def test_deadline(self):
        ticks = itertools.chain([0], itertools.repeat(so.DEADLINE_SECONDS + 1))
        code, r, _, _ = run_main(FakeWeb(make_rows()), clock=lambda: next(ticks))
        self.assertEqual(code, 2)
        self.assertFalse(r["gates"]["A3_complete"])
        self.assertEqual(r["cdx_queries"], 0)
        self.assertIsNone(r["predictions"])


if __name__ == "__main__":
    unittest.main()
