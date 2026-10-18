"""Offline wording tests for the README, the result notes, the guide, the code and the tests (no network). Apache-2.0.

Readings and labels in this repository were made by AI agents working for MV2, and no person has
checked them yet. These pages must say so and must not describe that work as done "by hand" or
"by eye". "By hand" may still describe the hand-coded studies of others, and instructions to
people who check the rules themselves.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HERE, "README.md")
ACCOMMODATION = os.path.join(HERE, "results", "recall", "ACCOMMODATION.md")
SCORES = os.path.join(HERE, "results", "recall", "SCORES-0.4.0.md")
GUIDE = os.path.join(HERE, "toolkit", "inclusive-eligibility-guide.md")
NOTES = [os.path.join(HERE, *p) for p in (
    ("results", "consent-phrase", "CONSENT-RESULT.md"),
    ("results", "consent-phrase", "CONSENT-NEAR-VARIANT.md"),
    ("results", "consent-phrase", "CONSENT-MISSED-READ.md"),
    ("results", "phone-check", "PHONE-REQUIREMENT-RESULT.md"),
    ("results", "phone-check", "PHONE-MATCHED-RESULT.md"),
    ("results", "sponsor-check", "VA-CHECK.md"),
    ("results", "sponsor-check", "VA-MATCHED-RESULT.md"),
    ("results", "trend-check", "TREND-CHECK.md"),
    ("results", "trend-check", "PREREG-v0.3-RESULT.md"),
    ("results", "trend-check", "PREREG-v0.3-PERYEAR.md"),
    ("results", "v0.1.1", "PRECISION.md"),
    ("results", "v0.1.1", "README.md"),
    ("toolkit", "inclusive-eligibility-guide.md"),
)]
CENSUS = os.path.join(HERE, "exclusion_census.py")
RECALL = os.path.join(HERE, "recall_sample.py")
TESTS = [os.path.join(HERE, n) for n in (
    "test_exclusion_census.py", "test_va_matched.py", "test_phone_matched.py", "test_peryear_v03.py")]

CLAIMS = re.compile(r"hand[- ]check|hand-label|(?<!can be )checked\s+by\s+hand|read\s+by\s+hand|"
                    r"traced\s+by\s+hand|adding\s+(?:\S+\s+){0,4}by\s+hand|worked\s+out\s+by\s+hand|"
                    r"measured\s+by\s+hand|by\s+eye", re.I)
# Every "by hand" left on the README, in the sentence it belongs to.
ALLOWED = ("hand-coded study", "coded by hand", "Earlier studies coded samples by hand",
           "precision can be checked by hand", "new rules can be checked by hand",
           "label recall/labels.csv by hand")
# The same in exclusion_census.py: others' studies, and people who check the rules themselves.
ALLOWED_CODE = ("coded by hand", "coded samples by hand", "can be checked by hand", "Their hand-coded rates")
# SCORES-0.4.0.md keeps recall_sample.py's printed output unchanged, heading included.
SCORES_HEADING = "# Recall and precision of the word rules (hand-labelled sample)"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(path):
    return re.sub(r"\s+", " ", read(path))


class WordingTests(unittest.TestCase):
    def test_no_hand_or_eye_claims(self):
        for path in (README, ACCOMMODATION):
            self.assertEqual(CLAIMS.findall(flat(path)), [], os.path.basename(path))

    def test_every_by_hand_is_allowed(self):
        text = flat(README)
        for match in re.finditer(r"by hand|hand-coded", text):
            window = text[max(0, match.start() - 60):match.end() + 10]
            self.assertTrue(any(a in window for a in ALLOWED), window)

    def test_who_did_the_reading_is_named(self):
        readme = flat(README)
        for s in ("720 random flagged exclusion items were read by AI agents working for MV2 (not "
                  "yet checked by a person)",
                  "Every reading and label so far was done by AI agents working for MV2",
                  "All 225 were labelled by AI agents working for MV2, one reader per trial."):
            self.assertIn(s, readme)
        accommodation = flat(ACCOMMODATION)
        self.assertIn("Read on 2026-10-15 by an AI agent working for MV2 of Munim, Inc., one reader",
                      accommodation)
        self.assertIn("No person has checked this reading yet.", accommodation)

    def test_numbers_unchanged(self):
        readme = flat(README)
        for s in ("found only **5** that offer an accommodation (31%; Wilson 95% interval 14% to 56%)",
                  "60 per category, 360 of them in the six disability categories",
                  "(263 instead of 255)", "the first 114 trials, whose misses shaped 0.4.0"):
            self.assertIn(s, readme)
        accommodation = read(ACCOMMODATION)
        self.assertEqual(len(re.findall(r"^\| R\d{3} \|", accommodation, re.M)), 16)
        self.assertEqual(len(re.findall(r"^\| R\d{3} \|.*\| yes \|\s*$", accommodation, re.M)), 5)
        self.assertIn("That is 9 matches in 225, all offers, against 5 of 16 before",
                      flat(ACCOMMODATION))


class NoteWordingTests(unittest.TestCase):
    """The second pass: result notes, the v0.1.1 run page and the guide."""

    def test_no_hand_or_eye_claims(self):
        for path in NOTES:
            self.assertEqual(CLAIMS.findall(flat(path)), [], os.path.relpath(path, HERE))

    def test_scores_heading_is_the_only_one_and_is_explained(self):
        self.assertEqual(CLAIMS.findall(flat(SCORES)), ["hand-label"])
        self.assertIn(SCORES_HEADING, read(SCORES))
        self.assertIn("Its first heading is the title that `recall_sample.py` 0.2.0 printed (0.2.1 "
                      "prints \"labelled sample\" instead); the labels it refers to are these AI-agent "
                      "labels.", flat(SCORES))
        self.assertIn("They have not yet been checked by a person.", flat(SCORES))

    def test_who_did_the_reading_is_named(self):
        named = {
            "CONSENT-RESULT.md": "Labelled by AI agents working for MV2 of Munim, Inc.; not yet checked by a person.",
            "CONSENT-NEAR-VARIANT.md": "Labelled by AI agents working for MV2 of Munim, Inc.; not yet checked by a person.",
            "CONSENT-MISSED-READ.md": "Read by AI agents working for MV2; not yet checked by a person.",
            "PHONE-REQUIREMENT-RESULT.md": "one reader (AI agents working for MV2); no person has checked the reading.",
            "PHONE-MATCHED-RESULT.md": "first worked out by AI agents working for MV2, outside the code",
            "VA-CHECK.md": "Section 3 was read by AI agents working for MV2; no person has checked it yet.",
            "VA-MATCHED-RESULT.md": "first worked out by AI agents working for MV2, outside the code",
            "PREREG-v0.3-PERYEAR.md": "first worked out by AI agents working for MV2, outside the code.",
            "PRECISION.md": "The checker was an AI agent working for MV2 of Munim, Inc.",
            "inclusive-eligibility-guide.md": "read and labelled by AI agents working for MV2 and not yet "
                                              "checked by a person",
        }
        by_name = {os.path.basename(p): p for p in NOTES}
        for name, s in named.items():
            self.assertIn(s, flat(by_name[name]), name)
        va = flat(by_name["VA-CHECK.md"])
        self.assertIn("AI agents working for MV2 read the 12 VA trials", va)
        self.assertIn("no person has checked that reading yet", va)
        self.assertIn("No person has checked this reading yet.", flat(by_name["PRECISION.md"]))

    def test_numbers_next_to_the_changed_sentences(self):
        d = {os.path.basename(p): flat(p) for p in NOTES if os.path.basename(p) != "README.md"}
        self.assertIn("(263 instead of 255)", d["VA-CHECK.md"])
        self.assertIn("**All 12 use it in the exclusion criteria.**", d["VA-CHECK.md"])
        self.assertIn("(12 of 12 read were exclusions, a small sample)", d["VA-CHECK.md"])
        self.assertIn("add up to **255** (75 + 48 + 34 + 33 + 65)", d["VA-MATCHED-RESULT.md"])
        self.assertEqual(75 + 48 + 34 + 33 + 65, 255)
        self.assertIn("12 of 12 VA cognitive mentions read by AI agents working for MV2 were exclusions",
                      d["VA-MATCHED-RESULT.md"])
        self.assertIn("A seeded random sample of 50 of the 422 was read one by one", d["CONSENT-RESULT.md"])
        self.assertIn("all 59 read one by one from their snippets", d["CONSENT-NEAR-VARIANT.md"])
        self.assertIn("All 32 were read one by one", d["CONSENT-MISSED-READ.md"])
        self.assertIn("The 20 were read one by one against the two rules", d["PHONE-REQUIREMENT-RESULT.md"])
        self.assertIn("pattern marks (40 of 40)", d["PHONE-REQUIREMENT-RESULT.md"])
        precision = read(os.path.join(HERE, "results", "v0.1.1", "PRECISION.md"))
        self.assertEqual(len(re.findall(r"^\| [a-z_]+ \| \d+ / 60 \| \d+% ", precision, re.M)), 12)

    def test_guide_quotes_the_published_scores(self):
        guide, scores = flat(GUIDE), read(SCORES)
        self.assertIn("| any | 22 | 16 | 16/16 = 100% (81-100%) | 16/22 = 73% (52-87%) |", scores)
        self.assertIn("| any | 19 | 14 | 13/14 = 93% (69-99%) | 13/19 = 68% (46-85%) |", scores)
        self.assertIn("On 78 random trials labelled after the 0.4.0 rules were fixed, the rules flag 16 of "
                      "the 22 trials labelled as excluding someone by disability, and the "
                      "inclusion-requirement rules find 13 of 19 labelled requirements.", guide)
        self.assertIn("census rules 0.4.0; labelled trials: 78 random, 33 broad.", scores)
        self.assertIn("mv2@munimtech.com", guide)
        self.assertNotIn("munimversion2@gmail.com", guide)
        self.assertIn("- 0.3.1 (2026-10-18):", guide)


class CodeWordingTests(unittest.TestCase):
    """The third pass: the module text of exclusion_census.py and recall_sample.py."""

    def test_no_hand_or_eye_claims(self):
        for path in (CENSUS, RECALL):
            self.assertEqual(CLAIMS.findall(flat(path)), [], os.path.basename(path))

    def test_every_by_hand_is_allowed(self):
        text = flat(CENSUS)
        for match in re.finditer(r"by hand|hand-coded", text):
            window = text[max(0, match.start() - 60):match.end() + 10]
            self.assertTrue(any(a in window for a in ALLOWED_CODE), window)
        self.assertNotIn("by hand", flat(RECALL))

    def test_who_did_the_reading_is_named(self):
        census = flat(CENSUS)
        for s in ("after AI agents working for MV2 read 360 flagged items from the first full run",
                  "after AI agents working for MV2 labelled 114 trials of the blind recall sample",
                  "a reading of the 16 recall-sample trials it flagged, by an AI agent working for MV2, "
                  "found only 5 real offers",
                  "Every reading and label behind these rule changes was made by AI agents working for "
                  "MV2, one reader per item, and no person has checked them yet."):
            self.assertIn(s, census)

    def test_contact_address(self):
        census = read(CENSUS)
        self.assertIn('UA = "trial-exclusion-census/%s (Munim, Inc.; mv2@munimtech.com)" % __version__', census)
        self.assertNotIn("munimversion2@gmail.com", census)

    def test_recall_report_title(self):
        recall = read(RECALL)
        self.assertIn('SCORE_TITLE = "# Recall and precision of the word rules (labelled sample)"', recall)
        self.assertIn('__version__ = "0.2.1"', recall)


class TestFileWordingTests(unittest.TestCase):
    """The fourth pass: comments and docstrings in the tests that hold the published numbers."""

    def test_no_hand_or_eye_claims(self):
        for path in TESTS:
            text = flat(path)
            self.assertEqual(CLAIMS.findall(text), [], os.path.basename(path))
            self.assertNotIn("by hand", text, os.path.basename(path))

    def test_who_did_the_work_is_named(self):
        for path in TESTS[1:]:
            text = flat(path)
            self.assertIn("worked out outside the code by AI agents working for MV2 on 2026-10-15", text,
                          os.path.basename(path))
            self.assertIn("no person has checked them yet.", text, os.path.basename(path))
        census = flat(TESTS[0])
        self.assertIn("false positives that AI agents working for MV2 found when they read the first full "
                      "run's sample_items.csv", census)
        self.assertIn("as labelled by AI agents working for MV2 (one reader; no person has checked the "
                      "labels yet)", census)


if __name__ == "__main__":
    unittest.main()
