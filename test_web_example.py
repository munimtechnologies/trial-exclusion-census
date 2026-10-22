"""Keeps the example button on the browser checker (web/check.html) from failing silently. Apache-2.0.

In a browser that cannot run the checker, the checker never sets its own listeners, so a small
script ahead of it answers the "Load an example" button in the status line.
"""

import os
import unittest

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "check.html")
RULES = '<script type="text/plain" id="rules">'


class WebExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(PAGE, encoding="utf-8") as f:
            cls.html = f.read()

    def test_example_answered_before_checker_loads(self):
        guard = self.html.index('document.getElementById("example").addEventListener("click"')
        self.assertLess(guard, self.html.index(RULES))
        body = self.html[guard:self.html.index("});", guard)]
        self.assertIn("if (!window.checkReady)", body)
        self.assertIn('document.getElementById("status").textContent', body)

    def test_button_and_status_are_the_ones_named(self):
        self.assertEqual(self.html.count('id="example"'), 1)
        self.assertEqual(self.html.count('id="status"'), 1)
        self.assertIn('type="button" class="secondary" id="example"', self.html)


if __name__ == "__main__":
    unittest.main()
