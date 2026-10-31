"""Tests for ctep_spread (no network). Apache-2.0. Made by MV2 of Munim, Inc. with AI agents."""

import csv
import io
import json
import os
import tempfile
import unittest
import urllib.parse

import ctep_spread as cs

SENTENCE_TEXT = ("Inclusion Criteria:\n\n* Ability to understand and willingness to sign an IRB "
                 "approved written informed consent document. Legally authorized\nrepresentatives "
                 "may sign and give informed consent on behalf of study participants.")
BARE_SENTENCE = ("Inclusion Criteria:\n\n* Signed consent. Legally authorized representatives "
                 "\\(LAR\\) may sign and give informed consent on behalf of study participants.")
NOISE_TEXT = "Inclusion Criteria:\n\n* A parent may sign and give informed consent for a child."


def local_bytes():
    with open(cs.__file__, "rb") as f:
        return f.read()


def study(nct, text, submitted, lead, lead_class="OTHER", collaborators=()):
    return {"protocolSection": {
        "identificationModule": {"nctId": nct},
        "statusModule": {"studyFirstSubmitDate": submitted},
        "sponsorCollaboratorsModule": {
            "leadSponsor": {"name": lead, "class": lead_class},
            "collaborators": [{"name": c, "class": "OTHER"} for c in collaborators]},
        "eligibilityModule": {"eligibilityCriteria": text}}}


def registry():
    """100 anchors (30 WashU, 30 NCI, 40 other centres), 20 other trials outside the frame, 10
    noise trials without the sentence."""
    out = {}
    for i in range(100):
        nct = "NCT%08d" % (5000000 + i)
        lead = (cs.WASHU_NAME.title() if i < 30 else "National Cancer Institute (NCI)" if i < 60
                else "Center %d" % i)
        out[nct] = study(nct, SENTENCE_TEXT, "2023-09-01", lead, "NIH" if 30 <= i < 60 else "OTHER")
    for i in range(20):
        nct = "NCT%08d" % (6000000 + i)
        out[nct] = study(nct, BARE_SENTENCE, "2024-01-01", "Hospital %d" % i)
    for i in range(10):
        nct = "NCT%08d" % (7000000 + i)
        out[nct] = study(nct, NOISE_TEXT, "2024-01-01", "Pharma %d" % i, "INDUSTRY")
    return out


def phrase_table(anchors):
    f = io.StringIO()
    w = csv.writer(f, lineterminator="\r\n")
    w.writerow(["nct_id", "start_year", cs.ANCHOR_COLUMN, "snippets"])
    for nct in anchors:
        w.writerow([nct, "2024", "True", "x"])
    for i in range(cs.PHRASE_ROWS - len(anchors)):
        w.writerow(["NCT%08d" % (1000000 + i), "2015", "False", ""])
    return f.getvalue().encode("utf-8")


class FakeApi:
    """Search 1 and 3 return every trial, search 2 only the sentence trials; 50 per page."""

    def __init__(self, studies, hide=()):
        self.studies = studies
        self.hide = set(hide)
        self.calls = 0

    def __call__(self, url):
        self.calls += 1
        q = {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).items()}
        if "filter.ids" in q:
            ids = q["filter.ids"].split(",")
            return {"studies": [self.studies[i] for i in ids if i in self.studies]}
        term = q["query.term"]
        ids = sorted(i for i in self.studies if i not in self.hide)
        if term == cs.SEARCHES[1]:
            ids = [i for i in ids if not i.startswith("NCT07")]
        start = int(q.get("pageToken", "0"))
        page = {"studies": [self.studies[i] for i in ids[start:start + 50]]}
        if start == 0:
            page["totalCount"] = len(ids)
        if start + 50 < len(ids):
            page["nextPageToken"] = str(start + 50)
        return page


def fake_fetch(prereg=b"# Pre-registration\nR1 ...", anchors=None, script=None):
    script = script if script is not None else local_bytes()
    table = phrase_table(anchors if anchors is not None else
                         ["NCT%08d" % (5000000 + i) for i in range(100)])

    def fetch(url):
        if url == cs.PHRASE_URL:
            return table
        if url.startswith(cs.REPO_RAW + cs.PREREG_PATH):
            return prereg
        if url.startswith(cs.REPO_RAW + cs.SCRIPT_PATH):
            return script
        raise IOError("404 " + url)
    return fetch


class Constants(unittest.TestCase):
    def test_pinned(self):
        self.assertEqual(cs.__version__, "0.1.0")
        self.assertEqual(cs.PHRASE_COMMIT, "c4c0ded776cdb43101b881c88f7de31fde2facdc")
        self.assertEqual((cs.PHRASE_ROWS, cs.ANCHOR_COLUMN, cs.MIN_ANCHORS,
                          cs.MIN_CURRENT_ANCHORS, cs.MIN_RECALL, cs.MIN_POST, cs.MIN_NEITHER),
                         (5473, "nci_lar_may_sign", 90, 80, 0.95, 40, 15))
        self.assertEqual((cs.LAST_WITHOUT, cs.FIRST_WITH), ("2022-07-09", "2023-08-04"))
        self.assertEqual((cs.R1_MIN_NEITHER_POST, cs.R2_MAX_NEITHER_PRE, cs.R3_MAX_INDUSTRY,
                          cs.R4_MIN_NEITHER_STOCK, cs.R5_MIN_NEITHER_SPONSORS),
                         (0.25, 0.10, 0.05, 0.80, 10))
        self.assertEqual(len(cs.SEARCHES), 3)
        self.assertEqual((cs.TRIES, cs.PAUSE), (40, 90))


class Patterns(unittest.TestCase):
    def test_sentence_across_lines_and_escapes(self):
        self.assertTrue(cs.marks(SENTENCE_TEXT)["sentence"])
        self.assertTrue(cs.marks(BARE_SENTENCE)["sentence"])
        self.assertFalse(cs.marks(NOISE_TEXT)["sentence"])

    def test_stock_line(self):
        self.assertTrue(cs.marks(SENTENCE_TEXT)["stock"])
        self.assertTrue(cs.marks("Ability to understand and the willingness to sign a written "
                                 "informed consent document.")["stock"])
        self.assertFalse(cs.marks(BARE_SENTENCE)["stock"])

    def test_clause(self):
        m = cs.marks("willingness to sign an IRB approved written informed consent document "
                     "\\(or that of legally authorized representative, if applicable\\).")
        self.assertTrue(m["clause"])
        self.assertFalse(m["sentence"])


class Pieces(unittest.TestCase):
    def test_period_bounds(self):
        self.assertEqual(cs.period("2022-07-09"), "pre")
        self.assertEqual(cs.period("2022-07-10"), "gap")
        self.assertEqual(cs.period("2023-08-03"), "gap")
        self.assertEqual(cs.period("2023-08-04"), "post")
        self.assertEqual(cs.period(""), "none")
        self.assertEqual(cs.period("2023-08"), "none")

    def test_groups(self):
        _, rec = cs.study_record(study("NCT1", "", "2024-01-01", "Mayo Clinic",
                                       collaborators=["National Cancer Institute (NCI)"]))
        self.assertTrue(cs.nci_linked(rec))
        self.assertFalse(cs.washu_led(rec))
        _, rec = cs.study_record(study("NCT2", "", "2024-01-01",
                                       " washington university SCHOOL of medicine "))
        self.assertTrue(cs.washu_led(rec))
        self.assertFalse(cs.nci_linked(rec))

    def test_read_anchors(self):
        n, has, ids, anchors = cs.read_anchors(phrase_table(["NCT05000001", "NCT05000000"]))
        self.assertEqual((n, has, len(ids)), (5473, True, 5473))
        self.assertEqual(anchors, ["NCT05000000", "NCT05000001"])
        n, has, _, anchors = cs.read_anchors(b"nct_id,x\r\nNCT1,True\r\n")
        self.assertEqual((n, has, anchors), (1, False, []))

    def test_search_pages(self):
        api = FakeApi(registry())
        recs, total, got = cs.search(cs.SEARCHES[0], fetch=api, sleep=lambda s: None)
        self.assertEqual((len(recs), total, got, api.calls), (130, 130, 130, 3))

    def test_fetch_ids_batches(self):
        api = FakeApi(registry())
        ids = ["NCT%08d" % (5000000 + i) for i in range(100)] + ["NCT09999999"]
        recs = cs.fetch_ids(ids, fetch=api, sleep=lambda s: None)
        self.assertEqual((len(recs), api.calls), (100, 2))


class Grading(unittest.TestCase):
    def rows(self):
        found = {}
        for nct, s in registry().items():
            found[nct] = (cs.study_record(s)[1], [1])
        return cs.build(found, {"NCT%08d" % (5000000 + i) for i in range(100)},
                        {"NCT%08d" % (5000000 + i) for i in range(100)})

    def test_build(self):
        rows = self.rows()
        self.assertEqual(len(rows), 120)
        by = {}
        for r in rows:
            by[r["group"]] = by.get(r["group"], 0) + 1
        self.assertEqual(by, {"washu": 30, "nci": 30, "neither": 60})
        self.assertEqual(sum(1 for r in rows if not r["in_frame"]), 20)

    def test_grade(self):
        measures, preds = cs.grade(self.rows())
        self.assertEqual(measures["R1_neither_of_post"][:3], [60, 120, 0.5])
        self.assertEqual(measures["R4_stock_of_neither"][:3], [40, 60, 0.6667])
        self.assertEqual(measures["R5_neither_lead_sponsors"], 60)
        self.assertEqual(preds, {"R1": True, "R2": True, "R3": True, "R4": False, "R5": True})

    def test_grade_small_is_ungraded(self):
        rows = [r for r in self.rows() if r["group"] != "neither"][:30]
        _, preds = cs.grade(rows)
        self.assertEqual(preds, {"R1": None, "R2": None, "R3": True, "R4": None, "R5": None})

    def test_pre_and_industry_fail(self):
        rows = self.rows()
        for r in rows[60:70]:
            r["period"] = "pre"
        for r in rows[:10]:
            r["lead_class"] = "INDUSTRY"
        _, preds = cs.grade(rows)
        self.assertFalse(preds["R2"])
        self.assertFalse(preds["R3"])

    def test_recall(self):
        reg = registry()
        recs = {k: cs.study_record(v)[1] for k, v in reg.items()}
        anchors = ["NCT%08d" % (5000000 + i) for i in range(100)]
        rc = cs.recall(anchors, recs, set(anchors[5:]))
        self.assertEqual((rc["anchors_current"], rc["anchors_found"], rc["recall"]), (100, 95, 0.95))
        self.assertEqual(rc["missed"], anchors[:5])


class Prereg(unittest.TestCase):
    def test_waits_then_ok(self):
        polls_seen = []
        real = fake_fetch()

        def fetch(url):
            if url.startswith(cs.REPO_RAW + cs.PREREG_PATH):
                polls_seen.append(url)
                if len(polls_seen) < 3:
                    raise IOError("404")
            return real(url)
        ok, polls = cs.wait_for_prereg(local_bytes(), fetch=fetch, sleep=lambda s: None)
        self.assertEqual((ok, polls), (True, 3))
        self.assertTrue(polls_seen[2].endswith("?n=2"))

    def test_other_script_never_ok(self):
        ok, polls = cs.wait_for_prereg(local_bytes(), fetch=fake_fetch(script=b"other"),
                                       sleep=lambda s: None, tries=4)
        self.assertEqual((ok, polls), (False, 4))

    def test_crlf_copy_is_same(self):
        local = local_bytes()
        ok, _ = cs.wait_for_prereg(local, fetch=fake_fetch(script=local.replace(b"\n", b"\r\n")),
                                   sleep=lambda s: None, tries=1)
        self.assertTrue(ok)


class Main(unittest.TestCase):
    def run_main(self, api, fetch):
        d = tempfile.mkdtemp()
        code = cs.main(["--out-dir", d], fetch=fetch, fetch_api=api, sleep=lambda s: None)
        with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
            return code, json.load(f), d

    def test_graded(self):
        code, res, d = self.run_main(FakeApi(registry()), fake_fetch())
        self.assertEqual((code, res["status"]), (0, "graded"))
        self.assertTrue(all(res["gates"].values()))
        self.assertEqual(res["sentence_trials"], 120)
        self.assertEqual(res["recall"]["recall"], 1.0)
        self.assertEqual(res["predictions"],
                         {"R1": True, "R2": True, "R3": True, "R4": False, "R5": True})
        self.assertEqual([s["total"] for s in res["searches"]], [130, 120, 130])
        self.assertEqual(res["described"]["outside_frame"], 20)
        with open(os.path.join(d, "ctep-spread-trials.csv"), encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 120)
        self.assertEqual(list(rows[0]), cs.TRIAL_COLUMNS)
        self.assertEqual(rows[0]["searches"], "1+2+3")

    def test_low_recall_not_graded(self):
        hide = ["NCT%08d" % (5000000 + i) for i in range(10)]
        code, res, _ = self.run_main(FakeApi(registry(), hide=hide), fake_fetch())
        self.assertEqual(code, 2)
        self.assertFalse(res["gates"]["A3_recall"])
        self.assertNotIn("predictions", res)

    def test_prereg_missing_fetches_nothing(self):
        api = FakeApi(registry())
        code, res, _ = self.run_main(api, fake_fetch(prereg=b"nothing here"))
        self.assertEqual((code, res["gates"]["P0_prereg_public"], res["polls"]), (2, False, 40))
        self.assertEqual(api.calls, 0)

    def test_table_gate(self):
        api = FakeApi(registry())
        code, res, _ = self.run_main(api, fake_fetch(anchors=["NCT05000000"]))
        self.assertEqual((code, res["gates"]["A1_table"]), (2, False))
        self.assertEqual(api.calls, 0)


if __name__ == "__main__":
    unittest.main()
