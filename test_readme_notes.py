"""Offline tests for the README's consent and phone-requirement parts (no network). Apache-2.0.

Each number those parts quote must be the number in the note it summarises; each note's own test
recomputes the note from its data. Where the note has the table, the number is recomputed here too.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HERE, "README.md")
CONSENT = os.path.join(HERE, "results", "consent-phrase")
PHONE = os.path.join(HERE, "results", "phone-check")


def read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read()


class ReadmeNoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = read(README)

    def check(self, note, pairs):
        for in_readme, in_note in pairs:
            self.assertIn(in_readme, self.readme)
            self.assertIn(in_note, note)

    def test_consent_result(self):
        note = read(CONSENT, "CONSENT-RESULT.md")
        self.check(note, [("(5,473 trials, on 2026-10-16)", "The search found 5,473 trials"),
                          ("4,059 trials have the exact line, and 422 of them (10.4%)",
                           "422 of 4,059 (10.4%)"),
                          ("Of 50 of these read by eye, 30 let someone else consent",
                           "Adult permission: 30 of 50"),
                          ("about **6.2%** (4.8% to 7.5%)", "6.2% (4.8-7.5)"),
                          ("path 4.3% of the time, those that started 2020-2026 19.2%",
                           "| 2019 or earlier | 2,419 | 103 | 4.3 |")])
        self.assertIn("| 2020-2026 | 1,587 | 304 | 19.2 |", note)
        self.assertEqual(round(100 * 103 / 2419, 1), 4.3)
        self.assertEqual(round(100 * 304 / 1587, 1), 19.2)
        self.assertEqual(round(100 * 422 / 4059, 1), 10.4)

    def test_near_variant(self):
        note = read(CONSENT, "CONSENT-NEAR-VARIANT.md")
        self.check(note, [("1,377 more trials use a near variant", "1,377 more trials"),
                          ("197 of them (14.3%)", "197 of 1,377 (14.3%)"),
                          ("about 450 of 5,436 trials (8.3%)", "about 450 trials (392-502) of the 5,436")])
        self.assertIn("8.3% (7.2-9.2)", note)
        self.assertIn("| all | 244 | 197 |", note)
        self.assertEqual(round(100 * 197 / 1377, 1), 14.3)
        self.assertEqual(4059 + 1377, 5436)

    def test_consent_missed(self):
        note = read(CONSENT, "CONSENT-MISSED-READ.md")
        self.check(note, [("none of the 32 lets another person consent", "All 32 were read by eye"),
                          ("(26 are contraception items)", "time of consent | 26 |")])
        self.assertIn("| Lets another person consent for the participant | 0 |", note)

    def test_phone_requirement(self):
        note = read(PHONE, "PHONE-REQUIREMENT-RESULT.md")
        self.check(note, [("(1,890 of 7,421 on the counting day)", "the base had 7,421 trials"),
                          ("**2.58 times** (2.04 to 3.24)",
                           "| hearing (all wordings) | family | 128 | 49.7 | 2.58 (2.04-3.24) |"),
                          ("against 1.62 for visual wordings",
                           "| visual (all wordings) | family | 64 | 39.8 | 1.62 (1.20-2.18) |"),
                          ("S1 p = 0.0083", "rank sum 27.0, p = 0.0083"),
                          ("phone-access condition appears in 16 of 20", "condition appears in 16 of 20")])
        self.assertIn("1,890 name a phone", note)
        controls = [float(r) for r in re.findall(r"^\| [a-z ]+ \| control \| \d+ \| [\d.]+ \| ([\d.]+) \(",
                                                 note, re.M)]
        self.assertEqual(len(controls), 7)
        self.assertIn("at most %.2f for a kept" % max(controls), self.readme)
        marks = re.findall(r"^\| NCT\d{8} \| (yes|no) \| (yes|no) \|\s*$", note, re.M)
        self.assertEqual(len(marks), 20)
        self.assertEqual(sum(b == "yes" for _, b in marks), 12)
        self.assertIn("%d of 20 trials read the hearing item itself names" % sum(b == "yes" for _, b in marks),
                      self.readme)
        self.assertIn("in 12 of 20 trials read", note)


if __name__ == "__main__":
    unittest.main()
