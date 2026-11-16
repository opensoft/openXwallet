"""Execute the declared main-only source-CI guard; no private dependency reads."""
import os
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/pytest-suite.yml"


def document():
    return yaml.safe_load(WORKFLOW.read_text())


class ManualMainValidation(unittest.TestCase):
    def test_manual_entrypoint_has_no_model_selectors_and_read_only_permissions(self):
        config = document()
        events = config.get("on", config.get(True))
        self.assertIn("workflow_dispatch", events)
        self.assertIn(events["workflow_dispatch"], (None, {}))
        self.assertEqual(config["permissions"], {"contents": "read"})

    def test_refusal_precedes_all_dependency_access(self):
        job = next(iter(document()["jobs"].values()))
        self.assertEqual(job["steps"][0].get("id"), "manual-main-guard")
        self.assertIn("run", job["steps"][0])

    def test_actual_guard_covers_main_branch_tag_and_pull_request_contexts(self):
        job = next(iter(document()["jobs"].values()))
        self.assertEqual(job["steps"][0].get("id"), "manual-main-guard")
        script = job["steps"][0]["run"]
        for event, ref, expected in [
            ("workflow_dispatch", "refs/heads/main", 0),
            ("workflow_dispatch", "refs/heads/feature", 1),
            ("workflow_dispatch", "refs/tags/main", 1),
            ("workflow_dispatch", "", 1),
            ("pull_request", "refs/pull/1/merge", 0),
        ]:
            with self.subTest(event=event, ref=ref):
                result = subprocess.run(
                    ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script],
                    env={"PATH": os.environ["PATH"], "VALIDATION_EVENT": event, "VALIDATION_REF": ref},
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
