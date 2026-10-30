"""Tests for grade_job (no network). Apache-2.0. Made by MV2 of Munim, Inc. with AI agents."""

import json
import os
import tempfile
import types
import unittest

import grade_job as gj

LABELS = b"blind_id,label,reason\nR001,adult_permission,x\n"


class FakeFetch:
    """Answers each URL with queued bytes, or raises like a 404 when nothing is queued."""

    def __init__(self, answers):
        self.answers = {k: list(v) for k, v in answers.items()}
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        base = url.split("?")[0]
        queue = self.answers.get(base) or []
        if not queue:
            raise OSError("HTTP Error 404: Not Found")
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(item, Exception):
            raise item
        return item


class Waiting(unittest.TestCase):
    def test_public_after_two_misses(self):
        fetch = FakeFetch({gj.RAW + gj.LABELS_PATH: [OSError("404"), OSError("404"), LABELS]})
        sleeps = []
        ok, tries, remote = gj.wait_for_public(LABELS, fetch=fetch, sleep=sleeps.append)
        self.assertEqual((ok, tries, remote), (True, 3, gj.sha256(LABELS)))
        self.assertEqual(sleeps, [gj.PAUSE, gj.PAUSE])

    def test_crlf_copy_counts_as_same(self):
        fetch = FakeFetch({gj.RAW + gj.LABELS_PATH: [LABELS.replace(b"\n", b"\r\n")]})
        self.assertTrue(gj.wait_for_public(LABELS, fetch=fetch, sleep=lambda s: None)[0])

    def test_gives_up(self):
        fetch = FakeFetch({})
        sleeps = []
        ok, tries, remote = gj.wait_for_public(LABELS, fetch=fetch, sleep=sleeps.append, tries=5)
        self.assertEqual((ok, tries, remote), (False, 5, None))
        self.assertEqual(len(sleeps), 4)

    def test_different_labels_never_pass(self):
        other = LABELS.replace(b"adult_permission", b"unclear")
        fetch = FakeFetch({gj.RAW + gj.LABELS_PATH: [other]})
        ok, _, remote = gj.wait_for_public(LABELS, fetch=fetch, sleep=lambda s: None, tries=3)
        self.assertFalse(ok)
        self.assertEqual(remote, gj.sha256(other))

    def test_cache_buster_changes(self):
        fetch = FakeFetch({})
        gj.wait_for_public(LABELS, fetch=fetch, sleep=lambda s: None, tries=3)
        self.assertEqual(len(set(fetch.urls)), 3)


class Pieces(unittest.TestCase):
    def test_check_sha(self):
        h = gj.sha256(b"abc")
        self.assertTrue(gj.check_sha(b"abc", h))
        self.assertTrue(gj.check_sha(b"abc", h[:12], prefix=True))
        self.assertFalse(gj.check_sha(b"abd", h))
        self.assertFalse(gj.check_sha(b"abc", h[:12]))

    def test_key_csv_format(self):
        data = gj.key_csv([("R001", "NCT00000002", "nci"), ("R002", "NCT00000001", "neither")])
        self.assertEqual(data, b"blind_id,nct_id,group\nR001,NCT00000002,nci\n"
                               b"R002,NCT00000001,neither\n")

    def test_key_rows_sorted_by_blind_id(self):
        cp = types.SimpleNamespace(
            GROUPS=(("nci", 1), ("neither", 1)),
            draw=lambda rows: {"nci": ["NCT1"], "neither": ["NCT2"]},
            blind_order=lambda ids: {"NCT1": "R002", "NCT2": "R001"})
        self.assertEqual(gj.key_rows(cp, []), [("R001", "NCT2", "neither"),
                                               ("R002", "NCT1", "nci")])

    def test_pinned_values(self):
        self.assertEqual(gj.SCRIPT_SHA256[:12], "7674ee9f942d")
        self.assertEqual(gj.READING_SHA12, "13c9e6d8b257")
        self.assertEqual(gj.LABELS_PATH, "results/consent-permission/labels.csv")


class Main(unittest.TestCase):
    def run_main(self, answers):
        out = tempfile.mkdtemp()
        labels = os.path.join(out, "labels.csv")
        with open(labels, "wb") as f:
            f.write(LABELS)
        fetch = FakeFetch(answers)
        code = gj.main(["--labels", labels, "--out-dir", out], fetch=fetch,
                       sleep=lambda s: None)
        with open(os.path.join(out, "gate.json"), encoding="utf-8") as f:
            return code, json.load(f), fetch, out

    def test_stops_when_labels_not_public(self):
        code, gate, fetch, out = self.run_main({})
        self.assertEqual(code, 2)
        self.assertFalse(gate["labels_public"])
        self.assertFalse(os.path.exists(os.path.join(out, "key.csv")))
        self.assertTrue(all(gj.LABELS_PATH in u for u in fetch.urls))

    def test_stops_on_wrong_script(self):
        code, gate, fetch, out = self.run_main({
            gj.RAW + gj.LABELS_PATH: [LABELS],
            gj.RAW + gj.READING_PATH: [b"reading"],
            gj.RAW + gj.SCRIPT_PATH: [b"print('not the tested file')\n"]})
        self.assertEqual(code, 2)
        self.assertTrue(gate["labels_public"])
        self.assertFalse(gate["script_matches"])
        self.assertIn("mismatch", gate["status"])
        self.assertFalse(os.path.exists(os.path.join(out, "key.csv")))


if __name__ == "__main__":
    unittest.main()
