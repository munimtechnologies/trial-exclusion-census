"""Keeps the colours of the browser checker (web/check.html) readable. Apache-2.0.

Each pair is a colour and the colour it sits on in the page, with the minimum contrast its WCAG 2.2
success criterion sets: 4.5:1 for text (1.4.3 Contrast (Minimum)) and 3:1 for the borders and focus
outline that show a control and its state (1.4.11 Non-text Contrast). The ratio is WCAG's, from the
relative luminance of each sRGB colour. Every colour the page's style sheet sets must be in a pair.
"""

import os
import re
import unittest

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "check.html")
TEXT, NON_TEXT = 4.5, 3.0
INPUT = "textarea, input[type=text]"

# (what, (rule, property) of the colour, (rule, property) of what it sits on, minimum)
PAIRS = [
    ("body text", ("body", "color"), ("body", "background"), TEXT),
    ("links", ("a", "color"), ("body", "background"), TEXT),
    ("hints under the labels", (".hint", "color"), ("body", "background"), TEXT),
    ("footer", ("footer", "color"), ("body", "background"), TEXT),
    ("typed text", (INPUT, "color"), (INPUT, "background"), TEXT),
    ("'Check criteria' button", ("button", "color"), ("button", "background"), TEXT),
    ("'Load an example' button", ("button.secondary", "color"), ("button.secondary", "background"), TEXT),
    ("flagged item", ("body", "color"), (".item", "background"), TEXT),
    ("item that offers an accommodation", ("body", "color"), (".offered", "background"), TEXT),
    ("note that an item matches the study's subject", (".related", "color"), ("body", "background"), TEXT),
    ("text box border", (INPUT, "border"), ("body", "background"), NON_TEXT),
    ("button border", ("button", "border"), ("body", "background"), NON_TEXT),
    ("focus outline", (":focus-visible", "outline"), ("body", "background"), NON_TEXT),
    ("bar beside a flagged item", (".item", "border-left"), ("body", "background"), NON_TEXT),
    ("bar beside an offered item", (".offered", "border-left"), ("body", "background"), NON_TEXT),
]


def rules_of(html):
    """Each rule of the page's one style sheet, as {selector: {property: value}}."""
    sheet = html[html.index("<style>") + len("<style>"):html.index("</style>")]
    rules = {}
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", sheet):
        selector = selector.strip()
        if selector in rules:
            raise ValueError("rule repeated: " + selector)
        decls = (d.split(":", 1) for d in body.split(";") if d.strip())
        rules[selector] = {p.strip(): v.strip() for p, v in decls}
    return rules


def colour(value):
    """The one hex colour in a declaration's value, as six lower-case hex digits."""
    found = re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", value)
    if len(found) != 1:
        raise ValueError("expected one hex colour in " + repr(value))
    h = found[0].lower()
    return h if len(h) == 6 else "".join(c * 2 for c in h)


def luminance(hex6):
    """WCAG relative luminance of an sRGB colour given as six hex digits."""
    def linear(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (linear(int(hex6[i:i + 2], 16)) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    """WCAG contrast ratio of two colours, from 1 to 21."""
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def is_colour_property(prop):
    return prop == "color" or (prop.startswith(("background", "border", "outline"))
                               and prop not in ("border-radius", "outline-offset"))


class WebContrastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(PAGE, encoding="utf-8") as f:
            cls.html = f.read()
        cls.rules = rules_of(cls.html)

    def test_ratio_matches_known_values(self):
        self.assertAlmostEqual(ratio("000000", "ffffff"), 21.0, places=6)
        self.assertAlmostEqual(ratio("767676", "ffffff"), 4.54, delta=0.01)
        self.assertLess(ratio("777777", "ffffff"), 4.5)
        self.assertEqual(colour("2px solid #fff"), "ffffff")

    def test_one_style_sheet_and_no_inline_colours(self):
        self.assertEqual(self.html.count("<style>"), 1)
        self.assertNotIn(" style=", self.html)
        self.assertNotIn(".style.", self.html)

    def test_every_colour_is_in_a_pair(self):
        paired = {side for _, fg, bg, _ in PAIRS for side in (fg, bg)}
        for selector, decls in self.rules.items():
            for prop in decls:
                if is_colour_property(prop):
                    self.assertIn((selector, prop), paired)

    def test_inherited_colours_are_the_paired_ones(self):
        # Pairs that take a colour from another rule hold only while these rules leave it unset.
        for selector in (".item", ".offered"):
            self.assertNotIn("color", self.rules[selector])
        for selector in ("a", ".hint", "footer", ".related", ":focus-visible"):
            self.assertFalse([p for p in self.rules[selector] if p.startswith("background")])

    def test_pairs_meet_their_minimum(self):
        for what, (fs, fp), (bs, bp), minimum in PAIRS:
            with self.subTest(what):
                r = ratio(colour(self.rules[fs][fp]), colour(self.rules[bs][bp]))
                self.assertGreaterEqual(r, minimum, f"{what}: {r:.2f}:1")


if __name__ == "__main__":
    unittest.main()
