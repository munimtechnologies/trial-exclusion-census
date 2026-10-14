"""trial-exclusion-census: how often do clinical trials exclude disabled people, and is it changing?

Reads the eligibility criteria of every interventional study on
ClinicalTrials.gov (public API v2), finds the exclusion criteria, and flags
items that exclude people by disability: cognitive or intellectual, capacity
to consent, vision, hearing, communication and mobility. Psychiatric,
substance use, performance status, investigator-discretion and English-only
items are counted alongside, as earlier manual studies did. It also notes
whether the criteria mention any accommodation (an assistive device, a legally
authorized representative, an interpreter, large print and the like), and
whether a flagged exclusion matches the trial's own condition (excluding
vision loss from a glaucoma trial is not the same as from a diabetes trial).

Since 0.2.0 it also reads the inclusion criteria for ability requirements in
the same six categories ("able to walk 100 m unaided", "normal or
corrected-to-normal vision", "able to read and write", "able to provide
informed consent" with no representative allowed). These shut people out as
surely as an exclusion does, but an exclusion-only count cannot see them.

Earlier work coded samples by hand: 97 protocols in four areas (DeCormier
Plosky et al., Health Affairs 2022) and 2,710 trials for ten conditions,
2010-2020 (scoping review, 2023). This is the whole registry, by year, with
open rules anyone can re-run and argue with.

A word list, not a reader: it flags what a criterion says, not whether the
exclusion is justified, and it misses exclusions worded in ways it does not
know. sample_items.csv holds random flagged items per category so its
precision can be checked by hand.

`check` runs the same rules on one trial's criteria and prints each flagged
item with an inclusive alternative to consider. Information only; it is not
medical, legal or IRB advice.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import collections
import csv
import gzip
import json
import logging
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

__version__ = "0.2.0"

API = "https://clinicaltrials.gov/api/v2/studies"
UA = "trial-exclusion-census/%s (Munim, Inc.; munimversion2@gmail.com)" % __version__
FIELDS = ("NCTId", "BriefTitle", "OverallStatus", "StudyType", "Phase", "StartDate",
          "StudyFirstSubmitDate", "Condition", "LeadSponsorClass", "EligibilityCriteria",
          "HealthyVolunteers", "EnrollmentCount")

# Disability categories (the "core" ones) and the others counted for comparison.
CORE = ("cognitive", "consent_capacity", "visual", "hearing", "communication", "mobility")
OTHER = ("psychiatric", "substance_use", "performance_status", "investigator_discretion",
         "english_only", "disability_general")
CATEGORIES = CORE + OTHER
SENSORY_PHYSICAL = ("visual", "hearing", "communication", "mobility")

_UNABLE = r"\b(?:unable|inability|not able|cannot|can ?not|incapable of|incapacity)"
_LANGS = (r"english|spanish|french|german|italian|dutch|chinese|mandarin|cantonese|japanese|"
          r"korean|portuguese|hebrew|arabic|danish|swedish|norwegian|finnish|polish|russian|"
          r"turkish|greek|thai|hindi|vietnamese|local language|national language|"
          r"study language|official language")
# Not followed, within the same clause, by a language name: "unable to read English"
# is a language requirement (english_only), not a communication disability.
_NOT_LANG = r"(?![^.;\n]{0,40}\b(?:" + _LANGS + r")\b)"
PATTERNS = {
    "cognitive": [
        r"\bdementia", r"\balzheimer", r"\bmild cognitive impairment\b",
        r"\bcognitive(?:ly)?\s+(?:impair|deficit|dysfunction|decline|disorder|disabilit|problem)",
        r"\bintellectual(?:ly)?\s+(?:disab|impair|deficien)", r"\bmental(?:ly)?\s+retard",
        r"\bdevelopmental\s+(?:delay|disab)", r"\blearning\s+disab",
        r"\b(?:mmse|mini[- ]mental|moca|montreal cognitive)\b"],
    "consent_capacity": [
        _UNABLE + r"\b[^.;\n]{0,60}\b(?:consent|assent)\b",
        r"\b(?:lack|lacks|lacking|impaired|diminished|without)\s+(?:the\s+)?(?:decision(?:al)?[- ]making\s+)?capacity\b",
        r"\bdecision(?:al)?[- ]making capacity\b", r"\blegally incompetent\b",
        _UNABLE + r"\s+(?:to\s+)?(?:understand|comprehend)\b" + _NOT_LANG],
    "visual": [
        r"(?<!double-)(?<!double )(?<!single-)(?<!single )(?<!triple-)(?<!triple )\bblind(?:ness)?\b(?!-)",
        r"\bvisual(?:ly)?\s+(?:impair|disab|handicap|loss|deficit)", r"\blow vision\b",
        r"\bvision\s+(?:loss|impairment|problem)", r"\bunable to see\b",
        r"\b(?:inadequate|insufficient|poor|impaired|reduced)\s+(?:vision|eyesight)\b",
        r"\bvisual acuity\b"],
    "hearing": [
        r"\bdeaf(?:ness)?\b", r"\bhearing\s+(?:impair|loss|disab|deficit|problem|difficult)",
        r"\bhard of hearing\b", r"\bunable to hear\b",
        r"\b(?:impaired|inadequate|insufficient|poor|reduced)\s+hearing\b", r"\bhearing aids?\b"],
    "communication": [
        r"\baphasi", r"\bdysarthri", r"\billiter", r"\bnon[- ]?verbal\b",
        _UNABLE + r"\s+(?:to\s+)?(?:speak|communicate|read|write|verbali[sz]e)\b" + _NOT_LANG,
        r"\b(?:speech|communication|language)\s+(?:impair|disorder|deficit|difficult|disab)"],
    "mobility": [
        r"\bwheel[- ]?chair", r"\bnon[- ]?ambulatory\b",
        _UNABLE + r"\s+(?:to\s+)?(?:walk|ambulate|stand)\b", r"\bbed[- ]?(?:ridden|bound)\b",
        r"\bparapleg", r"\btetrapleg", r"\bquadripleg", r"\bhemipleg",
        r"\bparaly(?:sis|ses|zed|sed)\b", r"\bamputat",
        r"\b(?:mobility|physical)\s+(?:impair|disab|limitation|handicap)",
        r"\b(?:requir\w*|dependent on|use of|uses?)\s+(?:an?\s+)?(?:walking aid|walker|cane|crutch|assistive device)"],
    "psychiatric": [
        r"\bschizo", r"\bbipolar\b", r"\bpsychos[ie]s\b", r"\bpsychotic\b",
        r"\bpsychiatric\s+(?:disorder|illness|condition|disease|history|hospitali|comorbid)",
        r"\bmental\s+(?:illness|disorder|health (?:disorder|condition))", r"\bmajor depress",
        r"\bsuicid"],
    "substance_use": [
        r"\b(?:substance|drug|alcohol|opioid)\s+(?:use|abuse|dependence|misuse|addiction)",
        r"\balcoholism\b", r"\baddict"],
    "performance_status": [
        r"\becog\b", r"\bkarnofsky\b", r"\bperformance status\b", r"\bkps\b", r"\blansky\b"],
    "investigator_discretion": [
        r"\b(?:opinion|judge?ment|discretion|view)\s+of\s+(?:the\s+)?(?:principal\s+|site\s+|treating\s+)?"
        r"(?:investigator|pi\b|study (?:doctor|physician|team)|physician|sponsor)",
        r"\binvestigator['’]?s?['’]?\s+(?:opinion|judge?ment|discretion)",
        r"\b(?:investigator|pi)\s+(?:believes|considers|deems|feels|determines)"],
    "english_only": [
        r"\bnon[- ]?english\b", r"\bnot (?:fluent|proficient) in english\b", r"\blimited english\b",
        r"\b(?:speak|read|write|understand|communicat|fluen|proficien|literate)\w*\b[^.;\n]{0,40}\benglish\b"],
    "disability_general": [
        r"\bhandicap", r"(?<!expanded )\bdisabilit(?:y|ies)\b(?!\s+status)"],
}
RULES = {cat: [re.compile(p, re.I) for p in pats] for cat, pats in PATTERNS.items()}

# Ability requirements in the inclusion criteria ("able to walk", "normal hearing").
# "unable" never matches: there is no word boundary inside it.
_ABLE = r"\b(?:able|ability|capable|capacity)(?:\s+and\s+willing)?\s+(?:to|of)\s+(?:\w+ly\s+)?"
# The whole item names no one who can consent for the participant.
_NO_PROXY = r"^(?!.*\b(?:representatives?|LAR|surrogates?|guardians?|prox(?:y|ies)|parents?)\b).*?"
REQUIRE_PATTERNS = {
    "cognitive": [
        r"\bcognitively\s+(?:intact|normal|unimpaired|healthy)\b",
        r"\b(?:normal|intact|preserved)\s+cognit",
        r"\b(?:mmse|mini[- ]mental|moca|montreal cognitive)\b[^.;\n]{0,40}"
        r"(?:≥|>=|>|\bat least\b|\bor (?:higher|greater|more|above)\b|\bgreater than\b|\babove\b)"],
    "consent_capacity": [
        _NO_PROXY + _ABLE + r"(?:provid|giv|sign)\w*\s+(?:\w+\s+){0,2}?(?:informed\s+)?consent\b",
        _NO_PROXY + r"\bcapacity to (?:give |provide )?(?:informed )?consent\b",
        _ABLE + r"(?:understand|comprehend)\w*\b" + _NOT_LANG],
    "visual": [
        r"\b(?:normal|adequate|sufficient|intact|good)\s+(?:or\s+corrected[- ](?:to[- ]normal\s+)?)?"
        r"(?:vision|eyesight|visual acuity)\b",
        r"\bcorrected[- ]to[- ]normal\s+(?:vision|visual acuity|eyesight)\b",
        _ABLE + r"see\b",
        r"\bvisual acuity\b[^.;\n]{0,40}\bor better\b"],
    "hearing": [
        r"\b(?:normal|adequate|sufficient|intact|good)\s+hearing\b",
        _ABLE + r"hear\b"],
    "communication": [
        _ABLE + r"(?:speak|communicat|read|writ|verbali[sz])\w*\b" + _NOT_LANG,
        r"\b(?:functionally\s+)?literate\b" + _NOT_LANG,
        r"\b(?:fluent|intelligible)\s+speech\b"],
    "mobility": [
        _ABLE + r"(?:walk(?:s|ing)?|ambulat(?:e|ing)|stand(?:ing)?)\b",
        r"\b(?:independently|fully|freely)\s+ambulat",
        r"\bambulat(?:ory|e|ing)\s+(?:without|with or without|independently|unaided|unassisted)\b",
        r"\bwalk(?:s|ing)?\s+(?:independently|unaided|unassisted|without (?:assistance|help|an? (?:assistive|walking) (?:device|aid)))"],
}
REQUIRE_RULES = {cat: [re.compile(p, re.I) for p in pats] for cat, pats in REQUIRE_PATTERNS.items()}
REQUIRED = tuple("required_" + cat for cat in CORE)

ACCOMMODATION = re.compile(
    r"\baccommodat(?:e|ed|es|ion|ions)\b|\bassistive (?:device|technolog)|"
    r"\blegally (?:authori[sz]ed|acceptable) representative|\bLAR\b|\bsign language\b|"
    r"\binterpreter|\bbraille\b|\blarge[- ]print|\bscreen[- ]reader|\bread (?:aloud|to (?:them|the participant))|"
    r"\bsurrogate\b|\bproxy (?:consent|respondent|informant)|\bguardian\b|"
    r"\bwith (?:the )?(?:help|assistance|support) of\b|\bcaregiver (?:may|can|will) (?:assist|help)", re.I)

# Conditions and titles that make an exclusion in that category part of the
# trial's own subject (a cataract trial screening vision, a stroke trial aphasia).
CONDITION_RELATED = {
    "cognitive": r"dementia|alzheimer|cognit|intellectual|down syndrome|autis|developmental|memory|delirium",
    "consent_capacity": r"dementia|alzheimer|cognit|intellectual|delirium|\bcoma\b|critical(?:ly)? ill|critical care|intensive care|\bicu\b|sepsis|cardiac arrest|brain injur|psychos|schizo",
    "visual": r"\beye|ocular|retin|macul|glaucoma|cataract|vision|visual|myopi|uveitis|corne|ophthalm|amblyop|keratocon",
    "hearing": r"hearing|deaf|tinnitus|cochlea|otitis|\bear\b|vestibul|meniere",
    "communication": r"aphasi|stroke|speech|language|dysarthri|stutter|autis|laryn|head and neck",
    "mobility": r"stroke|spinal|paraly|amput|multiple sclerosis|parkinson|cerebral palsy|\bgait\b|\bwalk|mobility|fracture|arthroplasty|\bknee|\bhip\b|wheelchair|muscular dystrophy|\bals\b|amyotrophic|neuropath|\bfall|\bfoot\b|\blimb|peripheral arter",
    "psychiatric": r"schizo|bipolar|depress|psych|mental|anxiety|suicid|ptsd|stress disorder|mood",
    "substance_use": r"alcohol|opioid|substance|drug use|smok|tobacco|nicotine|cocaine|cannabis|addict|methamphetamine",
}
CONDITION_RELATED = {k: re.compile(v, re.I) for k, v in CONDITION_RELATED.items()}

# The four areas DeCormier Plosky et al. (Health Affairs 2022) coded by hand.
PLOSKY_AREAS = {
    "dementia": re.compile(r"dementia|alzheimer", re.I),
    "depression": re.compile(r"depress", re.I),
    "diabetes": re.compile(r"diabet", re.I),
    "lung cancer": re.compile(r"lung (?:cancer|carcinoma|neoplasm|adenocarcinoma)|nsclc|\bsclc\b", re.I),
}

SUGGESTIONS = {
    "cognitive": "If cognition matters to the outcome, name the measure and cut-off and say why; otherwise consider supported decision-making and plain-language, easy-read materials.",
    "consent_capacity": "Consider a capacity assessment with a legally authorized representative and participant assent, rather than excluding everyone who cannot consent alone.",
    "visual": "Unless the study needs sight, offer large-print, screen-reader-ready or read-aloud consent forms and questionnaires.",
    "hearing": "Offer sign language interpreters, captioned video and written instructions instead of excluding hearing loss.",
    "communication": "Allow AAC devices, a communication partner or extra time, and accept written, typed or pointed answers.",
    "mobility": "Unless the outcome needs walking or standing, consider accessible sites, home or remote visits and transport support.",
    "investigator_discretion": "Broad discretion can hide disability exclusions; list the specific safety reasons instead.",
    "english_only": "Consider translated materials and interpreters.",
}

REQUIRE_SUGGESTIONS = {
    "cognitive": "If the outcome needs this level of cognition, name the measure and the reason; otherwise allow a supporter and easy-read materials.",
    "consent_capacity": "Allow consent by a legally authorized representative with the participant's own assent, unless the study cannot be done that way.",
    "visual": "Unless a task needs sight, accept blind and low-vision participants and adapt the materials (large print, screen reader, read aloud).",
    "hearing": "Unless a task needs hearing, accept deaf and hard-of-hearing participants and provide interpreters, captions and written instructions.",
    "communication": "Accept answers by AAC, writing, typing or pointing, and read documents aloud for people who do not read print.",
    "mobility": "Unless walking or standing is the outcome or a safety need, accept wheelchair users and people who use walking aids.",
}

HEADER = re.compile(
    r"^[^\w\n]*(?:(?:key|main|major|general|specific|additional|principal|other)\s+)?"
    r"(inclusion|exclusion|eligibility)(?:\s+criteri\w*)?[\s*_]*(?::|$)", re.I | re.M)
INLINE_EXCLUSION = re.compile(r"\bexclusion\s+criteri\w*\s*:?", re.I)
BULLET = re.compile(r"^\s*(?:[*\-•●▪·]+|\(?\d{1,2}[.)]|\(?[a-z][.)])\s+", re.I)


def _headed(text, kind):
    """The text under every header of this kind ("inclusion" or "exclusion"), or None."""
    heads = list(HEADER.finditer(text))
    parts = []
    for i, h in enumerate(heads):
        if h.group(1).lower() != kind:
            continue
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        parts.append(text[h.end():end])
    return "\n".join(parts) if parts else None


def exclusion_section(text):
    """The exclusion criteria part of an eligibility text, or None if it has none."""
    if not text:
        return None
    section = _headed(text, "exclusion")
    if section is not None:
        return section
    m = INLINE_EXCLUSION.search(text)
    return text[m.end():] if m else None


def inclusion_section(text):
    """The inclusion criteria part of an eligibility text (up to any inline
    "Exclusion criteria"), or None if it has no inclusion header."""
    if not text:
        return None
    section = _headed(text, "inclusion")
    if section is None:
        return None
    m = INLINE_EXCLUSION.search(section)
    return section[:m.start()] if m else section


def split_items(section):
    """One criterion per item: lines without their bullets; very long lines split at semicolons."""
    items = []
    for line in (section or "").splitlines():
        line = BULLET.sub("", line).strip()
        if len(line) > 400:
            items.extend(p.strip() for p in line.split(";"))
        elif line:
            items.append(line)
    return [it for it in items if len(it) >= 3]


def classify(item):
    """The categories an exclusion item falls into."""
    return {cat for cat, rules in RULES.items() if any(r.search(item) for r in rules)}


def requirements(item):
    """The core categories whose ability an inclusion item requires."""
    return {cat for cat, rules in REQUIRE_RULES.items() if any(r.search(item) for r in rules)}


def analyze(rec):
    """Flags for one trial record (see extract)."""
    crit = rec.get("criteria") or ""
    section = exclusion_section(crit)
    hits = {}
    for item in split_items(section):
        for cat in classify(item):
            hits.setdefault(cat, []).append(item)
    reqs = {}
    for item in split_items(inclusion_section(crit)):
        for cat in requirements(item):
            reqs.setdefault(cat, []).append(item)
    subject = " ".join(rec.get("conditions") or []) + " " + (rec.get("title") or "")
    related = {cat for cat in hits if cat in CONDITION_RELATED and CONDITION_RELATED[cat].search(subject)}
    related_req = {cat for cat in reqs if CONDITION_RELATED[cat].search(subject)}
    return {"has_exclusion": section is not None, "hits": hits, "related": related,
            "requires": reqs, "related_req": related_req,
            "accommodation": bool(ACCOMMODATION.search(crit))}


def check_text(text):
    """Human-readable report of the flagged items in one trial's criteria."""
    a = analyze({"criteria": text})
    if not a["has_exclusion"] and not a["requires"]:
        return "No exclusion criteria section found."
    lines = []
    if a["has_exclusion"]:
        for item in split_items(exclusion_section(text)):
            cats = sorted(classify(item), key=CATEGORIES.index)
            if not cats:
                continue
            lines.append("- " + item)
            lines.append("  categories: " + ", ".join(cats))
            for cat in cats:
                if cat in SUGGESTIONS:
                    lines.append("  consider: " + SUGGESTIONS[cat])
        if not lines:
            lines.append("No disability-related exclusion items found by these word rules.")
    else:
        lines.append("No exclusion criteria section found.")
    required = []
    for item in split_items(inclusion_section(text)):
        cats = sorted(requirements(item), key=CORE.index)
        if not cats:
            continue
        required.append("- " + item)
        required.append("  requires: " + ", ".join(cats))
        for cat in cats:
            required.append("  consider: " + REQUIRE_SUGGESTIONS[cat])
    if required:
        lines.append("Inclusion items that require an ability:")
        lines.extend(required)
    lines.append("Accommodation mentioned anywhere in the criteria: %s" % ("yes" if a["accommodation"] else "no"))
    lines.append("Word rules only: a flag is not a judgment that an exclusion is unjustified.")
    return "\n".join(lines)


# --- ClinicalTrials.gov ---------------------------------------------------

def _find(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = _find(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find(v, key)
            if r is not None:
                return r
    return None


def _pick(ps, module, key):
    v = (ps.get(module) or {}).get(key)
    return v if v is not None else _find(ps, key)


def extract(study):
    """The fields this census uses, from one API v2 study object."""
    ps = study.get("protocolSection") or {}
    start = _pick(ps, "statusModule", "startDateStruct") or {}
    lead = _pick(ps, "sponsorCollaboratorsModule", "leadSponsor") or {}
    enrol = _pick(ps, "designModule", "enrollmentInfo") or {}
    return {
        "nct": _pick(ps, "identificationModule", "nctId"),
        "title": _pick(ps, "identificationModule", "briefTitle") or "",
        "status": _pick(ps, "statusModule", "overallStatus"),
        "type": _pick(ps, "designModule", "studyType"),
        "phases": _pick(ps, "designModule", "phases") or [],
        "start": start.get("date") if isinstance(start, dict) else None,
        "first_submit": _pick(ps, "statusModule", "studyFirstSubmitDate"),
        "conditions": _pick(ps, "conditionsModule", "conditions") or [],
        "sponsor_class": lead.get("class") if isinstance(lead, dict) else None,
        "criteria": _pick(ps, "eligibilityModule", "eligibilityCriteria") or "",
        "healthy": _pick(ps, "eligibilityModule", "healthyVolunteers"),
        "enrollment": enrol.get("count") if isinstance(enrol, dict) else None,
    }


def http_get_json(url, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(15 * (i + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError):
            if i < tries - 1:
                time.sleep(15 * (i + 1))
                continue
            raise


def iter_studies(get=http_get_json, page_size=1000, pause=1.5, max_pages=0):
    """Every interventional study, page by page. Falls back to fewer server-side
    options if the API rejects one (HTTP 400) before the first page."""
    variants = [
        {"fields": ",".join(FIELDS), "filter.advanced": "AREA[StudyType]INTERVENTIONAL"},
        {"fields": ",".join(FIELDS)},
        {"pageSize": "200"},
    ]
    for variant in variants:
        params = {"format": "json", "pageSize": str(page_size), "countTotal": "true"}
        params.update(variant)
        token, pages = None, 0
        try:
            while True:
                p = dict(params)
                if token:
                    p["pageToken"] = token
                data = get(API + "?" + urllib.parse.urlencode(p))
                pages += 1
                if pages == 1:
                    logging.info("API variant %s: totalCount %s", variant, data.get("totalCount"))
                for study in data.get("studies") or []:
                    rec = extract(study)
                    if rec["type"] in (None, "INTERVENTIONAL"):
                        yield rec
                token = data.get("nextPageToken")
                if pages % 25 == 0:
                    logging.info("%d pages", pages)
                if not token or (max_pages and pages >= max_pages):
                    return
                time.sleep(pause)
        except urllib.error.HTTPError as e:
            if e.code != 400 or pages:
                raise
            logging.warning("API rejected %s (HTTP 400); trying the next form", variant)
    raise RuntimeError("the API rejected every request form")


def load_records(cache, refresh=False, max_pages=0, get=http_get_json):
    """Records from the cache if it exists, otherwise from the API, saved to the
    cache as they stream past (the cache only appears once the fetch is complete)."""
    if cache and os.path.exists(cache) and not refresh:
        with gzip.open(cache, "rt", encoding="utf-8") as f:
            for line in f:
                yield json.loads(line)
        return
    if not cache:
        yield from iter_studies(get=get, max_pages=max_pages)
        return
    tmp = cache + ".part"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        for rec in iter_studies(get=get, max_pages=max_pages):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            yield rec
    os.replace(tmp, cache)


# --- Aggregation -----------------------------------------------------------

def year_of(date):
    return int(date[:4]) if date and date[:4].isdigit() else None


def phase_label(phases):
    phases = [p for p in (phases or []) if p]
    return "+".join(sorted(phases)) if phases else "NA"


class Tally:
    """Counts of trials with an exclusion section, per category, any-core and accommodation,
    and the ability requirements in their inclusion criteria."""

    def __init__(self):
        self.n = 0
        self.cat = collections.Counter()
        self.cat_unrelated = collections.Counter()
        self.any_core = self.any_core_unrelated = self.any_sensory_physical = 0
        self.accommodation = self.accommodation_if_core = 0
        self.req = collections.Counter()
        self.any_req = self.req_only = self.any_barrier = 0

    def add(self, a):
        if not a["has_exclusion"]:
            return
        self.n += 1
        flagged = set(a["hits"])
        for cat in flagged:
            self.cat[cat] += 1
            if cat not in a["related"]:
                self.cat_unrelated[cat] += 1
        core = flagged & set(CORE)
        if core:
            self.any_core += 1
            if a["accommodation"]:
                self.accommodation_if_core += 1
        if core - a["related"]:
            self.any_core_unrelated += 1
        if flagged & set(SENSORY_PHYSICAL):
            self.any_sensory_physical += 1
        if a["accommodation"]:
            self.accommodation += 1
        required = set(a.get("requires") or ())
        for cat in required:
            self.req[cat] += 1
        if required:
            self.any_req += 1
            if not core:
                self.req_only += 1
        if required or core:
            self.any_barrier += 1

    def row(self):
        pct = lambda k: round(100.0 * k / self.n, 2) if self.n else None
        r = {"trials": self.n, "any_core_pct": pct(self.any_core),
             "any_core_unrelated_pct": pct(self.any_core_unrelated),
             "any_sensory_physical_pct": pct(self.any_sensory_physical),
             "accommodation_pct": pct(self.accommodation),
             "accommodation_if_core_pct": round(100.0 * self.accommodation_if_core / self.any_core, 2)
             if self.any_core else None}
        for cat in CATEGORIES:
            r[cat + "_pct"] = pct(self.cat[cat])
        for cat in CORE:
            r[cat + "_unrelated_pct"] = pct(self.cat_unrelated[cat])
        r["any_required_pct"] = pct(self.any_req)
        r["required_only_pct"] = pct(self.req_only)
        r["any_barrier_pct"] = pct(self.any_barrier)
        for cat in CORE:
            r[cat + "_required_pct"] = pct(self.req[cat])
        return r


TRIAL_COLUMNS = ("nct", "start_year", "sponsor_class", "phase", "status", "categories",
                 "condition_related", "accommodation", "required")


def census(records, sample_per_cat=60, seed=2026):
    """Aggregate tables and a seeded sample of flagged items for hand-checking."""
    total = Tally()
    by_year, by_sponsor, by_phase, by_area = (collections.defaultdict(Tally) for _ in range(4))
    rng = random.Random(seed)
    seen = collections.Counter()
    samples = {key: [] for key in CATEGORIES + REQUIRED}
    trials = []
    n_records = n_criteria = 0
    for rec in records:
        n_records += 1
        if not rec.get("criteria"):
            continue
        n_criteria += 1
        a = analyze(rec)
        total.add(a)
        y = year_of(rec.get("start"))
        if y and 2000 <= y <= 2026:
            by_year[y].add(a)
        by_sponsor[rec.get("sponsor_class") or "UNKNOWN"].add(a)
        by_phase[phase_label(rec.get("phases"))].add(a)
        subject = " ".join(rec.get("conditions") or [])
        for area, rx in PLOSKY_AREAS.items():
            if rx.search(subject):
                by_area[area].add(a)
        flagged = list(a["hits"].items()) + [("required_" + c, items) for c, items in a["requires"].items()]
        for key, items in flagged:
            for item in items:
                seen[key] += 1
                s = samples[key]
                if len(s) < sample_per_cat:
                    s.append((rec.get("nct"), item))
                else:
                    j = rng.randrange(seen[key])
                    if j < sample_per_cat:
                        s[j] = (rec.get("nct"), item)
        if a["has_exclusion"]:
            trials.append((rec.get("nct"), y, rec.get("sponsor_class"), phase_label(rec.get("phases")),
                           rec.get("status"), "|".join(sorted(a["hits"], key=CATEGORIES.index)),
                           "|".join(sorted(a["related"], key=CATEGORIES.index)), int(a["accommodation"]),
                           "|".join(sorted(a["requires"], key=CORE.index))))
    return {
        "records": n_records, "with_criteria": n_criteria,
        "total": total.row(),
        "by_year": {y: t.row() for y, t in sorted(by_year.items())},
        "by_sponsor": {k: t.row() for k, t in sorted(by_sponsor.items(), key=lambda kv: -kv[1].n)},
        "by_phase": {k: t.row() for k, t in sorted(by_phase.items(), key=lambda kv: -kv[1].n)},
        "plosky_areas": {k: by_area[k].row() for k in PLOSKY_AREAS},
        "samples": samples, "trials": trials,
    }


def write_table(path, rows, key_name):
    rows = list(rows.items())
    if not rows:
        return
    cols = list(rows[0][1].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([key_name] + cols)
        for k, r in rows:
            w.writerow([k] + [r.get(c) for c in cols])


def report_md(res, fetched_at):
    t = res["total"]
    lines = [
        "# Disability-related exclusion criteria on ClinicalTrials.gov",
        "",
        "trial-exclusion-census %s, data fetched %s from the ClinicalTrials.gov API v2." % (__version__, fetched_at),
        "Interventional studies: %d; with eligibility criteria: %d; with an exclusion section: %d."
        % (res["records"], res["with_criteria"], t["trials"]),
        "",
        "Shares are of trials with an exclusion section. 'Unrelated' leaves out trials whose own",
        "condition or title is in that category. Word rules only; see sample_items.csv for precision.",
        "",
        "| Category | % of trials | % excluding condition-related |",
        "|---|---|---|",
    ]
    for cat in CORE:
        lines.append("| %s | %s | %s |" % (cat, t[cat + "_pct"], t[cat + "_unrelated_pct"]))
    for cat in OTHER:
        lines.append("| %s | %s | |" % (cat, t[cat + "_pct"]))
    lines += [
        "| any disability category | %s | %s |" % (t["any_core_pct"], t["any_core_unrelated_pct"]),
        "| any vision, hearing, communication or mobility | %s | |" % t["any_sensory_physical_pct"],
        "",
        "Accommodation mentioned: %s%% of all trials; %s%% of trials with a disability exclusion."
        % (t["accommodation_pct"], t["accommodation_if_core_pct"]),
        "",
        "## Ability requirements in the inclusion criteria",
        "",
        "Inclusion criteria can shut people out too (\"able to walk 100 m unaided\", \"normal hearing\",",
        "\"able to provide informed consent\" with no representative allowed). Same trials as above.",
        "",
        "| Category | % of trials requiring it |",
        "|---|---|",
    ]
    for cat in CORE:
        lines.append("| %s | %s |" % (cat, t[cat + "_required_pct"]))
    lines += [
        "| any disability category | %s |" % t["any_required_pct"],
        "",
        "Trials with a disability barrier in either section: %s%%. With one only in the inclusion"
        " criteria (invisible to an exclusion-only count): %s%%." % (t["any_barrier_pct"], t["required_only_pct"]),
        "",
        "## By start year",
        "",
        "| Year | Trials | Any disability % | Unrelated % | Cognitive % | Consent % | Visual % | Hearing % | Communication % | Mobility % | Accommodation % |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for y, r in res["by_year"].items():
        lines.append("| %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            y, r["trials"], r["any_core_pct"], r["any_core_unrelated_pct"], r["cognitive_pct"],
            r["consent_capacity_pct"], r["visual_pct"], r["hearing_pct"], r["communication_pct"],
            r["mobility_pct"], r["accommodation_pct"]))
    lines += ["", "## Inclusion-criteria requirements by start year", "",
              "| Year | Trials | Requires any % | Requirement only % | Any barrier % |", "|---|---|---|---|---|"]
    for y, r in res["by_year"].items():
        lines.append("| %s | %d | %s | %s | %s |" % (
            y, r["trials"], r["any_required_pct"], r["required_only_pct"], r["any_barrier_pct"]))
    lines += ["", "## By lead sponsor class", "",
              "| Sponsor | Trials | Any disability % | Unrelated % | Discretion % | Accommodation % |",
              "|---|---|---|---|---|---|"]
    for k, r in res["by_sponsor"].items():
        lines.append("| %s | %d | %s | %s | %s | %s |" % (k, r["trials"], r["any_core_pct"],
                     r["any_core_unrelated_pct"], r["investigator_discretion_pct"], r["accommodation_pct"]))
    lines += ["", "## The four areas of DeCormier Plosky et al. (Health Affairs 2022, 97 protocols)", "",
              "Their hand-coded rates: psychiatric 68%, cognitive or intellectual 42%, visual 34%, hearing 10%,",
              "mobility 9%, communication 3%; accommodations permitted 18%; investigator discretion 85%.", "",
              "| Area | Trials | Psychiatric % | Cognitive % | Consent % | Visual % | Hearing % | Mobility % | Communication % | Discretion % | Accommodation % |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in res["plosky_areas"].items():
        lines.append("| %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            k, r["trials"], r["psychiatric_pct"], r["cognitive_pct"], r["consent_capacity_pct"],
            r["visual_pct"], r["hearing_pct"], r["mobility_pct"], r["communication_pct"],
            r["investigator_discretion_pct"], r["accommodation_pct"]))
    lines.append("")
    return "\n".join(lines)


def write_outputs(res, out_dir, fetched_at):
    os.makedirs(out_dir, exist_ok=True)
    summary = {k: res[k] for k in ("records", "with_criteria", "total", "by_year", "by_sponsor",
                                    "by_phase", "plosky_areas")}
    summary.update({"version": __version__, "fetched_at": fetched_at, "categories": list(CATEGORIES),
                    "core": list(CORE)})
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, default=str)
    with open(os.path.join(out_dir, "results.md"), "w", encoding="utf-8") as f:
        f.write(report_md(res, fetched_at))
    write_table(os.path.join(out_dir, "by_year.csv"), res["by_year"], "start_year")
    write_table(os.path.join(out_dir, "by_sponsor.csv"), res["by_sponsor"], "sponsor_class")
    write_table(os.path.join(out_dir, "by_phase.csv"), res["by_phase"], "phase")
    write_table(os.path.join(out_dir, "plosky_areas.csv"), res["plosky_areas"], "area")
    with open(os.path.join(out_dir, "sample_items.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["category", "nct", "item", "correct"])
        for cat in CATEGORIES + REQUIRED:
            for nct, item in res["samples"][cat]:
                w.writerow([cat, nct, item, ""])
    with gzip.open(os.path.join(out_dir, "trials.csv.gz"), "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(TRIAL_COLUMNS)
        w.writerows(res["trials"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("census", help="fetch every interventional study and write the tables")
    c.add_argument("--out-dir", default="out")
    c.add_argument("--cache", default="", help="jsonl.gz of fetched records; reused if present")
    c.add_argument("--refresh", action="store_true", help="fetch again even if the cache exists")
    c.add_argument("--max-pages", type=int, default=0, help="stop after this many API pages (testing)")
    k = sub.add_parser("check", help="flag disability-related exclusions in one trial's criteria")
    k.add_argument("file", help="text file with the eligibility criteria, or - for stdin")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if args.cmd == "check":
        text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
        print(check_text(text))
        return 0
    cache = "" if args.max_pages else args.cache  # never cache a partial fetch
    fetched_at = time.strftime("%Y-%m-%d", time.gmtime())
    if cache and os.path.exists(cache) and not args.refresh:
        fetched_at = time.strftime("%Y-%m-%d", time.gmtime(os.path.getmtime(cache)))
    res = census(load_records(cache, args.refresh, args.max_pages))
    logging.info("%d records, %d with criteria", res["records"], res["with_criteria"])
    write_outputs(res, args.out_dir, fetched_at)
    print(report_md(res, fetched_at))
    return 0


if __name__ == "__main__":
    sys.exit(main())
