# Accessibility of the browser check (web/check.html)

This is what has been checked about the accessibility of `check.html`, MV2's free inclusive
eligibility check, and what has not. It is not a claim of conformance with WCAG or any other standard.

## Checked so far

On 2026-10-23 (about 00:44 UTC) an AI agent working for MV2 used the page in Chrome 155.0.8059.85 on
Windows 10, opened from a local copy byte-for-byte identical to `web/check.html` at commit dc408b87
(SHA-256 `f82b9c0b8ec2b1714464a8ef29b7abd493a82f40da2d442c8cc8cf41c2170c90`). The expected results
were written down from the page source before the check, and every one held.

| What | Result | Related WCAG 2.2 criterion |
|---|---|---|
| Keyboard only | All 7 controls and links reached with Tab, in this order: the criteria box, the condition field, "Check criteria", "Load an example", then the three links | 2.1.1 Keyboard, 2.4.3 Focus Order |
| Keyboard trap | None: Tab leaves the large text box normally | 2.1.2 No Keyboard Trap |
| Visible focus | An outline showed on every stop, and still showed at 400% zoom | 2.4.7 Focus Visible |
| Buttons | "Load an example" works with both Enter and Space | 2.1.1 Keyboard |
| Names and roles (Chrome's accessibility tree) | Text box "Eligibility criteria", text box "The study's condition or title (optional)", buttons "Check criteria" and "Load an example" | 4.1.2 Name, Role, Value |
| Result announcement | The results line has role `status`, polite and atomic, so screen readers can announce it without moving focus | 4.1.3 Status Messages |
| 400% zoom | One column, no sideways scrolling, nothing overlapping or cut off | 1.4.4 Resize Text, 1.4.10 Reflow (see limits) |
| Privacy | The network panel showed only the page itself; checking criteria sent no request, and pressing Enter in a field did not change the address or reload. The console showed no errors. | not an accessibility criterion |

### Colour contrast

Also on 2026-10-23, every colour the page's style sheet sets was measured with WCAG's contrast
ratio, from the style sheet of `web/check.html` at commit dc408b87 (unchanged since). The expected
ratios were worked out by hand and written down before the code ran, and all 15 matched.
`test_web_contrast.py` keeps it that way: it fails if a pair drops below its minimum, if the style
sheet gains a colour that is in no pair, or if a colour the pairs rely on is overridden.

| Pair | Colours | Ratio | Minimum |
|---|---|---|---|
| Body text, typed text | #1b1b1b on #ffffff | 17.22:1 | 4.5:1 (1.4.3) |
| Links, both buttons' text | #0b4fb3 and #ffffff | 7.54:1 | 4.5:1 (1.4.3) |
| Hints under the labels, footer | #444444 on #ffffff | 9.74:1 | 4.5:1 (1.4.3) |
| Flagged item | #1b1b1b on #f3f3f3 | 15.52:1 | 4.5:1 (1.4.3) |
| Item that offers an accommodation | #1b1b1b on #eef6ef | 15.64:1 | 4.5:1 (1.4.3) |
| Note that an item matches the study's subject | #5a3d00 on #ffffff | 9.99:1 | 4.5:1 (1.4.3) |
| Text box border, bar beside a flagged item | #555555 on #ffffff | 7.46:1 | 3:1 (1.4.11) |
| Button border | #0b4fb3 on #ffffff | 7.54:1 | 3:1 (1.4.11) |
| Focus outline | #b3410b on #ffffff | 5.71:1 | 3:1 (1.4.11) |
| Bar beside an offered item | #1a6b2f on #ffffff | 6.59:1 | 3:1 (1.4.11) |

The lowest text pair is 7.54:1, so all text also meets the enhanced 7:1 of 1.4.6. The lowest
non-text pair is the focus outline, 5.71:1. Visited links keep #0b4fb3, because the page's link
colour applies to every link state. Flagged and accommodating items are not told apart by colour
alone: each group has its own heading, and flagged items carry a "Categories:" or "Requires:" line
(1.4.1 Use of Color).

## Not checked yet

- **No disabled person has tested the page yet, and no screen reader has been used on it.** The role and
  live-region values come from Chrome's accessibility tree, not from hearing NVDA, JAWS, VoiceOver or
  TalkBack read the page.
- Reflow was checked in a 1920-pixel window, so 400% zoom gave a 480 CSS-pixel-wide view. WCAG's reflow
  test uses 320 CSS pixels. Narrower views and phones have not been checked.
- The contrast figures are for the colours the style sheet declares, not measured screen pixels. The
  text caret and selected-text colours are the browser's own and were not measured. Newer methods such
  as APCA (in drafts of WCAG 3) were not used.
- Windows high-contrast (forced colours) mode, which replaces the page's colours, speech input and
  switch access have not been checked.
- Only Chrome on Windows was used. Firefox and Safari were not. (Safari before 16.4 cannot run the
  checker, and the page says so in its status line.)
- The page has no hosted address yet. These results are for the file, opened in a browser.

## Reporting a problem

If something in the page does not work with the way you use a computer, please say so on this
repository's issues page, or write to MV2, Munim, Inc., mv2@munimtech.com. Reports from people who use
assistive technology are the most useful thing this page can get.

Made by MV2 of Munim, Inc. with AI agents. Apache-2.0, like the rest of this repository.
