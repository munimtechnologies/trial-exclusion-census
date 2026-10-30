"""consent_permission: are the stock consent line's representative mentions real adult permissions?

Two steps, written down before any sampled trial was read (results/consent-permission/PREREG.md):

  sample  takes the trials of results/consent-sponsor/consent-sponsor-trials.csv (commit dfa8206)
          that name a representative, guardian or surrogate, draws a seeded sample from three
          sponsor groups (NCI-linked, WashU-led, Neither), fetches each sampled trial's current
          eligibility text from the ClinicalTrials.gov API v2, and writes a blind reading file
          (no NCT ids, no sponsors) and a separate key.
  grade   joins the reader's labels with the key and grades the pre-registered predictions.

The reading itself is done by AI agents working for MV2, with the categories of the 2026-10-16
reading (results/consent-phrase/consent-read.json).

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import csv
import hashlib
import io
import json
import math
import random
import re
import sys
import time
import urllib.parse
import urllib.request

__version__ = "0.1.0"

SPONSOR_COMMIT = "dfa820661d6c06ec4eddee5e0ce1513c069a4dc6"
SPONSOR_URL = ("https://raw.githubusercontent.com/munimtechnologies/trial-exclusion-census/%s/"
               "results/consent-sponsor/consent-sponsor-trials.csv" % SPONSOR_COMMIT)
API = "https://clinicaltrials.gov/api/v2/studies"
FIELDS = "NCTId,BriefTitle,EligibilityCriteria,MinimumAge,MaximumAge,StdAge"
USER_AGENT = "consent_permission/%s (MV2 of Munim, Inc.; mv2@munimtech.com)" % __version__

SPONSOR_HEADER = ["nct_id", "start_year", "stock_exact", "adult_only", "adult_path",
                  "lead_sponsor", "lead_class", "nci_linked", "washu_led"]

# The published counts the sponsor table must reproduce (CONSENT-SPONSOR-RESULT.md).
EXPECTED = {"rows": 5436,
            "nci_linked": (278, 1570), "washu_led": (165, 224), "neither": (241, 3666),
            "both": (18, 24)}

# Pre-registered sample (PREREG.md). Changing any of these after the sample is drawn voids it.
SEED = 20261030
GROUPS = (("nci", 40), ("washu", 20), ("neither", 40))
MIN_FETCHED = 98
MIN_STILL_PRESENT = 95
EXCERPT_CAP = 4000

LABELS = ("adult_permission", "physical_only", "minor_only", "unclear", "not_a_permission",
          "path_gone")

# Pre-registered thresholds (PREREG.md). Changing any of these after reading voids the test.
R1_MIN_DIFF = 0.15
R2_MIN_NCI = 0.70
R3_MAX_NEITHER = 0.60
R4_MIN_WASHU = 0.80
R5_MIN_OWNER_SHARE = 0.70

# The same patterns as consent_phrase_check (representative, guardian, surrogate).
PATHS = {
    "representative": re.compile(
        r"\blegal(?:ly)?[\s-]+(?:authori[sz]ed\s+|acceptable\s+)?representatives?\b"
        r"|\bauthori[sz]ed\s+representatives?\b|\b(?-i:LARs?)\b", re.I),
    "guardian": re.compile(r"\bguardians?\b|\bconservators?\b", re.I),
    "surrogate": re.compile(
        r"\bsurrogates?\b|\bprox(?:y|ies)\b|\bnext\s+of\s+kin\b"
        r"|\bhealth\s*care\s+agents?\b|\bsubstitute\s+decision", re.I),
}
CONSENT = re.compile(r"\bconsent", re.I)
HEADING = re.compile(r"^\W*(inclusion|exclusion)\b[^.]{0,40}criteria", re.I)


def truthy(v):
    return str(v).strip() == "True"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url, tries=4, timeout=60):
    """GET a URL, retrying with a growing pause; raises the last error."""
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # network errors are retried, then raised
            err = e
            time.sleep(2 * (i + 1))
    raise err


def fetch_json(url):
    return json.loads(fetch_bytes(url).decode("utf-8"))


def read_csv(data):
    reader = csv.reader(io.StringIO(data.decode("utf-8")))
    header = next(reader)
    return header, [dict(zip(header, r)) for r in reader if r]


def group_of(row):
    """'nci', 'washu', 'neither' or 'both' for one sponsor-table row."""
    n, w = truthy(row["nci_linked"]), truthy(row["washu_led"])
    if n and w:
        return "both"
    return "nci" if n else "washu" if w else "neither"


def counts(rows):
    """(trials naming a path, trials) per published group; nci_linked and washu_led overlap."""
    def c(sel):
        return (sum(1 for r in sel if truthy(r["adult_path"])), len(sel))
    return {"nci_linked": c([r for r in rows if truthy(r["nci_linked"])]),
            "washu_led": c([r for r in rows if truthy(r["washu_led"])]),
            "neither": c([r for r in rows if group_of(r) == "neither"]),
            "both": c([r for r in rows if group_of(r) == "both"])}


def sample_gates(header, rows, expected=EXPECTED):
    got = counts(rows)
    return {"S1_table": header == SPONSOR_HEADER and len(rows) == expected["rows"],
            "S2_counts": all(tuple(got[k]) == tuple(expected[k]) for k in got)}, got


def draw(rows, seed=SEED, groups=GROUPS):
    """The seeded sample: {group: [nct ids]}, each drawn from the sorted ids naming a path."""
    rng = random.Random(seed)
    out = {}
    for g, n in groups:
        ids = sorted(r["nct_id"] for r in rows if truthy(r["adult_path"]) and group_of(r) == g)
        out[g] = rng.sample(ids, n)
    return out


def blind_order(ids, seed=SEED):
    """{nct id: 'R001', ...} in an order fixed by a hash, unrelated to the group."""
    key = sorted(ids, key=lambda i: sha256(("%d:%s" % (seed, i)).encode()))
    return {nct: "R%03d" % (k + 1) for k, nct in enumerate(key)}


def study_record(study):
    ps = study.get("protocolSection", {})
    el = ps.get("eligibilityModule", {})
    return ps.get("identificationModule", {}).get("nctId"), {
        "title": ps.get("identificationModule", {}).get("briefTitle", ""),
        "criteria": el.get("eligibilityCriteria", ""),
        "min_age": el.get("minimumAge", ""), "max_age": el.get("maximumAge", ""),
        "std_ages": el.get("stdAges", [])}


def fetch_studies(ids, fetch=None):
    fetch = fetch or fetch_json
    params = {"filter.ids": ",".join(ids), "fields": FIELDS, "pageSize": 1000, "format": "json"}
    out, token = {}, None
    while True:
        if token:
            params["pageToken"] = token
        page = fetch(API + "?" + urllib.parse.urlencode(params))
        for s in page.get("studies", []):
            nct, rec = study_record(s)
            if nct:
                out[nct] = rec
        token = page.get("nextPageToken")
        if not token:
            return out


def path_terms(text):
    return [n for n, p in PATHS.items() if p.search(text or "")]


def excerpt(criteria, cap=EXCERPT_CAP):
    """Lines naming a path or consent, one line either side, each tagged with its section."""
    lines = [l.strip() for l in (criteria or "").splitlines() if l.strip()]
    section, sections = "before any heading", []
    for l in lines:
        if HEADING.match(l):
            section = HEADING.match(l).group(1).lower()
        sections.append(section)
    hit = [bool(path_terms(l) or CONSENT.search(l)) for l in lines]
    keep = set()
    for i, h in enumerate(hit):
        if h:
            keep.update(j for j in (i - 1, i, i + 1) if 0 <= j < len(lines))
    out, last = [], None
    for i in sorted(keep):
        if last is not None and i != last + 1:
            out.append("    ...")
        out.append("    [%s]%s %s" % (sections[i], " *" if path_terms(lines[i]) else "", lines[i]))
        last = i
    text = "\n".join(out)
    if len(text) > cap:
        text = text[:cap] + "\n    [cut at %d characters]" % cap
    return text


def years(age):
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*(year|month|week|day)s?\b", age or "", re.I)
    if not m:
        return None
    f = {"year": 1, "month": 1 / 12, "week": 1 / 52, "day": 1 / 365}[m.group(2).lower()]
    return float(m.group(1)) * f


def reading_block(rid, rec):
    lo = years(rec["min_age"])
    adult = "unknown" if lo is None else "yes" if lo >= 18 else "no"
    terms = path_terms(rec["criteria"])
    return "\n".join([
        "## %s" % rid,
        "Title: %s" % rec["title"],
        "Ages: minimum %s; maximum %s; age groups %s; adult-only: %s" % (
            rec["min_age"] or "not given", rec["max_age"] or "not given",
            ", ".join(rec["std_ages"]) or "not given", adult),
        "Path terms in today's text: %s" % (", ".join(terms) if terms else "none"),
        "Excerpt (* = names a representative, guardian or surrogate):",
        excerpt(rec["criteria"]), ""])


def run_sample(sponsor_bytes, fetch=None):
    header, rows = read_csv(sponsor_bytes)
    g, got = sample_gates(header, rows)
    result = {"version": __version__, "sponsor_url": SPONSOR_URL,
              "sponsor_sha256": sha256(sponsor_bytes), "seed": SEED, "groups": dict(GROUPS),
              "gates": g, "counts": got, "sample": None}
    if not all(g.values()):
        return result, None, None
    picked = draw(rows)
    ids = [i for grp, _ in GROUPS for i in picked[grp]]
    studies = fetch_studies(ids, fetch=fetch)
    order = blind_order(ids)
    present = sum(1 for i in ids if i in studies and path_terms(studies[i]["criteria"]))
    g["S3_fetched"] = sum(1 for i in ids if i in studies) >= MIN_FETCHED
    g["S4_still_present"] = present >= MIN_STILL_PRESENT
    result["sample"] = {grp: sorted(picked[grp]) for grp, _ in GROUPS}
    result["fetched"] = sum(1 for i in ids if i in studies)
    result["still_present"] = present
    key = sorted(((order[i], i, grp) for grp, _ in GROUPS for i in picked[grp]))
    blocks = ["# Blind reading file (consent_permission %s, seed %d)" % (__version__, SEED),
              "Label each record with one of: %s." % ", ".join(LABELS), ""]
    for rid, nct, _ in key:
        if nct in studies:
            blocks.append(reading_block(rid, studies[nct]))
        else:
            blocks.append("## %s\nNot returned by the API.\n" % rid)
    reading = "\n".join(blocks)
    result["reading_sha256"] = sha256(reading.encode("utf-8"))
    return result, reading, key


# --- grading -------------------------------------------------------------------------------

def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def newcombe(k1, n1, k2, n2):
    """Difference k1/n1 - k2/n2 with Newcombe's hybrid score 95% interval (method 10)."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return (d, d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
            d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def read_labels(data):
    header, rows = read_csv(data)
    return header, rows


def label_gates(key_rows, label_header, label_rows):
    ids = [r["blind_id"] for r in label_rows]
    want = sorted(r["blind_id"] for r in key_rows)
    return {"L1_header": label_header[:2] == ["blind_id", "label"],
            "L2_complete": sorted(ids) == want and len(set(ids)) == len(ids),
            "L3_valid": all(r.get("label") in LABELS for r in label_rows)}


def share(rows):
    read = [r for r in rows if r["label"] != "path_gone"]
    k = sum(1 for r in read if r["label"] == "adult_permission")
    n = len(read)
    ci = wilson(k, n)
    return {"read": n, "adult_permission": k, "share": round(k / n, 4) if n else None,
            "ci": [round(ci[0], 4), round(ci[1], 4)] if ci else None,
            "labels": {l: sum(1 for r in rows if r["label"] == l) for l in LABELS}}


def grade(key_rows, label_header, label_rows, mentions=EXPECTED):
    g = label_gates(key_rows, label_header, label_rows)
    result = {"version": __version__, "gates": g, "groups": None, "predictions": None}
    if not all(g.values()):
        return result
    lab = {r["blind_id"]: r["label"] for r in label_rows}
    joined = [{"group": k["group"], "label": lab[k["blind_id"]]} for k in key_rows]
    s = {grp: share([r for r in joined if r["group"] == grp]) for grp, _ in GROUPS}
    result["groups"] = s
    pn, pw, px = s["nci"]["share"], s["washu"]["share"], s["neither"]["share"]
    if None in (pn, pw, px):
        return result
    d, lo, hi = newcombe(s["nci"]["adult_permission"], s["nci"]["read"],
                         s["neither"]["adult_permission"], s["neither"]["read"])
    result["diff_nci_minus_neither"] = [round(d, 4), round(lo, 4), round(hi, 4)]
    # Estimated real adult permissions: NCI-linked mentions (the 18 trials that are both count
    # here) at the NCI rate, WashU-only mentions at the WashU rate, Neither at the Neither rate.
    n_nci = mentions["nci_linked"][0]
    n_washu = mentions["washu_led"][0] - mentions["both"][0]
    n_neither = mentions["neither"][0]
    owners = n_nci * pn + n_washu * pw
    total = owners + n_neither * px
    result["estimated_permissions"] = {
        "owners": round(owners, 1), "neither": round(n_neither * px, 1), "total": round(total, 1),
        "owner_share": round(owners / total, 4) if total else None,
        "of_all_trials": round(total / mentions["rows"], 4),
        "neither_of_neither_trials": round(n_neither * px / mentions["neither"][1], 4)}
    result["predictions"] = {
        "R1": d >= R1_MIN_DIFF and lo > 0,
        "R2": pn >= R2_MIN_NCI,
        "R3": px <= R3_MAX_NEITHER,
        "R4": pw >= R4_MIN_WASHU,
        "R5": bool(total) and owners / total >= R5_MIN_OWNER_SHARE,
    }
    return result


def grade_text(result):
    lines = ["consent_permission %s grade" % result["version"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for grp, c in (result.get("groups") or {}).items():
        lines.append("%s: %d of %d adult_permission (%s; %s) labels %s" % (
            grp, c["adult_permission"], c["read"], c["share"], c["ci"],
            json.dumps(c["labels"], sort_keys=True)))
    if result.get("diff_nci_minus_neither"):
        lines.append("diff nci - neither: %s" % result["diff_nci_minus_neither"])
        lines.append("estimated permissions: %s" % json.dumps(result["estimated_permissions"],
                                                              sort_keys=True))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--sponsor-csv", default=SPONSOR_URL, help="a file or a URL")
    s.add_argument("--out-dir", required=True)
    g = sub.add_parser("grade")
    g.add_argument("--key", required=True)
    g.add_argument("--labels", required=True)
    g.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "sample":
        if args.sponsor_csv.startswith("http"):
            data = fetch_bytes(args.sponsor_csv)
        else:
            with open(args.sponsor_csv, "rb") as f:
                data = f.read()
        started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        result, reading, key = run_sample(data)
        result["started_utc"] = started
        if reading is not None:
            with open(args.out_dir + "/reading.txt", "w", encoding="utf-8", newline="\n") as f:
                f.write(reading)
            with open(args.out_dir + "/key.csv", "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f, lineterminator="\n")
                w.writerow(["blind_id", "nct_id", "group"])
                w.writerows(key)
        with open(args.out_dir + "/sample.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1)
        ok = all(result["gates"].values())
        print("gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items())))
        print("counts: %s" % json.dumps(result["counts"], sort_keys=True))
        print("fetched %s, still naming a path %s, reading sha256 %s" % (
            result.get("fetched"), result.get("still_present"),
            (result.get("reading_sha256") or "none")[:12]))
        print("sample: %s" % ("ok" if ok else "gate failed"))
        return 0
    with open(args.key, "rb") as f:
        _, key_rows = read_csv(f.read())
    with open(args.labels, "rb") as f:
        label_bytes = f.read()
    header, label_rows = read_labels(label_bytes)
    result = grade(key_rows, header, label_rows)
    result["labels_sha256"] = sha256(label_bytes)
    with open(args.out_dir + "/grade.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    text = grade_text(result)
    with open(args.out_dir + "/grade.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
