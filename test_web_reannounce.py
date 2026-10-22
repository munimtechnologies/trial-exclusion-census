"""Keeps the browser checker's (web/check.html) fallback messages heard on every press. Apache-2.0.

In a browser that cannot run the checker, a small script ahead of it answers both buttons in the
status line. Like the checker's own say(), it clears the status first and sets the message a
moment later, so a screen reader announces it again when the same button is pressed twice.
"""

import os
import re
import unittest

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "check.html")
RULES = '<script type="text/plain" id="rules">'
SET = 'document.getElementById("status").textContent = '


class WebReannounceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(PAGE, encoding="utf-8") as f:
            cls.html = f.read()
        cls.guard = cls.html[cls.html.index("<script>"):cls.html.index(RULES)]

    def test_guard_never_sets_a_message_directly(self):
        self.assertEqual(re.findall(r'^\s*' + re.escape(SET) + r'"[^"]+";', self.guard, re.M), [])

    def test_guard_clears_then_sets_each_message(self):
        later = re.findall(re.escape(SET) + r'"";\n\s*setTimeout\(function \(\) \{ ' + re.escape(SET)
                           + r'"([^"]+)"; \}, 100\);', self.guard)
        self.assertEqual(len(later), 2)
        self.assertTrue(all(m.startswith("This browser could not run the check") for m in later))


if __name__ == "__main__":
    unittest.main()
