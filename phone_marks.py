"""phone_marks: the two marks of PREREG-PHONE-REQUIREMENT's S2 reading, applied by pattern.

S2 reads the first 20 trials of phone_requirement.reading_term() by eye and marks (a) an inclusion
item names a phone and (b) the hearing item itself names a phone or calls. This applies the same
two rules by pattern, so the reading by eye has a check written before the reading list was
fetched. Each record's criteria are split into items under their inclusion and exclusion
headings; a record with no hearing item found, or no heading, is flagged for the reader instead of
guessed. The reading by eye stays the pre-registered result; where the two differ, both are shown.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import json
import re
import sys

__version__ = "0.1.0"

READ = "results/phone-check/phone-hearing-read.json"
# The rules of PREREG-PHONE-REQUIREMENT, S2. (a) is case-insensitive, so it also finds telephone
# and smartphone; (b) is the rule of PHONE-HEARING-READ.
REQUIREMENT = re.compile(r"phone", re.I)
TIED = re.compile(r"phone|\bcalls?\b", re.I)
# An item that names hearing. The registry search also matched wordings outside the family's own
# phrases ("no hearing or vision impairment", "impaired hearing"), so any hear- or deaf- word,
# but not heart.
HEARING = re.compile(r"\b(?:hear(?!t)|deaf)", re.I)
BULLET = re.compile(r"^\s*(?:[*\-•]|\d{1,2}[.)]|[a-z][.)]|\(\w{1,3}\))\s+")
# A heading starts with inclusion or exclusion, after at most two words such as "key" or
# "patient", so an item like "does not meet inclusion criteria" is not one.
HEADING = re.compile(r"^(?:(?:key|main|general|major|other|additional|specific|study|patient|"
                     r"participant|caregiver|parent|child|subject|healthy|volunteer)s?\s+){0,2}"
                     r"(inclusion|exclusion)\b")
PREDICTED_A = 12
TIED_RULE = 11


def heading(line):
    """'inclusion' or 'exclusion' if the line is a criteria heading, 'unknown' if it names both."""
    text = BULLET.sub("", line).strip().strip("*_#").strip().lower()
    m = HEADING.match(text)
    if not m or len(text) > 80 or not ("criteri" in text or text.endswith(":")):
        return None
    other = "exclusion" if m.group(1) == "inclusion" else "inclusion"
    return "unknown" if other in text else m.group(1)


def items(criteria):
    """[section, text] for each item of a record's criteria, in order. A line that is not a
    bullet and follows a non-blank line continues the item before it."""
    out, section, gap = [], "unknown", True
    for line in (criteria or "").splitlines():
        if not line.strip():
            gap = True
            continue
        h = heading(line)
        if h:
            section, gap = h, True
            continue
        text = BULLET.sub("", line).strip()
        if gap or BULLET.match(line) or not out:
            out.append([section, text])
        else:
            out[-1][1] += " " + text
        gap = False
    return out


def mark(row):
    """The marks for one record of the reading list."""
    its = items(row.get("criteria"))
    hearing = [i for i in its if HEARING.search(i[1])]
    phone = [t for s, t in its if s == "inclusion" and REQUIREMENT.search(t)]
    check = []
    if not hearing:
        check.append("no hearing item found")
    if all(s == "unknown" for s, _ in its):
        check.append("no inclusion or exclusion heading")
    return {"nct": row.get("nct"), "title": row.get("title"), "hearing_items": hearing,
            "inclusion_phone_items": phone, "a_requirement": bool(phone),
            "b_phone_tied": any(TIED.search(t) for _, t in hearing), "check_by_eye": check}


def overlaps(marks, read):
    """Records also read for PHONE-HEARING-READ, with the group they were read in."""
    seen = {r["nct"]: g for g, grp in read["groups"].items() for r in grp["rows"]}
    return [{"nct": m["nct"], "group": seen[m["nct"]]} for m in marks if m["nct"] in seen]


def summary(marks):
    a = sum(m["a_requirement"] for m in marks)
    b = sum(m["b_phone_tied"] for m in marks)
    return {"trials": len(marks), "a_requirement": a, "b_phone_tied": b,
            "check_by_eye": sum(bool(m["check_by_eye"]) for m in marks),
            "a_prediction_met": a >= PREDICTED_A, "b_tied_rule_met": b >= TIED_RULE}


def markdown(marks, over=None):
    s = summary(marks)
    lines = ["| NCT | (a) requirement | (b) phone-tied | Check by eye |", "|---|---|---|---|"]
    for m in marks:
        lines.append("| %s | %s | %s | %s |" % (
            m["nct"], "yes" if m["a_requirement"] else "no", "yes" if m["b_phone_tied"] else "no",
            "; ".join(m["check_by_eye"]) or "-"))
    lines += ["", "By pattern: (a) in %d of %d (predicted at least %d: %s); (b) in %d of %d (at least "
              "%d would make HP1 mostly the hearing items' own wording: %s); %d to check by eye." % (
                  s["a_requirement"], s["trials"], PREDICTED_A,
                  "met" if s["a_prediction_met"] else "not met", s["b_phone_tied"], s["trials"],
                  TIED_RULE, "yes" if s["b_tied_rule_met"] else "no", s["check_by_eye"])]
    if over is not None:
        lines += ["", "Also read for PHONE-HEARING-READ: %s." % (
            ", ".join("%s (%s)" % (o["nct"], o["group"]) for o in over) or "none")]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("reading_list", help="s2-reading-list.json, as fetch_reading.py saves it")
    ap.add_argument("--read", default=READ, help="phone-hearing-read.json, for the overlaps ('' to skip)")
    ap.add_argument("--json", help="also write the marks and the summary to this file")
    args = ap.parse_args(argv)
    with open(args.reading_list, encoding="utf-8") as f:
        data = json.load(f)
    marks = [mark(r) for r in data["rows"]]
    over = None
    if args.read:
        with open(args.read, encoding="utf-8") as f:
            over = overlaps(marks, json.load(f))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"version": __version__, "query": data.get("query"), "total": data.get("total"),
                       "summary": summary(marks), "overlaps": over, "marks": marks}, f, indent=1)
    print(markdown(marks, over))
    return 0


if __name__ == "__main__":
    sys.exit(main())
