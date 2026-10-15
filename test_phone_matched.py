"""Offline tests for phone_matched (no network). Apache-2.0."""

import copy
import json
import os
import tempfile
import unittest
from unittest import mock

import phone_matched as pm
import va_matched as vm

HERE = os.path.dirname(os.path.abspath(__file__))
# Two strata. Hearing is twice as common in telephone trials in both (matched 2.0, 1.29-3.09;
# unmatched 5.5). Visual and pregnant are as common in both (1.0). Hernia is too rare to keep
# (1.0 telephone match expected).
SMALL = {
    "strata": ["a", "b"],
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


class TermTests(unittest.TestCase):
    def test_first_stratum_telephone(self):
        self.assertEqual(pm.term(0, phone=True),
                         "AREA[StudyType]INTERVENTIONAL AND AREA[Phase]NA AND "
                         "AREA[InterventionSearch]telephone AND AREA[ConditionSearch](PTSD) AND "
                         "NOT AREA[ConditionSearch](%s)" % vm.OWN)

    def test_other_stratum_leaves_out_all_five_and_the_control_condition(self):
        self.assertEqual(pm.term(5, "hernia"),
                         'AREA[StudyType]INTERVENTIONAL AND AREA[Phase]NA AND '
                         'AREA[EligibilityCriteria]"hernia" AND NOT AREA[ConditionSearch](%s OR %s OR hernia)'
                         % (" OR ".join(c for _, c in vm.STRATA), vm.OWN))

    def test_all_trial_counts_are_the_va_tests_queries(self):
        for i in range(5):
            self.assertEqual(pm.term(i), vm.term(i))
            self.assertEqual(pm.term(i, "pregnant"), vm.term(i, "pregnant"))
            self.assertEqual(pm.term(i, "hearing (all wordings)"), vm.term(i, "hearing (all wordings)"))

    def test_strata_and_phrases(self):
        self.assertEqual([s for s, _ in pm.STRATA],
                         ["ptsd", "substance use", "depression", "pain", "cardiometabolic", "other"])
        self.assertEqual(pm.PHRASES, vm.PHRASES)


class MathTests(unittest.TestCase):
    def test_rows_use_va_matched(self):
        h, v, c, x = pm.rows(SMALL)
        self.assertEqual((h["mh"], h["low"], h["high"], h["crude"]), (2.0, 1.29, 3.09, 5.5))
        self.assertEqual((h["va"], h["expected"], h["kept"]), (42, 21.0, True))
        self.assertEqual((v["mh"], c["mh"], c["kept"]), (1.0, 1.0, True))
        self.assertEqual((x["mh"], x["expected"], x["kept"]), (0.0, 1.0, False))

    def test_verdicts(self):
        self.assertEqual(pm.verdicts(pm.rows(SMALL)), {"HP1": True, "HP2": True, "rivals": 2})

    def test_hp2_fails_when_visual_rises_as_much(self):
        d = copy.deepcopy(SMALL)
        d["phrases"]["visual (all wordings)"] = dict(d["phrases"]["hearing (all wordings)"])
        self.assertEqual(pm.verdicts(pm.rows(d)), {"HP1": True, "HP2": False, "rivals": 2})

    def test_hp1_fails_when_hearing_is_level(self):
        d = copy.deepcopy(SMALL)
        d["phrases"]["hearing (all wordings)"] = dict(d["phrases"]["pregnant"], kind="family")
        self.assertFalse(pm.verdicts(pm.rows(d))["HP1"])


class RunTests(unittest.TestCase):
    def test_fetch_counts(self):
        urls = []

        def fake(u):
            urls.append(u)
            return {"totalCount": 7}

        data = pm.fetch_counts(["pregnant"], fetch=fake, pause=0)
        self.assertEqual(len(urls), 24)
        self.assertEqual(sum("telephone" in u for u in urls), 12)
        self.assertEqual(data["strata"][-1], "other")
        self.assertEqual(data["trials"]["other"], {"phone": 7, "registry": 7})
        self.assertEqual(data["phrases"]["pregnant"]["kind"], "control")
        self.assertEqual(data["phrases"]["pregnant"]["ptsd"], {"phone": 7, "registry": 7})

    def test_markdown(self):
        md = pm.markdown(SMALL)
        self.assertIn("| a | 100 | 100 |", md)
        self.assertIn("| b | 20 | 1000 |", md)
        self.assertIn("| hearing (all wordings) | family | 42 | 21.0 | 2.0 | 1.29-3.09 | 5.5 | 2.0 | 2.0 |", md)
        self.assertIn("| hernia | control | 0 | 1.0 | 0.0* | - | 0.0 | 0.0 | 0.0 |", md)
        self.assertIn("HP1 (hearing interval above 1): holds. HP2 (hearing above visual and every kept "
                      "control, 2 rivals, chance 1 in 3): holds.", md)

    def test_main_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            counts, out = os.path.join(d, "counts.json"), os.path.join(d, "out.json")
            with open(counts, "w", encoding="utf-8") as f:
                json.dump(SMALL, f)
            with mock.patch("builtins.print"):
                rc = pm.main(["--counts", counts, "--json", out])
            self.assertEqual(rc, 0)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["verdicts"], {"HP1": True, "HP2": True, "rivals": 2})
            self.assertEqual(data["s1"]["left_out"], ["hernia"])


class PreregTests(unittest.TestCase):
    def load(self, folder, name):
        path = os.path.join(HERE, "results", folder, name)
        if not os.path.exists(path):
            self.skipTest("%s not present" % name)
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_code_matches_the_preregistration(self):
        p = self.load("phone-check", "prereg-phone-matched.json")
        self.assertEqual(list(p["strata_in_priority_order"].items()), [tuple(s) for s in pm.STRATA])
        self.assertEqual(p["exposure"], pm.PHONE)
        self.assertEqual(p["phrases"], pm.PHRASES)
        self.assertEqual(p["left_out_of_every_stratum"], vm.OWN)
        self.assertEqual(p["controls_with_own_condition_left_out"], vm.CONTROLS)
        self.assertEqual(p["min_expected_phone_matches"], vm.MIN_EXPECTED)
        self.assertEqual(list(p["stratum_sizes_known_before"]), [s for s, _ in pm.STRATA])

    def test_all_trial_sizes_equal_the_va_tests(self):
        p = self.load("phone-check", "prereg-phone-matched.json")
        va = self.load("sponsor-check", "prereg-va-matched.json")
        for s, size in va["stratum_sizes_known_before"].items():
            self.assertEqual(p["stratum_sizes_known_before"][s]["registry"], size["registry"])
        for size in p["stratum_sizes_known_before"].values():
            self.assertLess(size["phone"], size["registry"])


class PublishedTests(unittest.TestCase):
    def load(self, name):
        path = os.path.join(HERE, "results", "phone-check", name)
        if not os.path.exists(path):
            self.skipTest("%s not present" % name)
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_counts_file(self):
        data = self.load("phone-matched-counts.json")
        self.assertEqual(data["strata"], [s for s, _ in pm.STRATA])
        self.assertEqual(list(data["phrases"]), pm.PHRASES)
        for p, c in data["phrases"].items():
            self.assertEqual(c["kind"], vm.kind(p))
            for s in data["strata"]:
                self.assertLessEqual(c[s]["phone"], c[s]["registry"])
                self.assertLessEqual(c[s]["registry"], data["trials"][s]["registry"])

    def test_stratum_sizes_match_the_preregistration(self):
        data = self.load("phone-matched-counts.json")
        prereg = self.load("prereg-phone-matched.json")
        self.assertEqual(data["trials"], prereg["stratum_sizes_known_before"])

    def test_result(self):
        data = self.load("phone-matched-counts.json")
        rs = {r["phrase"]: r for r in pm.rows(data)}
        # Worked out by hand on 2026-10-15 (PHONE-MATCHED-RESULT.md).
        for phrase, est in [("cognitive (all wordings)", 1.93), ("hearing (all wordings)", 2.45),
                            ("visual (all wordings)", 2.13), ("pregnant", 0.61),
                            ("hepatitis", 0.34), ("allergy", 0.25), ("migraine", 0.56),
                            ("osteoporosis", 0.43), ("claustrophobia", 0.24), ("celiac", 0.40),
                            ("hernia", 0.49), ("informed consent", 0.78)]:
            self.assertAlmostEqual(rs[phrase]["mh"], est, delta=0.011)
        for phrase, low, high in [("hearing (all wordings)", 2.17, 2.75),
                                  ("visual (all wordings)", 1.85, 2.47),
                                  ("cognitive (all wordings)", 1.84, 2.02),
                                  ("pregnant", 0.58, 0.63),
                                  ("informed consent", 0.75, 0.81)]:
            self.assertAlmostEqual(rs[phrase]["low"], low, delta=0.011)
            self.assertAlmostEqual(rs[phrase]["high"], high, delta=0.011)
        h = rs["hearing (all wordings)"]
        self.assertEqual(h["va"], 294)
        self.assertAlmostEqual(h["expected"], 120.4, delta=0.05)
        self.assertAlmostEqual(h["crude"], 2.44, delta=0.011)
        self.assertTrue(all(r["kept"] for r in rs.values()))
        self.assertEqual(pm.verdicts(list(rs.values())), {"HP1": True, "HP2": True, "rivals": 9})
        t = vm.test(list(rs.values()))
        self.assertEqual((t["families"], t["controls"], t["left_out"], t["rank_sum"], t["p"]),
                         (3, 8, [], 30.0, 0.0061))

    def test_exploratory_without_the_va(self):
        data = self.load("phone-matched-nonva-counts.json")
        full = self.load("phone-matched-counts.json")
        for s in data["strata"]:
            for k in ("phone", "registry"):
                self.assertLessEqual(data["trials"][s][k], full["trials"][s][k])
        (h,) = pm.rows(data)
        self.assertEqual(h["va"], 279)
        self.assertAlmostEqual(h["mh"], 2.41, delta=0.011)
        self.assertAlmostEqual(h["low"], 2.14, delta=0.011)
        self.assertAlmostEqual(h["high"], 2.72, delta=0.011)
        self.assertAlmostEqual(h["crude"], 2.40, delta=0.011)


if __name__ == "__main__":
    unittest.main()
