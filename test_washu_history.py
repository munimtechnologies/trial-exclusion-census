"""Tests for washu_history (no network). Apache-2.0. Made by MV2 of Munim, Inc. with AI agents."""

import gzip
import json
import os
import tempfile
import unittest
import urllib.parse

import washu_history as wh

STOCK_P = ("Ability to understand and willingness to sign an IRB approved written informed consent "
           "document")
CLAUSE_P = STOCK_P + " (or that of legally authorized representative, if applicable)."
SENT_P = ("Legally authorized representatives may sign and give informed consent on behalf of "
          "study participants.")
LATE = ["NCT0600000%d" % i for i in range(6)]
OTHER = ["NCT03%06d" % i for i in range(215)]
COLS = "nct_id,period,start_year,seen,nci_linked,path_2026_10_16,fetched,clause,sentence\n"


def page(nct, *items, script=""):
    return ("<html><head><script>%s</script><style>li{x:1}</style></head><body><h1>%s</h1>"
            "<!-- %s --><ul>%s</ul></body></html>" % (
                script, nct, SENT_P, "".join("<li>%s</li>" % i for i in items))).encode("utf-8")


def table_csv():
    rows = [(n, "early", False, True) for n in wh.EARLY_SENTENCE]
    rows += [(n, "late", True, False) for n in LATE]
    rows += [(n, "early", True, False) for n in OTHER]
    out = COLS + "".join("%s,%s,2020,False,False,True,True,%s,%s\n" % r for r in sorted(rows))
    return out.encode("utf-8")


def mark(clause=False, sentence=False, usable=True):
    return {"usable": usable, "clause": clause, "sentence": sentence}


class Constants(unittest.TestCase):
    def test_preregistered_values(self):
        self.assertEqual(wh.TABLE_ROWS, 224)
        self.assertEqual(wh.EARLY_SENTENCE, ("NCT04462328", "NCT04852328", "NCT05521984"))
        self.assertEqual(wh.LATE_CLAUSE_COUNT, 6)
        self.assertEqual(wh.HOSTS, ("clinicaltrials.gov",))
        self.assertEqual(wh.BOUNDARY_HOSTS, ("clinicaltrials.gov", "classic.clinicaltrials.gov"))
        self.assertEqual(wh.PATHS, ("/ct2/show/%s", "/ct2/show/record/%s"))
        self.assertEqual(wh.CUTOFF_DAY, "20220709")
        self.assertEqual((wh.PRE_TRIES, wh.BOUNDARY_MAX, wh.MIN_PRE_USABLE, wh.H2_MIN_GRADED),
                         (3, 25, 30, 2))
        self.assertEqual(wh.H3_KEPT, (9, 10))
        self.assertEqual(wh.DEADLINE_SECONDS, 9000)
        self.assertEqual(wh.TABLE_PATH, "results/washu-switch/washu-switch-trials.csv")


class Pages(unittest.TestCase):
    def test_patterns(self):
        self.assertTrue(wh.STOCK.search(STOCK_P))
        self.assertTrue(wh.CLAUSE.search(CLAUSE_P))
        self.assertFalse(wh.CLAUSE.search(SENT_P))
        self.assertTrue(wh.SENTENCE.search(SENT_P))
        self.assertTrue(wh.SENTENCE.search("Legally authorized representatives (LARs) may sign "
                                           "and give written informed consent"))
        self.assertFalse(wh.SENTENCE.search(CLAUSE_P))

    def test_scripts_comments_and_entities_dropped(self):
        data = page("NCT01234567", STOCK_P + " &amp; more",
                    script='var s = "%s";' % SENT_P)
        text = wh.page_text(data)
        self.assertNotIn("may sign", text)
        self.assertNotIn("x:1", text)
        self.assertIn("& more", text)
        m = wh.classify(data, "NCT01234567")
        self.assertTrue(m["usable"])
        self.assertFalse(m["sentence"] or m["clause"])

    def test_usable_needs_the_trial_and_the_stock_line(self):
        self.assertTrue(wh.classify(page("NCT01234567", CLAUSE_P), "nct01234567")["usable"])
        self.assertFalse(wh.classify(page("NCT07654321", CLAUSE_P), "NCT01234567")["usable"])
        self.assertFalse(wh.classify(page("NCT01234567", "Age 18 or over"),
                                     "NCT01234567")["usable"])
        m = wh.classify(page("NCT01234567", STOCK_P + ".", SENT_P), "NCT01234567")
        self.assertTrue(m["usable"] and m["sentence"])
        self.assertEqual(wh.wording(m), "sentence")

    def test_gzip_and_garbage(self):
        data = gzip.compress(page("NCT01234567", CLAUSE_P))
        m = wh.classify(data, "NCT01234567")
        self.assertTrue(m["usable"] and m["clause"])
        self.assertFalse(wh.classify(b"\x1f\x8bnot gzip", "NCT01234567")["usable"])


class Selection(unittest.TestCase):
    def test_prefixes(self):
        self.assertEqual(wh.prefixes("NCT01234567", False),
                         ["clinicaltrials.gov/ct2/show/NCT01234567",
                          "clinicaltrials.gov/ct2/show/record/NCT01234567"])
        self.assertEqual(len(wh.prefixes("NCT01234567", True)), 4)
        self.assertIn("classic.clinicaltrials.gov/ct2/show/record/NCT01234567",
                      wh.prefixes("NCT01234567", True))

    def test_captures_keep_status_200_only(self):
        rows = [{"timestamp": "20200101000000", "original": "u", "statuscode": "200",
                 "digest": "A"},
                {"timestamp": "20190101000000", "original": "u", "statuscode": "301",
                 "digest": "B"},
                {"timestamp": "20180101000000", "original": "u", "statuscode": "-",
                 "digest": "A"}]
        self.assertEqual([c["ts"] for c in wh.captures(rows)], ["20200101000000"])

    def test_pre_candidates(self):
        caps = [{"ts": ts, "original": "u", "digest": d} for ts, d in (
            ("20190101000000", "A"), ("20200101000000", "B"), ("20210101000000", "A"),
            ("20210601000000", "C"), ("20220101000000", "D"), ("20220709235959", "E"),
            ("20220710000000", "F"))]
        got = wh.pre_candidates(caps)
        self.assertEqual([c["ts"] for c in got], ["20220709235959", "20220101000000",
                                                  "20210601000000"])
        self.assertEqual(wh.pre_candidates(caps[:3])[1]["ts"], "20200101000000")
        self.assertEqual(len(wh.pre_candidates(caps[:3])), 2)

    def test_boundary_plan(self):
        caps = [{"ts": "2020%02d01000000" % (i % 12 + 1), "original": "u", "digest": str(i % 30)}
                for i in range(40)]
        caps.sort(key=lambda c: c["ts"])
        got = wh.boundary_plan(caps)
        self.assertEqual(len(got), wh.BOUNDARY_MAX)
        self.assertEqual(len({c["digest"] for c in got}), wh.BOUNDARY_MAX)
        self.assertEqual(got, sorted(got, key=lambda c: (c["ts"], c["original"])))

    def test_cdx_resume_key(self):
        header = wh.CDX_FIELDS.split(",")
        pages = [[header, ["20150101000000", "u", "200", "D1", "x"], [], ["KEY1"]],
                 [header, ["20160101000000", "u", "200", "D2", "x"]]]
        calls = []

        def fetch(url):
            calls.append(url)
            return json.dumps(pages[1 if "resumeKey" in url else 0]).encode("utf-8")
        rows, complete = wh.cdx_rows("a/", fetch)
        self.assertTrue(complete)
        self.assertEqual([r["digest"] for r in rows], ["D1", "D2"])
        self.assertIn("resumeKey=KEY1", calls[1])

    def test_table(self):
        trials = wh.read_table(table_csv())
        self.assertTrue(wh.table_ok(trials))
        self.assertEqual(wh.boundary_ids(trials), sorted(list(wh.EARLY_SENTENCE) + LATE))
        self.assertFalse(wh.table_ok(trials[:-1]))
        i = [t["nct_id"] for t in trials].index(wh.EARLY_SENTENCE[0])
        trials[i] = dict(trials[i], sentence=False)
        self.assertFalse(wh.table_ok(trials))


def trials_of(n, clause=True):
    return [{"nct_id": "NCT%08d" % i, "period": "early", "clause": clause, "sentence": False}
            for i in range(n)]


class Grading(unittest.TestCase):
    def test_all_hold(self):
        trials = trials_of(30)
        pre = {t["nct_id"]: mark(clause=True) for t in trials}
        first = {n: mark(clause=True) for n in wh.EARLY_SENTENCE[:2]}
        r = wh.grade(trials, pre, first, True)
        self.assertTrue(all(r["gates"].values()))
        self.assertEqual(r["predictions"], {"H1": True, "H2": True, "H3": True})
        self.assertEqual((r["pre_usable"], r["clause_today"], r["clause_kept"]), (30, 30, 30))

    def test_failures(self):
        trials = trials_of(30)
        pre = {t["nct_id"]: mark(clause=True) for t in trials}
        for t in trials[:4]:
            pre[t["nct_id"]] = mark(sentence=True)
        first = {n: mark(sentence=(n == wh.EARLY_SENTENCE[0])) for n in wh.EARLY_SENTENCE}
        r = wh.grade(trials, pre, first, True)
        self.assertEqual(r["pre_with_sentence"], [t["nct_id"] for t in trials[:4]])
        self.assertEqual(r["h2_sentence_first"], [wh.EARLY_SENTENCE[0]])
        self.assertEqual(r["predictions"], {"H1": False, "H2": False, "H3": False})

    def test_h3_boundary_is_exact(self):
        trials = trials_of(30)
        pre = {t["nct_id"]: mark(clause=True) for t in trials}
        for t in trials[:3]:
            pre[t["nct_id"]] = mark()
        self.assertTrue(wh.grade(trials, pre, {}, True)["predictions"]["H3"])  # 27 of 30
        pre[trials[3]["nct_id"]] = mark()
        self.assertFalse(wh.grade(trials, pre, {}, True)["predictions"]["H3"])  # 26 of 30

    def test_ungraded_parts(self):
        trials = trials_of(30)
        pre = {t["nct_id"]: mark(clause=True) for t in trials}
        r = wh.grade(trials, pre, {wh.EARLY_SENTENCE[0]: mark(clause=True)}, True)
        self.assertIsNone(r["predictions"]["H2"])
        r = wh.grade(trials_of(30, clause=False), {t["nct_id"]: mark()
                                                   for t in trials_of(30)}, {}, True)
        self.assertIsNone(r["predictions"]["H3"])
        self.assertTrue(r["predictions"]["H1"])

    def test_gates(self):
        trials = trials_of(30)
        pre = {t["nct_id"]: mark(clause=True) for t in trials[:29]}
        r = wh.grade(trials, pre, {}, True)
        self.assertFalse(r["gates"]["A2_coverage"])
        self.assertIsNone(r["predictions"])
        pre[trials[29]["nct_id"]] = mark(clause=True)
        r = wh.grade(trials, pre, {}, False)
        self.assertFalse(r["gates"]["A3_complete"])
        self.assertIsNone(r["predictions"])


class Main(unittest.TestCase):
    def run_main(self, public=True, clock=None, sentence_in=()):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "washu_history.py"), "rb") as f:
            script = f.read()
        calls = []

        def fetch(url):
            calls.append(url)
            if url.startswith(wh.REPO_RAW):
                if wh.TABLE_PATH in url:
                    return table_csv()
                if not public:
                    raise OSError("404")
                if wh.PREREG_PATH in url:
                    return b"# PREREG\nH1 ...\n"
                return script.replace(b"\n", b"\r\n")
            if url.startswith(wh.CDX):
                prefix = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["url"][0]
                if prefix.startswith("clinicaltrials.gov/ct2/show/NCT"):
                    nct = prefix.rsplit("/", 1)[1]
                    return json.dumps([wh.CDX_FIELDS.split(","),
                                       ["20210101000000", "https://clinicaltrials.gov/ct2/show/"
                                        + nct, "200", "D" + nct, "text/html"]]).encode("utf-8")
                return b"[]"
            if url.startswith("https://web.archive.org/web/"):
                nct = url.rsplit("/", 1)[1]
                if nct in sentence_in:
                    return page(nct, STOCK_P + ".", SENT_P)
                return page(nct, CLAUSE_P, script='var s = "%s";' % SENT_P)
            raise OSError("unexpected " + url)
        out = tempfile.mkdtemp()
        sleeps = []
        code = wh.main(["--out-dir", out], fetch=fetch, sleep=sleeps.append,
                       clock=clock or (lambda: 0.0))
        with open(os.path.join(out, "result.json"), encoding="utf-8") as f:
            return code, json.load(f), out, sleeps, calls

    def test_graded_when_public(self):
        code, r, out, sleeps, calls = self.run_main()
        self.assertEqual(code, 0)
        self.assertEqual(r["status"], "graded")
        self.assertEqual(r["polls"], 1)
        self.assertTrue(all(r["gates"].values()), r["gates"])
        self.assertEqual(r["predictions"], {"H1": True, "H2": True, "H3": True})
        self.assertEqual(r["trials"], 224)
        self.assertEqual(r["cdx_queries"], 215 * 2 + 9 * 4)
        self.assertEqual(r["downloaded"], 224)  # the boundary page is the cached pre page
        self.assertEqual(sleeps.count(wh.CDX_PAUSE), 215 * 2 + 9 * 4 - 1)
        self.assertEqual(sleeps.count(wh.DOWNLOAD_PAUSE), 223)
        self.assertEqual(r["pre_usable"], 224)
        self.assertEqual(r["described"]["pre_to_today"], {"clause->clause": 221,
                                                          "clause->sentence": 3})
        self.assertIsNone(r["described"]["earliest_sentence_page"])
        self.assertEqual(r["described"]["boundary_timelines"]["NCT04462328"],
                         [["20210101", "clause"]])
        with open(os.path.join(out, "washu-history-pages.csv"), encoding="utf-8") as f:
            self.assertEqual(len(f.read().splitlines()), 1 + 224 + 9)
        with open(os.path.join(out, "result.txt"), encoding="utf-8") as f:
            self.assertIn("predictions: H1=True, H2=True, H3=True", f.read())

    def test_sentence_before_the_cutoff_fails_h1(self):
        code, r, _, _, _ = self.run_main(sentence_in=("NCT04462328",))
        self.assertEqual(code, 0)
        self.assertEqual(r["pre_with_sentence"], ["NCT04462328"])
        self.assertEqual(r["predictions"]["H1"], False)
        self.assertEqual(r["predictions"]["H2"], False)
        self.assertEqual(r["described"]["earliest_sentence_page"],
                         ["NCT04462328", "20210101000000"])

    def test_deadline_leaves_it_ungraded(self):
        ticks = iter([0.0] + [wh.DEADLINE_SECONDS + 1.0] * 10000)
        code, r, _, _, _ = self.run_main(clock=lambda: next(ticks))
        self.assertEqual(code, 2)
        self.assertFalse(r["gates"]["A3_complete"])
        self.assertIsNone(r["predictions"])
        self.assertEqual(r["cdx_queries"], 0)

    def test_nothing_fetched_when_not_public(self):
        code, r, _, sleeps, calls = self.run_main(public=False)
        self.assertEqual(code, 2)
        self.assertFalse(r["gates"]["P0_prereg_public"])
        self.assertEqual(len(sleeps), wh.TRIES - 1)
        self.assertNotIn("fetched_utc", r)
        self.assertFalse(any(u.startswith((wh.CDX, "https://web.archive.org/web/"))
                             or wh.TABLE_PATH in u for u in calls))


if __name__ == "__main__":
    unittest.main()
