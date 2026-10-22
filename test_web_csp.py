"""Keeps the browser checker (web/check.html) from sending what is pasted into it. Apache-2.0.

The page's Content-Security-Policy has the browser block every connection and form submission,
and a small script stops the form even in a browser that cannot run the checker itself.
"""

import os
import re
import unittest

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "check.html")
CSP = re.compile(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)">')


def directives(policy):
    out = {}
    for part in policy.split(";"):
        words = part.split()
        if words:
            out[words[0]] = words[1:]
    return out


class WebCspTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(PAGE, encoding="utf-8") as f:
            cls.html = f.read()

    def policy(self):
        found = CSP.findall(self.html)
        self.assertEqual(len(found), 1, "one Content-Security-Policy meta tag")
        return directives(found[0])

    def test_policy_blocks_connections_and_forms(self):
        d = self.policy()
        self.assertEqual(d.get("default-src"), ["'none'"])
        self.assertEqual(d.get("form-action"), ["'none'"])
        self.assertEqual(d.get("base-uri"), ["'none'"])
        # Inline code and styles only: no address, scheme or wildcard anywhere in the policy.
        self.assertEqual(d.get("script-src"), ["'unsafe-inline'"])
        self.assertEqual(d.get("style-src"), ["'unsafe-inline'"])
        self.assertEqual(set(d), {"default-src", "script-src", "style-src", "form-action", "base-uri"})

    def test_policy_comes_first(self):
        # A policy in a meta tag only covers what comes after it.
        at = CSP.search(self.html).start()
        self.assertLess(self.html.index('<meta charset="utf-8">'), at)
        self.assertLess(at, self.html.index("<style>"))
        self.assertNotIn("<script", self.html[:at])

    def test_form_stopped_before_checker_loads(self):
        guard = self.html.index('document.getElementById("form").addEventListener("submit"')
        self.assertLess(guard, self.html.index('<script type="text/plain" id="rules">'))
        self.assertIn("e.preventDefault();", self.html[guard:guard + 200])
        # The checker says it is ready only once its own listeners are set.
        self.assertLess(self.html.rindex("addEventListener"), self.html.index("window.checkReady = true;"))
        self.assertNotIn(" action=", self.html)

    def test_nothing_the_policy_cannot_block(self):
        # Navigation is outside the policy, so the page must not navigate, open windows or beacon.
        self.assertNotRegex(self.html, r"\blocation\b|window\.open|sendBeacon|javascript:|\son[a-z]+=")

    def test_page_says_so(self):
        self.assertIn("security policy also tells your browser to block", self.html)
        self.assertIn("<noscript>", self.html)


if __name__ == "__main__":
    unittest.main()
