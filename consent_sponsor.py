"""consent_sponsor: where do the stock consent line's representative paths come from?

Joins the published consent-phrase table (results/consent-phrase/consent-phrase-trials.csv,
made by consent_phrase_check 0.2.0 from registry data of 2026-10-16) with each trial's lead
sponsor and collaborators from the ClinicalTrials.gov API v2, and counts how often the trials
of each sponsor group name a representative, guardian or surrogate (the table's adult_path
column). The groups, predictions and gates were written down before any sponsor was fetched:
results/consent-sponsor/PREREG.md.

A mention is not always a permission: in a reading of 50 exact-line mentions by AI agents
working for MV2, 30 were adult permissions. This script counts mentions only.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import csv
import hashlib
import io
import json
import math
import sys
import time
import urllib.parse
import urllib.request

__version__ = "0.1.0"

CSV_COMMIT = "c4c0ded776cdb43101b881c88f7de31fde2facdc"
CSV_URL = ("https://raw.githubusercontent.com/munimtechnologies/trial-exclusion-census/%s/"
           "results/consent-phrase/consent-phrase-trials.csv" % CSV_COMMIT)
API = "https://clinicaltrials.gov/api/v2/studies"
FIELDS = "NCTId,LeadSponsorName,LeadSponsorClass,CollaboratorName,CollaboratorClass"
USER_AGENT = "consent_sponsor/%s (MV2 of Munim, Inc.; mv2@munimtech.com)" % __version__

HEADER = ["nct_id", "start_year", "phase", "study_type", "adult_only", "stock_exact",
          "stock_loose", "has_exclusion_heading", "representative", "representative_section",
          "guardian", "guardian_section", "surrogate", "surrogate_section", "parent",
          "parent_section", "idmc", "idmc_section", "adult_path", "adult_path_inclusion",
          "nci_idmc_must_have", "nci_idmc_also_eligible", "nci_lar_may_sign", "snippets"]
USED = ("nct_id", "start_year", "adult_only", "stock_exact", "stock_loose", "adult_path")

# The published totals the joined table must reproduce (CONSENT-PHRASE.md, CONSENT-RESULT.md).
EXPECTED = {"rows": 5473, "population": 5436, "exact": 4059, "exact_adult_path": 422}
MIN_COVERAGE = 0.99

# Sponsor groups. The US National Cancer Institute is listed in the registry under exactly this
# name; other national cancer institutes (Egypt, Thailand, ...) have other names and do not count.
NCI_NAME = "national cancer institute (nci)"
WASHU_NAME = "washington university school of medicine"
LEAD_CLASSES = ("INDUSTRY", "NIH", "OTHER")

# Pre-registered thresholds (PREREG.md). Changing any of these after the fetch voids the test.
P1_MIN_RR = 1.5
P2_MIN_RR = 3.0
P3_MIN_PATH_SHARE = 0.40
P3_MAX_TRIAL_SHARE = 0.30
P4_MAX_FRACTION = 0.5
P5_MAX_RISE = 2.0


def truthy(v):
    return str(v).strip() == "True"


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


def read_table(data):
    """The consent-phrase table from its bytes: (header, rows)."""
    reader = csv.reader(io.StringIO(data.decode("utf-8")))
    header = next(reader)
    rows = [dict(zip(header, r)) for r in reader if r]
    return header, rows


def population(rows):
    """Trials with the exact stock line or its near variant."""
    return [r for r in rows if truthy(r.get("stock_exact")) or truthy(r.get("stock_loose"))]


def sponsor_record(study):
    """(nct_id, {lead, lead_class, collaborators}) from one API v2 study."""
    ps = study.get("protocolSection", {})
    nct = ps.get("identificationModule", {}).get("nctId")
    sc = ps.get("sponsorCollaboratorsModule", {})
    lead = sc.get("leadSponsor", {})
    collabs = [(c.get("name", ""), c.get("class", "")) for c in sc.get("collaborators", [])]
    return nct, {"lead": lead.get("name", ""), "lead_class": lead.get("class", ""),
                 "collaborators": collabs}


def fetch_sponsors(ids, fetch=None, batch=100, pause=0.5):
    """Lead sponsor and collaborators for each NCT id, 100 ids per request."""
    fetch = fetch or fetch_json
    out = {}
    for i in range(0, len(ids), batch):
        params = {"filter.ids": ",".join(ids[i:i + batch]), "fields": FIELDS,
                  "pageSize": 1000, "format": "json"}
        token = None
        while True:
            if token:
                params["pageToken"] = token
            page = fetch(API + "?" + urllib.parse.urlencode(params))
            for s in page.get("studies", []):
                nct, rec = sponsor_record(s)
                if nct:
                    out[nct] = rec
            token = page.get("nextPageToken")
            if not token:
                break
        if pause:
            time.sleep(pause)
    return out


def nci_linked(rec):
    names = [rec["lead"]] + [n for n, _ in rec["collaborators"]]
    return any(n.strip().casefold() == NCI_NAME for n in names)


def washu_led(rec):
    return rec["lead"].strip().casefold() == WASHU_NAME


def lead_bucket(rec):
    c = rec["lead_class"].strip().upper()
    return c if c in LEAD_CLASSES else "OTHER_KINDS"


def period(start_year):
    """'<=2019', '2020-2026', or None (no start year, or 2027 and later)."""
    try:
        y = int(str(start_year).strip())
    except ValueError:
        return None
    if y <= 2019:
        return "<=2019"
    if y <= 2026:
        return "2020-2026"
    return None


def wilson(k, n, z=1.96):
    """Wilson 95% interval for k of n, as fractions."""
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 4), round(c + h, 4))


def risk_ratio(k1, n1, k2, n2, z=1.96):
    """Ratio of the shares k1/n1 and k2/n2 with a Katz log 95% interval."""
    if not n1 or not n2 or not k1 or not k2:
        return {"rr": None, "low": None, "high": None}
    rr = (k1 / n1) / (k2 / n2)
    se = math.sqrt(1 / k1 - 1 / n1 + 1 / k2 - 1 / n2)
    return {"rr": round(rr, 3), "low": round(rr * math.exp(-z * se), 3),
            "high": round(rr * math.exp(z * se), 3)}


def cell(rows):
    """Trials, trials naming a path, share and Wilson interval for a list of rows."""
    n = len(rows)
    k = sum(1 for r in rows if truthy(r.get("adult_path")))
    return {"trials": n, "with_path": k, "share": round(k / n, 4) if n else None,
            "ci": wilson(k, n)}


def label(rows, sponsors):
    """Attach the sponsor flags to each row that has a sponsor record; drop the others."""
    out = []
    for r in rows:
        rec = sponsors.get(r["nct_id"])
        if rec is None:
            continue
        r = dict(r)
        r["nci_linked"] = nci_linked(rec)
        r["washu_led"] = washu_led(rec)
        r["template_owner"] = r["nci_linked"] or r["washu_led"]
        r["lead_bucket"] = lead_bucket(rec)
        r["lead"] = rec["lead"]
        out.append(r)
    return out


def gates(header, rows, pop, sponsors, expected=EXPECTED, min_coverage=MIN_COVERAGE):
    exact = [r for r in pop if truthy(r.get("stock_exact"))]
    covered = sum(1 for r in pop if r["nct_id"] in sponsors)
    g = {
        "G1_table": set(USED) <= set(header) and len(rows) == expected["rows"],
        "G2_population": len(pop) == expected["population"] and len(exact) == expected["exact"],
        "G3_adult_path": sum(1 for r in exact if truthy(r.get("adult_path"))) == expected["exact_adult_path"],
        "G4_coverage": bool(pop) and covered / len(pop) >= min_coverage,
    }
    return g, {"rows": len(rows), "header_as_published": header == HEADER,
               "population": len(pop), "exact": len(exact),
               "covered": covered, "coverage": round(covered / len(pop), 4) if pop else None}


def analyse(lab):
    """Every count the pre-registration names, from the labelled population."""
    nci = [r for r in lab if r["nci_linked"]]
    washu = [r for r in lab if r["washu_led"]]
    neither = [r for r in lab if not r["template_owner"]]
    owners = [r for r in lab if r["template_owner"]]
    paths = [r for r in lab if truthy(r.get("adult_path"))]
    c_nci, c_washu, c_neither = cell(nci), cell(washu), cell(neither)
    ind = cell([r for r in neither if r["lead_bucket"] == "INDUSTRY"])
    oth = cell([r for r in neither if r["lead_bucket"] == "OTHER"])
    early = cell([r for r in neither if period(r.get("start_year")) == "<=2019"])
    late = cell([r for r in neither if period(r.get("start_year")) == "2020-2026"])
    owner_paths = sum(1 for r in paths if r["template_owner"])
    return {
        "groups": {"all": cell(lab), "nci_linked": c_nci, "washu_led": c_washu,
                   "both": cell([r for r in lab if r["nci_linked"] and r["washu_led"]]),
                   "neither": c_neither, "template_owner": cell(owners)},
        "lead_class": {b: cell([r for r in lab if r["lead_bucket"] == b])
                       for b in LEAD_CLASSES + ("OTHER_KINDS",)},
        "neither_lead_class": {"INDUSTRY": ind, "OTHER": oth},
        "neither_period": {"<=2019": early, "2020-2026": late},
        "by_period": {p: {g: cell([r for r in rows if period(r.get("start_year")) == p])
                          for g, rows in (("nci_linked", nci), ("washu_led", washu),
                                          ("neither", neither))}
                      for p in ("<=2019", "2020-2026")},
        "rr_nci_vs_neither": risk_ratio(c_nci["with_path"], c_nci["trials"],
                                        c_neither["with_path"], c_neither["trials"]),
        "rr_washu_vs_neither": risk_ratio(c_washu["with_path"], c_washu["trials"],
                                          c_neither["with_path"], c_neither["trials"]),
        "rr_neither_late_vs_early": risk_ratio(late["with_path"], late["trials"],
                                               early["with_path"], early["trials"]),
        "template_owner_share_of_paths": round(owner_paths / len(paths), 4) if paths else None,
        "template_owner_paths": owner_paths, "paths": len(paths),
        "template_owner_share_of_trials": round(len(owners) / len(lab), 4) if lab else None,
    }


def predictions(a):
    """Grade P1-P5 exactly as written in PREREG.md."""
    r1, r2, r5 = a["rr_nci_vs_neither"], a["rr_washu_vs_neither"], a["rr_neither_late_vs_early"]
    ind, oth = a["neither_lead_class"]["INDUSTRY"], a["neither_lead_class"]["OTHER"]
    p4 = None
    if ind["share"] is not None and oth["share"]:
        p4 = ind["share"] <= P4_MAX_FRACTION * oth["share"]
    return {
        "P1": r1["rr"] is not None and r1["rr"] >= P1_MIN_RR and r1["low"] > 1,
        "P2": r2["rr"] is not None and r2["rr"] >= P2_MIN_RR and r2["low"] > 1,
        "P3": (a["template_owner_share_of_paths"] is not None
               and a["template_owner_share_of_paths"] >= P3_MIN_PATH_SHARE
               and a["template_owner_share_of_trials"] <= P3_MAX_TRIAL_SHARE),
        "P4": p4,
        "P5": r5["rr"] is not None and r5["rr"] < P5_MAX_RISE,
    }


def top_leads(lab, n=15):
    """The lead sponsors (organisations) with the most trials naming a path."""
    counts = {}
    for r in lab:
        c = counts.setdefault(r["lead"], [0, 0])
        c[0] += 1
        c[1] += 1 if truthy(r.get("adult_path")) else 0
    rows = sorted(counts.items(), key=lambda kv: (-kv[1][1], -kv[1][0], kv[0]))[:n]
    return [{"lead": k, "trials": v[0], "with_path": v[1]} for k, v in rows]


def markdown(result):
    def pc(c):
        if c["share"] is None:
            return "%d of %d" % (c["with_path"], c["trials"])
        lo, hi = c["ci"]
        return "%d of %d (%.1f%%; %.1f-%.1f)" % (c["with_path"], c["trials"], 100 * c["share"],
                                                  100 * lo, 100 * hi)

    def rr(x):
        return "n/a" if x["rr"] is None else "%.2f (%.2f-%.2f)" % (x["rr"], x["low"], x["high"])

    lines = ["consent_sponsor %s, table sha256 %s" % (result["version"], result["csv_sha256"][:12]),
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items())),
             "counts: %s" % json.dumps(result["counts"], sort_keys=True)]
    a = result.get("analysis")
    if a:
        for g, c in a["groups"].items():
            lines.append("group %s: %s" % (g, pc(c)))
        for b, c in a["lead_class"].items():
            lines.append("lead class %s: %s" % (b, pc(c)))
        for b, c in a["neither_lead_class"].items():
            lines.append("neither, lead class %s: %s" % (b, pc(c)))
        for p, c in a["neither_period"].items():
            lines.append("neither, start %s: %s" % (p, pc(c)))
        lines += ["RR nci vs neither: %s" % rr(a["rr_nci_vs_neither"]),
                  "RR washu vs neither: %s" % rr(a["rr_washu_vs_neither"]),
                  "RR neither late vs early: %s" % rr(a["rr_neither_late_vs_early"]),
                  "template owners: %d of %d paths (%s), %s of trials" % (
                      a["template_owner_paths"], a["paths"], a["template_owner_share_of_paths"],
                      a["template_owner_share_of_trials"])]
        s = result["secondary_adult_only"]
        lines.append("adult-only: RR nci %s; RR washu %s; owners %s of paths" % (
            rr(s["rr_nci_vs_neither"]), rr(s["rr_washu_vs_neither"]),
            s["template_owner_share_of_paths"]))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded (a gate failed)"))
    return "\n".join(lines)


def result_from(csv_bytes, header, rows, pop, sponsors, expected=EXPECTED):
    g, counts = gates(header, rows, pop, sponsors, expected)
    result = {"version": __version__, "csv_url": CSV_URL,
              "csv_sha256": hashlib.sha256(csv_bytes).hexdigest(),
              "gates": g, "counts": counts, "analysis": None, "predictions": None}
    lab = label(pop, sponsors)
    if lab:
        result["analysis"] = analyse(lab)
        result["secondary_adult_only"] = analyse([r for r in lab if truthy(r.get("adult_only"))])
        result["top_leads"] = top_leads(lab)
    if all(g.values()):
        result["predictions"] = predictions(result["analysis"])
    return result, lab


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--csv", default=CSV_URL, help="the consent-phrase table: a file or a URL")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--pause", type=float, default=0.5, help="seconds between API requests")
    args = ap.parse_args(argv)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if args.csv.startswith("http"):
        data = fetch_bytes(args.csv)
    else:
        with open(args.csv, "rb") as f:
            data = f.read()
    header, rows = read_table(data)
    pop = population(rows)
    sponsors = fetch_sponsors([r["nct_id"] for r in pop], pause=args.pause)
    result, lab = result_from(data, header, rows, pop, sponsors)
    result["started_utc"] = started
    result["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(args.out_dir + "/consent-sponsor.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    with open(args.out_dir + "/consent-sponsor-trials.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nct_id", "start_year", "stock_exact", "adult_only", "adult_path",
                    "lead_sponsor", "lead_class", "nci_linked", "washu_led"])
        for r in lab:
            w.writerow([r["nct_id"], r["start_year"], r["stock_exact"], r["adult_only"],
                        r["adult_path"], r["lead"], sponsors[r["nct_id"]]["lead_class"],
                        r["nci_linked"], r["washu_led"]])
    text = markdown(result)
    with open(args.out_dir + "/consent-sponsor.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)
    print("consent-sponsor: %s" % ("ok" if all(result["gates"].values()) else "gate failed"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
