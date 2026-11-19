"""Plain unit tests, no Band account and no Nettacker needed.

Run: python -m unittest discover tests
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.blue_agent import PLAYBOOK, plan, respond  # noqa: E402
from agents.red_agent import MODULES, confirmed  # noqa: E402


def report(*ids):
    return {"findings": [{"id": i, "severity": "low"} for i in ids]}


class BlueTests(unittest.TestCase):
    def test_every_red_finding_has_a_blue_fix(self):
        for key, _title, _sev in MODULES.values():
            self.assertIn(key, PLAYBOOK)

    def test_plan_changes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            patch = os.path.join(d, "patches.json")
            plan(report("open_cors"))
            self.assertFalse(os.path.exists(patch))

    def test_respond_writes_patches_and_log(self):
        with tempfile.TemporaryDirectory() as d:
            patch, log = os.path.join(d, "p.json"), os.path.join(d, "l.jsonl")
            respond(report("open_cors", "weak_cookie"), patch, log)
            self.assertEqual(json.load(open(patch)),
                             {"restrict_cors": True, "harden_cookie": True})
            lines = [json.loads(x) for x in open(log)]
            self.assertEqual([x["finding"] for x in lines], ["open_cors", "weak_cookie"])
            self.assertTrue(all("time" in x for x in lines))

    def test_unknown_finding_goes_to_a_human(self):
        with tempfile.TemporaryDirectory() as d:
            acts = respond(report("mystery"), os.path.join(d, "p.json"))
            self.assertIn("human", acts[0]["action"])


def event(url, code):
    return {"json_event": {"url": url,
                           "response": {"conditions_results": {"status_code": [code]}}}}


class RedFilterTests(unittest.TestCase):
    def test_admin_scan_needs_200_on_a_real_path(self):
        evs = [event("http://127.0.0.1:8081/", "200"),
               event("http://127.0.0.1:8081/secret", "403"),
               event("http://127.0.0.1:8081/admin", "200")]
        kept = confirmed("admin_scan", evs)
        self.assertEqual([e["json_event"]["url"] for e in kept],
                         ["http://127.0.0.1:8081/admin"])

    def test_other_modules_pass_through(self):
        evs = [event("http://127.0.0.1:8081/", "200")]
        self.assertEqual(confirmed("http_cors_vuln", evs), evs)


if __name__ == "__main__":
    unittest.main()
