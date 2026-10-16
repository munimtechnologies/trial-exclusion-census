"""Offline tests for phone_requirement (no network). Apache-2.0.

Checks the queries against the pre-registration, the sums its stratum sizes must meet, and every
number PREREG-PHONE-REQUIREMENT.md quotes against prereg-phone-requirement.json.
"""

import copy
import json
import os
import tempfile
import unittest
import urllib.parse
from unittest import mock

import phone_matched as pm
import phone_requirement as pr
import trend_check as tc
import va_matched as vm

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "results", "phone-check")
NOT_VA = "NOT AREA[LeadSponsorName](VA OR Veteran OR Veterans)"
# phone_matched's two-stratum example, now read as phone arm against the rest of the base:
# hearing is twice as common in the phone arm (matched 2.0, 1.29-3.09; unmatched 5.5), visual and
# pregnant are level (1.0), hernia is too rare to keep (1.0 phone-arm match expected).
SMALL = {
    "strata": ["a", "b"],
    "wordings": {"base": 1220, "phone": 120, "telephone": 120, "(phone OR telephone)": 120},
    "trials": {"a": {"phone": 100, "registry": 200}, "b": {"phone": 20, "registry": 1020}},
    "phrases": {
        "hearing (all wordings)": {"kind": "family", "a": {"phone": 40, "registry": 60},
                                   "b": {"phone": 2, "registry": 52}},
        "visual (all wordings)": {"kind": "family", "a": {"phone": 20, "registry": 40},
                                  "b": {"phone": 1, "registry": 51}},
        "pregnant": {"kind": "control", "a": {"phone": 20, "registry": 40},
                     "b": {"phone": 1, "registry": 51}},
        "hernia": {"kind": "control", "a": {"phone": 0, "registry": 1},
                   "b": {"phone": 0, "registry": 2}},
    },
}


def load(name):
    with open(os.path.join(CHECK, name), encoding="utf-8") as f:
        return f.read() if name.endswith(".md") else json.loads(f.read())


class TermTests(unittest.TestCase):
    def test_first_stratum_phone_arm(self):
        self.assertEqual(pr.term(0, required=True),
                         "AREA[StudyType]INTERVENTIONAL AND AREA[Phase]NA AND "
                         "AREA[InterventionSearch]telephone AND AREA[ConditionSearch](PTSD) AND "
                         "NOT AREA[ConditionSearch](%s) AND %s AND "
                         "AREA[EligibilityCriteria](phone OR telephone)" % (vm.OWN, NOT_VA))

    def test_base_is_phone_matched_telephone_without_the_va(self):
        for i in range(len(pr.STRATA)):
            for p in (None, "hernia", pr.HEARING):
                self.assertEqual(pr.term(i, p), pm.term(i, p, phone=True) + " AND " + NOT_VA)
                self.assertEqual(pr.term(i, p, required=True),
                                 pr.term(i, p) + " AND " + pr.REQUIREMENT)

    def test_wording_terms(self):
        base = ("AREA[StudyType]INTERVENTIONAL AND AREA[Phase]NA AND AREA[InterventionSearch]telephone"
                " AND NOT AREA[ConditionSearch](%s) AND %s" % (vm.OWN, NOT_VA))
        self.assertEqual(pr.wording_term(), base)
        self.assertEqual(pr.wording_term("phone"), base + " AND AREA[EligibilityCriteria]phone")
        self.assertEqual(pr.wording_term("(phone OR telephone)"), base + " AND " + pr.REQUIREMENT)

    def test_reading_term(self):
        self.assertEqual(pr.reading_term(),
                         pr.wording_term() + " AND " + pr.REQUIREMENT + " AND AREA[EligibilityCriteria]"
                         + tc.criteria(pr.HEARING))

    def test_strata_and_phrases(self):
        self.assertEqual(pr.STRATA, pm.STRATA)
        self.assertEqual(pr.PHRASES, vm.PHRASES)
        self.assertEqual(pr.WORDINGS, ["phone", "telephone", "(phone OR telephone)"])


class MathTests(unittest.TestCase):
    def test_rows_use_va_matched(self):
        h, v, c, x = pr.rows(SMALL)
        self.assertEqual((h["mh"], h["low"], h["high"], h["crude"]), (2.0, 1.29, 3.09, 5.5))
        self.assertEqual((h["va"], h["expected"], h["kept"]), (42, 21.0, True))
        self.assertEqual((v["mh"], c["mh"], c["kept"]), (1.0, 1.0, True))
        self.assertEqual((x["mh"], x["expected"], x["kept"]), (0.0, 1.0, False))

    def test_verdicts(self):
        self.assertEqual(pr.verdicts(pr.rows(SMALL)), {"HP1": True, "HP2": True, "rivals": 2})

    def test_hp2_fails_when_visual_rises_as_much(self):
        d = copy.deepcopy(SMALL)
        d["phrases"]["visual (all wordings)"] = dict(d["phrases"]["hearing (all wordings)"])
        self.assertEqual(pr.verdicts(pr.rows(d)), {"HP1": True, "HP2": False, "rivals": 2})

    def test_checks(self):
        self.assertEqual(pr.checks(SMALL), {"strata_add_up_to_base": True,
                                            "strata_add_up_to_phone_arm": True,
                                            "wordings_equal": True, "nested": True})
        d = copy.deepcopy(SMALL)
        d["wordings"]["base"] = 1219
        d["phrases"]["pregnant"]["a"]["phone"] = 101
        c = pr.checks(d)
        self.assertFalse(c["strata_add_up_to_base"])
        self.assertFalse(c["nested"])
        self.assertTrue(c["strata_add_up_to_phone_arm"])


class RunTests(unittest.TestCase):
    def test_fetch_counts(self):
        terms = []

        def fake(u):
            terms.append(urllib.parse.parse_qs(urllib.parse.urlparse(u).query)["query.term"][0])
            return {"totalCount": 7}

        data = pr.fetch_counts(["pregnant"], fetch=fake, pause=0)
        self.assertEqual(len(terms), 28)
        self.assertEqual(terms[0], pr.wording_term())
        self.assertTrue(all(NOT_VA in t for t in terms))
        self.assertEqual(sum(pr.REQUIREMENT in t for t in terms), 13)
        self.assertEqual(data["wordings"], {"base": 7, "phone": 7, "telephone": 7,
                                            "(phone OR telephone)": 7})
        self.assertEqual(data["strata"][-1], "other")
        self.assertEqual(data["trials"]["other"], {"phone": 7, "registry": 7})
        self.assertEqual(data["phrases"]["pregnant"]["kind"], "control")
        self.assertFalse(pr.checks(data)["strata_add_up_to_base"])

    def test_markdown(self):
        md = pr.markdown(SMALL)
        self.assertIn("| a | 100 | 100 |", md)
        self.assertIn("| b | 20 | 1000 |", md)
        self.assertIn("| hearing (all wordings) | family | 42 | 21.0 | 2.0 | 1.29-3.09 | 5.5 | 2.0 | 2.0 |", md)
        self.assertIn("| hernia | control | 0 | 1.0 | 0.0* | - | 0.0 | 0.0 | 0.0 |", md)
        self.assertIn("HP1 (hearing interval above 1): holds. HP2 (hearing above visual and every kept "
                      "control, 2 rivals, chance 1 in 3): holds.", md)
        self.assertIn("Checks: strata_add_up_to_base yes, strata_add_up_to_phone_arm yes, "
                      "wordings_equal yes, nested yes.", md)

    def test_main_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            counts, out = os.path.join(d, "counts.json"), os.path.join(d, "out.json")
            with open(counts, "w", encoding="utf-8") as f:
                json.dump(SMALL, f)
            with mock.patch("builtins.print"):
                rc = pr.main(["--counts", counts, "--json", out])
            self.assertEqual(rc, 0)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["verdicts"], {"HP1": True, "HP2": True, "rivals": 2})
            self.assertEqual(data["s1"]["left_out"], ["hernia"])
            self.assertTrue(all(data["checks"].values()))


class PreregTests(unittest.TestCase):
    def test_code_matches_the_preregistration(self):
        p = load("prereg-phone-requirement.json")
        self.assertEqual(list(p["strata_in_priority_order"].items()), [tuple(s) for s in pr.STRATA])
        self.assertEqual(p["exposure"], pr.REQUIREMENT)
        self.assertEqual(p["not_va"], pr.NOT_VA)
        self.assertEqual(p["phrases"], pr.PHRASES)
        self.assertEqual(p["left_out_of_every_stratum"], vm.OWN)
        self.assertEqual(p["controls_with_own_condition_left_out"], vm.CONTROLS)
        self.assertEqual(p["min_expected_phone_matches"], vm.MIN_EXPECTED)
        self.assertEqual(p["counts_file"], pr.COUNTS)
        self.assertEqual(list(p["stratum_sizes_known_before"]), [s for s, _ in pr.STRATA])
        self.assertEqual(list(p["wording_check_known_before"]), ["base"] + pr.WORDINGS)

    def test_stratum_sizes_add_up(self):
        p = load("prereg-phone-requirement.json")
        sizes, w = p["stratum_sizes_known_before"], p["wording_check_known_before"]
        self.assertEqual(sum(s["registry"] for s in sizes.values()), w["base"])
        self.assertEqual(sum(s["phone"] for s in sizes.values()), w["(phone OR telephone)"])
        self.assertEqual(len({w[x] for x in pr.WORDINGS}), 1)
        for s in sizes.values():
            self.assertLess(s["phone"], s["registry"])

    def test_base_is_inside_the_telephone_test(self):
        # Non-VA telephone trials (2026-10-16) are a subset of all telephone trials (2026-10-15).
        p = load("prereg-phone-requirement.json")
        tel = load("prereg-phone-matched.json")["stratum_sizes_known_before"]
        for s, size in p["stratum_sizes_known_before"].items():
            self.assertLessEqual(size["registry"], tel[s]["phone"])

    def test_note_quotes_the_preregistration(self):
        p = load("prereg-phone-requirement.json")
        md = load("PREREG-PHONE-REQUIREMENT.md")
        sizes, w = p["stratum_sizes_known_before"], p["wording_check_known_before"]
        for s, size in sizes.items():
            self.assertIn("| %s | %s | %s |" % (s, "{:,}".format(size["phone"]),
                                                 "{:,}".format(size["registry"])), md)
        self.assertIn("| sum | {:,} | {:,} |".format(w["(phone OR telephone)"], w["base"]), md)
        self.assertIn("| (none: the whole base) | {:,} |".format(w["base"]), md)
        for x in pr.WORDINGS:
            self.assertIn("| `%s` | %s |" % (x, "{:,}".format(w[x])), md)
        share = round(100.0 * w["(phone OR telephone)"] / w["base"], 1)
        self.assertIn("A phone is named in %s%% of base trials" % share, md)
        self.assertIn("(a) in at least %d of 20" % p["s2_requirement_prediction_at_least"], md)
        self.assertIn("at least %d of 20, HP1" % p["s2_tied_reading_rule_at_least"], md)
        for s in (pr.NOT_VA, pr.REQUIREMENT, "2.45 times (2.17-2.75)", "4 of 20", "13 of the",
                  "160 small requests"):
            self.assertIn(s, md)


class PublishedTests(unittest.TestCase):
    def test_counts_file(self):
        path = os.path.join(HERE, pr.COUNTS)
        if not os.path.exists(path):
            self.skipTest("phone-requirement-counts.json not counted yet")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["strata"], [s for s, _ in pr.STRATA])
        self.assertEqual(list(data["phrases"]), pr.PHRASES)
        for p, c in data["phrases"].items():
            self.assertEqual(c["kind"], vm.kind(p))
        c = pr.checks(data)
        self.assertTrue(c["strata_add_up_to_base"] and c["strata_add_up_to_phone_arm"] and c["nested"])
        # Counted on a later day than the sizes fixed in advance: allow the registry's drift only.
        before = load("prereg-phone-requirement.json")["stratum_sizes_known_before"]
        for s in data["strata"]:
            for k in ("phone", "registry"):
                self.assertLessEqual(abs(data["trials"][s][k] - before[s][k]),
                                     max(5, 0.02 * before[s][k]), (s, k))


if __name__ == "__main__":
    unittest.main()
