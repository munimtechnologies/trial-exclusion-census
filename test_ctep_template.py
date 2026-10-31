"""Tests for ctep_template (no network). Apache-2.0. Made by MV2 of Munim, Inc. with AI agents."""

import io
import json
import os
import tempfile
import unittest
import urllib.parse
import zipfile

import ctep_template as ct

STOCK_P = "Ability to understand and the willingness to sign a written informed consent document."
SENT_P = ("Legally authorized representatives may sign and give informed consent on behalf of "
          "study participants.")
EXCL_P = "3.2 Exclusion Criteria. Patients who are receiving any other investigational agents."


def docx(paragraphs, extra=""):
    body = "".join('<w:p><w:r><w:t xml:space="preserve">%s</w:t></w:r></w:p>' % p
                   for p in paragraphs)
    xml = ('<?xml version="1.0"?><w:document xmlns:w="x"><w:body>%s%s</w:body></w:document>'
           % (body, extra))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", xml)
    return buf.getvalue()


NEW = docx(["3.1.17 " + STOCK_P, SENT_P, EXCL_P])
OLD = docx([STOCK_P, EXCL_P])
OLD2 = docx(["Version Date: June 22, 2015", STOCK_P, EXCL_P])
DOC_OLD = ct.OLE + ("  " + STOCK_P + "\r" + EXCL_P).encode("utf-16-le")


class Constants(unittest.TestCase):
    def test_preregistered_values(self):
        self.assertEqual(ct.PREFIXES, ("ctep.cancer.gov/protocoldevelopment/docs/",
                                       "dctd.cancer.gov/research/ctep-trials/trial-development/"))
        self.assertEqual(ct.EXCLUDE_WORDS, ("consent", "icd", "worksheet"))
        self.assertEqual((ct.MAX_DOWNLOADS, ct.MIN_USABLE, ct.MAX_BRACKET_DAYS), (150, 4, 730))
        self.assertEqual((ct.T1_EARLIEST, ct.T1_LATEST), ("20200101", "20231231"))
        self.assertEqual((ct.ADJACENT_CHARS, ct.NEAR_CHARS), (300, 500))


class Patterns(unittest.TestCase):
    def test_stock(self):
        self.assertTrue(ct.STOCK.search(STOCK_P))
        self.assertTrue(ct.STOCK.search("ability to understand and willingness to sign an IRB "
                                        "approved written informed consent document"))
        self.assertFalse(ct.STOCK.search("Ability to understand the study"))

    def test_sentence_and_clause(self):
        self.assertTrue(ct.SENTENCE.search(SENT_P))
        self.assertFalse(ct.SENTENCE.search(STOCK_P))
        self.assertTrue(ct.CLAUSE.search("(or that of legally authorized representative, if "
                                         "applicable)"))
        self.assertFalse(ct.CLAUSE.search(SENT_P))

    def test_lar(self):
        self.assertTrue(ct.LAR.search("a Legally Authorized Representative may sign"))
        self.assertTrue(ct.LAR.search("consent of the LAR"))
        self.assertFalse(ct.LAR.search("a lar of text; the solar panel"))


class Text(unittest.TestCase):
    def test_split_runs_deleted_text_and_entities(self):
        xml = ('<w:p><w:r><w:t>Legally authorized</w:t></w:r><w:r><w:t xml:space="preserve"> '
               'representatives may sign and give informed consent</w:t></w:r></w:p>'
               '<w:p><w:del><w:r><w:delText>or that of legally authorized representative'
               '</w:delText></w:r></w:del><w:r><w:t>A &amp; B</w:t></w:r></w:p>')
        text = ct.clean(ct.xml_text(xml))
        self.assertIn("Legally authorized representatives may sign", text)
        self.assertNotIn("or that of", text)
        self.assertIn("A & B", text)

    def test_docx_classified(self):
        f = ct.classify(NEW)
        self.assertEqual(f["kind"], "docx")
        self.assertTrue(f["usable"] and f["sentence"] and f["adjacent"] and f["lar_near"])
        self.assertFalse(f["clause"])
        f = ct.classify(OLD2)
        self.assertTrue(f["usable"])
        self.assertFalse(f["sentence"] or f["lar_near"])
        self.assertEqual(f["version_dates"], ["June 22, 2015"])

    def test_doc_both_alignments_and_cp1252(self):
        # The text starts with a paragraph mark, as in a real .doc text stream: without it the
        # header's last byte (0xE1) reads as a letter glued to "Ability".
        both = "\r" + STOCK_P + " " + SENT_P
        for data in (DOC_OLD, ct.OLE + b"\x00" + both.encode("utf-16-le"),
                     ct.OLE + both.encode("cp1252")):
            f = ct.classify(data)
            self.assertEqual(f["kind"], "doc")
            self.assertTrue(f["usable"])
        self.assertFalse(ct.classify(DOC_OLD)["sentence"])
        self.assertTrue(ct.classify(data)["sentence"])

    def test_other_and_broken(self):
        self.assertEqual(ct.classify(b"<html>Not found</html>")["kind"], "other")
        self.assertFalse(ct.classify(b"<html>Not found</html>")["usable"])
        self.assertEqual(ct.classify(b"PK\x03\x04broken")["kind"], "bad-docx")

    def test_far_sentence_not_adjacent(self):
        f = ct.classify(docx([STOCK_P, "x " * 200, SENT_P]))
        self.assertTrue(f["sentence"])
        self.assertFalse(f["adjacent"])


class Selection(unittest.TestCase):
    def test_template_name(self):
        base = "http://ctep.cancer.gov:80/protocolDevelopment/docs/"
        self.assertEqual(ct.template_name(base + "CTEP%20Generic%20Protocol%20Template.doc"),
                         "ctep generic protocol template.doc")
        self.assertTrue(ct.template_name(base + "ctep_generic_protocol_template_for_cancer_"
                                                "treatment_trial.docx?x=1"))
        self.assertIsNone(ct.template_name(base + "protocol_template.pdf"))
        self.assertIsNone(ct.template_name(base + "consent_protocol_template.docx"))
        self.assertIsNone(ct.template_name(base + "Generic_ICD_Template.docx"))

    def test_cdx_resume_key(self):
        header = ct.CDX_FIELDS.split(",")
        pages = [[header, ["20150101000000", "http://a/protocol_template.doc", "200", "D1",
                           "x"], [], ["KEY1"]],
                 [header, ["20160101000000", "http://a/protocol_template.doc", "200", "D2",
                           "x"]]]
        calls = []

        def fetch(url):
            calls.append(url)
            return json.dumps(pages[1 if "resumeKey" in url else 0]).encode("utf-8")
        rows, complete = ct.cdx_rows("a/", fetch)
        self.assertTrue(complete)
        self.assertEqual([r["digest"] for r in rows], ["D1", "D2"])
        self.assertEqual(len(calls), 2)
        self.assertIn("resumeKey=KEY1", calls[1])
        self.assertEqual(ct.cdx_rows("a/", lambda url: b"[]"), ([], True))


def cdx_page():
    d = "http://ctep.cancer.gov/protocolDevelopment/docs/"
    t = d + "ctep_generic_protocol_template_for_cancer_treatment_trial.docx"
    rows = [["20150601000000", d + "CTEP_Generic_Protocol_Template.doc", "200", "D1", "m"],
            ["20180601000000", d + "CTEP_Generic_Protocol_Template.doc", "200", "D2", "m"],
            ["20200301000000", t, "200", "D3", "m"],
            ["20210301000000", t, "-", "D3", "warc/revisit"],
            ["20211001000000", t, "200", "D4", "m"],
            ["20230101000000", t, "200", "D4", "m"],
            ["20190101000000", d + "consent_template.docx", "200", "D5", "m"],
            ["20190101000000", d + "protocol_template.pdf", "200", "D6", "m"],
            ["20220101000000", d + "ETCTN_Protocol_Template.docx", "404", "D7", "m"]]
    return [ct.CDX_FIELDS.split(",")] + rows


ARCHIVED = {"20150601000000": DOC_OLD, "20180601000000": OLD, "20200301000000": OLD2,
            "20211001000000": NEW}


def caps_files(stamps):
    """Captures and files from (ts, digest, sentence) triples, all usable."""
    caps = [{"ts": ts, "original": "http://a/protocol_template.docx", "digest": d,
             "fetchable": True} for ts, d, _ in stamps]
    files = {d: ct.classify(NEW if s else OLD) for _, d, s in stamps}
    return caps, files


class Grading(unittest.TestCase):
    def test_selection_and_bracket(self):
        caps = ct.captures([dict(zip(cdx_page()[0], r)) for r in cdx_page()[1:]])
        self.assertEqual(len(caps), 6)
        todo = ct.plan(caps)
        self.assertEqual([c["digest"] for c in todo], ["D1", "D2", "D3", "D4"])
        files = {c["digest"]: ct.classify(ARCHIVED[c["ts"]]) for c in todo}
        r = ct.grade(caps, files, ct.classify(NEW))
        self.assertEqual((r["last_without"], r["first_with"]), ("20210301000000",
                                                                "20211001000000"))
        self.assertEqual(r["bracket_days"], 214)
        self.assertEqual((r["usable_files"], r["usable_captures"]), (4, 6))
        self.assertTrue(all(r["gates"].values()), r["gates"])
        self.assertEqual(r["predictions"], {"T1": True, "T2": True, "T3": True, "T4": True})

    def test_t1_fails_outside_window(self):
        caps, files = caps_files([("20160101000000", "A", False), ("20180601000000", "B", False),
                                  ("20190301000000", "C", True), ("20200101000000", "D", True)])
        r = ct.grade(caps, files, ct.classify(NEW))
        self.assertTrue(r["gates"]["G4_bracket_narrow"])
        self.assertFalse(r["predictions"]["T1"])

    def test_wide_bracket_leaves_t1_ungraded(self):
        caps, files = caps_files([("20140101000000", "A", False), ("20150601000000", "B", False),
                                  ("20210301000000", "C", True), ("20220101000000", "D", True)])
        r = ct.grade(caps, files, ct.classify(NEW))
        self.assertEqual(r["bracket_days"], 2100)
        self.assertFalse(r["gates"]["G4_bracket_narrow"])
        self.assertIsNone(r["predictions"]["T1"])
        self.assertTrue(r["predictions"]["T3"])

    def test_t4_fails_on_an_earlier_representative(self):
        caps, files = caps_files([("20200101000000", "A", False), ("20210101000000", "B", False),
                                  ("20210601000000", "C", True), ("20220101000000", "D", True)])
        files["A"] = ct.classify(docx([STOCK_P + " (or that of legally authorized "
                                                 "representative, if applicable)"]))
        r = ct.grade(caps, files, ct.classify(NEW))
        self.assertFalse(r["predictions"]["T2"])
        self.assertFalse(r["predictions"]["T4"])

    def test_gates_without_an_earlier_side(self):
        caps, files = caps_files([("20200101000000", "A", True), ("20210101000000", "B", False),
                                  ("20210601000000", "C", True), ("20220101000000", "D", True)])
        r = ct.grade(caps, files, ct.classify(NEW))
        self.assertFalse(r["gates"]["G3_both_sides"])
        self.assertIsNone(r["predictions"])
        self.assertEqual(r["without_after_first_with"], ["http://a/protocol_template.docx"])
        r = ct.grade(caps, files, ct.classify(OLD))
        self.assertFalse(r["gates"]["G1_live_control"])


class Main(unittest.TestCase):
    def run_main(self, public):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "ctep_template.py"), "rb") as f:
            script = f.read()

        def fetch(url):
            if url.startswith(ct.REPO_RAW):
                if not public:
                    raise OSError("404")
                if ct.PREREG_PATH in url:
                    return b"# PREREG\nT1 ...\n"
                return script.replace(b"\n", b"\r\n")
            if url == ct.LIVE_URL:
                return NEW
            if url.startswith(ct.CDX):
                prefix = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["url"][0]
                page = cdx_page() if prefix.startswith("ctep.") else []
                return json.dumps(page).encode("utf-8")
            if url.startswith("https://web.archive.org/web/"):
                return ARCHIVED[url.split("/web/")[1][:14]]
            raise OSError("unexpected " + url)
        out = tempfile.mkdtemp()
        sleeps = []
        code = ct.main(["--out-dir", out], fetch=fetch, sleep=sleeps.append)
        with open(os.path.join(out, "result.json"), encoding="utf-8") as f:
            return code, json.load(f), out, sleeps

    def test_graded_when_public(self):
        code, result, out, sleeps = self.run_main(True)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "graded")
        self.assertEqual(result["polls"], 1)
        self.assertEqual(result["live_source"], "direct")
        self.assertEqual(sleeps, [ct.DOWNLOAD_PAUSE] * 3)
        self.assertEqual((result["template_captures"], result["distinct_files"],
                          result["downloaded"]), (6, 4, 4))
        self.assertTrue(all(result["predictions"].values()))
        with open(os.path.join(out, "ctep-template-captures.csv"), encoding="utf-8") as f:
            self.assertEqual(len(f.read().splitlines()), 7)
        with open(os.path.join(out, "result.txt"), encoding="utf-8") as f:
            self.assertIn("June 22, 2015", f.read())

    def test_nothing_fetched_when_not_public(self):
        code, result, _, sleeps = self.run_main(False)
        self.assertEqual(code, 2)
        self.assertFalse(result["gates"]["P0_prereg_public"])
        self.assertEqual(len(sleeps), ct.TRIES - 1)
        self.assertNotIn("fetched_utc", result)


if __name__ == "__main__":
    unittest.main()
