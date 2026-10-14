"""Keeps the browser checker (web/check.html) on exactly the rules in exclusion_census.py. Apache-2.0."""

import os
import re
import unittest

import exclusion_census as ec

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "check.html")


def expected_rules():
    rows = [("rule", cat, p) for cat, pats in ec.PATTERNS.items() for p in pats]
    rows.append(("accommodation", "-", ec.ACCOMMODATION.pattern))
    rows += [("related", k, v.pattern) for k, v in ec.CONDITION_RELATED.items()]
    rows += [("suggest", k, v) for k, v in ec.SUGGESTIONS.items()]
    rows += [("header", "-", ec.HEADER.pattern), ("inline", "-", ec.INLINE_EXCLUSION.pattern),
             ("bullet", "-", ec.BULLET.pattern)]
    return rows


class WebCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(PAGE, encoding="utf-8") as f:
            cls.html = f.read()

    def page_rules(self):
        m = re.search(r'<script type="text/plain" id="rules">(.*?)</script>', self.html, re.S)
        self.assertIsNotNone(m, "rules block missing")
        return [tuple(line.split(" ", 2)) for line in m.group(1).splitlines() if line.strip()]

    def test_rules_match_python(self):
        self.assertEqual(self.page_rules(), expected_rules())

    def test_categories_in_order(self):
        cats = []
        for kind, key, _ in self.page_rules():
            if kind == "rule" and key not in cats:
                cats.append(key)
        self.assertEqual(tuple(cats), ec.CATEGORIES)

    def test_page_basics(self):
        self.assertIn('<html lang="en">', self.html)
        self.assertIn('<label for="criteria">', self.html)
        self.assertIn('role="status"', self.html)
        # Nothing loaded from elsewhere: the pasted text never leaves the page.
        self.assertNotRegex(self.html, r"<script[^>]+src=|<link[^>]+stylesheet|fetch\(|XMLHttpRequest")


if __name__ == "__main__":
    unittest.main()
