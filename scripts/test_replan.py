"""Behavioral tests; isolated temporary projects, no external harness or project changes."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
spec = importlib.util.spec_from_file_location("replan", Path(__file__).with_name("replan.py"))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class Workflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="replan-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        p.initialize(self.root, "Example Project")
        self.plan = self.root / "replan"

    def save(self, name, value):
        (self.plan / name).write_bytes(p.encode(value))

    def populated(self):
        scope = p.read(self.plan / "SCOPE.json")
        scope.update(status="approved", outcomes=["A working private tool"],
                     authorization={"allowed": ["Local implementation and testing"], "requires_separate_authorization": ["Publication"]},
                     preflight_task="PA-01", first_review_task="PA-04", full_release_task="PA-05")
        self.save("SCOPE.json", scope)
        for name in ("BRAND.lock.json", "SOURCE_INVENTORY.json"):
            self.save(name, {"files": [], "applicability": "not_applicable", "reason": "Synthetic greenfield test fixture has no external foundation or brand assets"})
        tasks = []
        deps = {1: [], 2: ["PA-01"], 3: ["PA-01"], 4: ["PA-02", "PA-03"], 5: ["PA-04"]}
        for i in range(1, 6):
            tasks.append({"id": f"PA-{i:02}", "title": f"Task {i}", "status": "planned", "kind": "test" if i == 1 else "implementation",
                          "depends_on": deps[i], "feature_ids": ["FA-01"], "work": f"Concrete work {i}",
                          "acceptance": [f"Outcome {i}"], "owned_paths": [f"track{i}"], "resources": [], "evidence": []})
        self.save("TASKS.json", {"tasks": tasks})
        self.save("FEATURES.json", {"features": [{"id": "FA-01", "title": "Working product", "status": "planned", "acceptance": ["User journey works"], "acceptance_map": {"User journey works": [{"task_id": "PA-05", "acceptance_item": "Outcome 5"}]}, "task_ids": [t["id"] for t in tasks], "evidence": []}]})
        return p.load_pack(self.root)

    def verify(self, tid):
        doc = p.read(self.plan / "TASKS.json")
        task = next(t for t in doc["tasks"] if t["id"] == tid)
        log = f"evidence/{tid}.log"
        (self.plan / log).write_text("Actual synthetic test fixture outcome\n", encoding="utf-8")
        proof = {"task_id": tid, "candidate_commit": "a" * 40, "environment": {"os": "test-fixture"},
                 "checks": [{"acceptance_item": a, "result": "passed", "command": "synthetic fixture check", "artifact": log} for a in task["acceptance"]],
                 "review": "Synthetic fixture review", "limitations": ["Not live harness qualification"],
                 "engineering_review": dict.fromkeys(["design", "simplification", "language_review", "dependencies", "performance", "ux"], "Synthetic fixture")}
        path = f"evidence/{tid}.json"
        self.save(path, proof)
        task.update(status="verified", evidence=[path])
        self.save("TASKS.json", doc)

    def active(self):
        scope, tasks, features, state = self.populated()
        binding = {"project_id": scope["project_id"], "supervisor_thread_id": "test-supervisor", "profile": {"provider": "fixture", "model": "fixture", "options": {"effort": "high"}}}
        p.mutate("bind", self.root, scope, tasks, state, binding, None)
        p.mutate("authorize", self.root, scope, tasks, state, {}, "Implement this local project")
        self.verify("PA-01")
        scope, tasks, features, _ = p.load_pack(self.root)
        p.mutate("preflight", self.root, scope, tasks, state, {"evidence": "evidence/PA-01.json"}, None)
        return scope, tasks, state

    def job(self, tid, key=None):
        return {"key": key or tid, "client_request_id": "request-" + (key or tid), "pa_task": tid,
                "base_commit": "a" * 40, "owned_paths": ["track" + str(int(tid[-2:]))], "resources": []}

    def attach(self, scope, tasks, state, key):
        p.mutate("attach", self.root, scope, tasks, state,
                 {"key": key, "task_id": "actual-fixture-task-" + key, "child_thread_id": "fixture-child-" + key,
                  "run_id": "fixture-run", "link": "fixture-link", "profile": state["binding"]["profile"]}, None)

    def test_draft_is_not_execution(self):
        s, t, f, state = p.load_pack(self.root)
        self.assertEqual(p.decision(s, t, state)["decision"], "stop")
        self.assertFalse(state["schedule"]["enabled"])
        with self.assertRaises(p.Invalid):
            p.initialize(self.root, "Overwrite")

    def test_graph_cycle_and_reciprocity(self):
        self.populated()
        doc = p.read(self.plan / "TASKS.json")
        doc["tasks"][0]["depends_on"] = ["PA-05"]
        self.save("TASKS.json", doc)
        with self.assertRaisesRegex(p.Invalid, "cycle"):
            p.load_pack(self.root)
        doc["tasks"][0]["depends_on"] = []
        doc["tasks"][0]["feature_ids"] = []
        self.save("TASKS.json", doc)
        with self.assertRaises(p.Invalid):
            p.load_pack(self.root)

    def test_release_cannot_drop_scope(self):
        self.populated()
        doc = p.read(self.plan / "TASKS.json")
        doc["tasks"][3]["depends_on"] = ["PA-02"]
        self.save("TASKS.json", doc)
        with self.assertRaisesRegex(p.Invalid, "retain every task"):
            p.load_pack(self.root)

    def test_parallel_batch_and_scheduled_yield(self):
        scope, tasks, state = self.active()
        p.reserve(scope, tasks, state, {"jobs": [self.job("PA-02"), self.job("PA-03")]})
        self.assertEqual(len(p.live(state)), 2)
        self.assertEqual(p.decision(scope, tasks, state)["decision"], "yield")
        for key in ("PA-02", "PA-03"):
            self.attach(scope, tasks, state, key)
        self.assertEqual(p.decision(scope, tasks, state)["free_slots"], 1)
        state["schedule"].update(id="fixture-schedule", enabled=True)
        self.assertEqual(p.decision(scope, tasks, state, scheduled=True)["decision"], "yield")

    def test_overlap_and_resource_collisions(self):
        scope, tasks, state = self.active()
        for by_resource in (False, True):
            local = copy.deepcopy(state)
            a, b = self.job("PA-02"), self.job("PA-03")
            if by_resource:
                a["resources"] = b["resources"] = ["owned-vm"]
            else:
                b["owned_paths"] = ["track2/child"]
            for job in (a, b):
                tasks[job["pa_task"]].update(owned_paths=job["owned_paths"], resources=job["resources"])
            with self.assertRaisesRegex(p.Invalid, "Overlapping"):
                p.reserve(scope, tasks, local, {"jobs": [a, b]})

    def test_unknown_receipt_cannot_expire(self):
        scope, tasks, state = self.active()
        p.reserve(scope, tasks, state, {"jobs": [self.job("PA-02")]})
        state["jobs"][0]["reserved_utc"] = "1990-01-01T00:00:00Z"
        self.assertEqual(p.decision(scope, tasks, state)["decision"], "yield")
        with self.assertRaises(p.Invalid):
            p.reserve(scope, tasks, state, {"jobs": [self.job("PA-03")]})

    def test_duplicate_after_terminal_is_rejected(self):
        scope, tasks, state = self.active()
        p.reserve(scope, tasks, state, {"jobs": [self.job("PA-02")]})
        self.attach(scope, tasks, state, "PA-02")
        p.mutate("terminal", self.root, scope, tasks, state, {"key": "PA-02", "status": "completed", "terminal_evidence": "Actual fixture completion"}, None)
        with self.assertRaisesRegex(p.Invalid, "Reused"):
            p.reserve(scope, tasks, state, {"jobs": [self.job("PA-02")]})

    def test_pause_preserves_external_schedule_and_explicit_resume(self):
        scope, tasks, state = self.active()
        state["schedule"].update(id="fixture-schedule", enabled=True)
        p.mutate("pause", self.root, scope, tasks, state, {}, "Pause tonight")
        self.assertTrue(state["schedule"]["enabled"])
        self.assertEqual(p.decision(scope, tasks, state)["decision"], "stop")
        with self.assertRaises(p.Invalid):
            p.mutate("resume", self.root, scope, tasks, state, {}, "Resume")
        state["schedule"]["enabled"] = False
        with self.assertRaises(p.Invalid):
            p.mutate("resume", self.root, scope, tasks, state, {}, None)
        p.mutate("resume", self.root, scope, tasks, state, {}, "Resume tomorrow")
        self.assertFalse(state["stop_requested"])
        self.assertIsNone(state["preflight"])
        self.assertFalse(state["schedule"]["enabled"])

    def test_review_cannot_resume_as_ordinary_pause(self):
        scope, tasks, state = self.active()
        self.verify("PA-02")
        self.verify("PA-03")
        self.verify("PA-04")
        scope, tasks, _, _ = p.load_pack(self.root)
        p.mutate("review", self.root, scope, tasks, state, {}, None)
        p.mutate("pause", self.root, scope, tasks, state, {}, "Pause")
        with self.assertRaises(p.Invalid):
            p.mutate("resume", self.root, scope, tasks, state, {}, "Resume")

    def test_mixed_candidate_evidence_refused(self):
        self.populated()
        self.verify("PA-01")
        proof = p.read(self.plan / "evidence/PA-01.json")
        proof["candidate_commit"] = "b" * 40
        self.save("evidence/other.json", proof)
        doc = p.read(self.plan / "TASKS.json")
        doc["tasks"][0]["evidence"].append("evidence/other.json")
        self.save("TASKS.json", doc)
        with self.assertRaisesRegex(p.Invalid, "different candidates"):
            p.load_pack(self.root)

    def test_unverified_dependency_and_missing_acceptance_proof(self):
        self.populated()
        self.verify("PA-02")
        with self.assertRaisesRegex(p.Invalid, "Unverified dependency"):
            p.load_pack(self.root)
        self.verify("PA-01")
        proof = p.read(self.plan / "evidence/PA-01.json")
        proof["checks"][0]["acceptance_item"] = "Something else"
        self.save("evidence/PA-01.json", proof)
        with self.assertRaisesRegex(p.Invalid, "Incomplete acceptance"):
            p.load_pack(self.root)

    def test_unknown_schedule_intent_blocks_second_create(self):
        scope, tasks, state = self.active()
        p.mutate("schedule-intent", self.root, scope, tasks, state, {"client_request_id": "fixture-intent"}, None)
        self.assertEqual(p.decision(scope, tasks, state)["decision"], "yield")
        with self.assertRaises(p.Invalid):
            p.mutate("schedule-intent", self.root, scope, tasks, state, {"client_request_id": "duplicate"}, None)
        receipt = {"id": "fixture-schedule", "enabled": True, "bound_thread_id": "test-supervisor", "interval_ms": 1800000, "evidence": "Fixture tool receipt"}
        p.mutate("schedule-record", self.root, scope, tasks, state, receipt, None)
        receipt["id"] = "different-schedule"
        with self.assertRaises(p.Invalid):
            p.mutate("schedule-record", self.root, scope, tasks, state, receipt, None)

    def test_bootstrap_allows_preflight_only(self):
        scope, tasks, _, state = self.populated()
        state.update(owner_start_authorized=True, stop_requested=False, phase="executing",
                     binding={"supervisor_thread_id": "fixture"})
        self.assertEqual(p.decision(scope, tasks, state)["decision"], "bootstrap")
        p.reserve(scope, tasks, state, {"jobs": [self.job("PA-01")]})
        self.assertEqual(len(p.live(state)), 1)

    def test_corrupt_json_and_workspace_copy_refused(self):
        bad = self.root / "bad.json"
        bad.write_text('{"name":1,"NAME":2}', encoding="utf-8")
        with self.assertRaisesRegex(p.Invalid, "Duplicate"):
            p.read(bad)
        state = p.read(self.root / "RUN_STATE.json")
        state["workspace"] = "some-other-worktree"
        (self.root / "RUN_STATE.json").write_bytes(p.encode(state))
        with self.assertRaisesRegex(p.Invalid, "integration workspace"):
            p.load_pack(self.root)

    def test_atomic_failure_and_compare_preserve_original(self):
        path = self.root / "RUN_STATE.json"
        original = path.read_bytes()
        value = p.read(path)
        value["revision"] += 1
        with patch.object(p.os, "replace", side_effect=OSError("Injected replacement failure")):
            with self.assertRaises(OSError):
                p.atomic(path, value, original)
        self.assertEqual(path.read_bytes(), original)
        with self.assertRaises(p.Invalid):
            p.atomic(path, value, b"wrong expected bytes")
        self.assertEqual(path.read_bytes(), original)

    def test_cross_process_lock_contention(self):
        code = "import sys; sys.path.insert(0,sys.argv[1]); import replan as p;\nwith p.lease(sys.argv[2]): print('unexpected')"
        with p.lease(self.root):
            result = subprocess.run([sys.executable, "-c", code, str(Path(__file__).parent), str(self.root)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Lease busy", result.stderr)
        with p.lease(self.root):
            pass

    def test_live_profile_mismatch_refused(self):
        scope, tasks, state = self.active()
        p.reserve(scope, tasks, state, {"jobs": [self.job("PA-02")]})
        receipt = {"key": "PA-02", "task_id": "task", "child_thread_id": "thread", "run_id": "run", "link": "link", "profile": {"provider": "wrong"}}
        with self.assertRaisesRegex(p.Invalid, "profile differs"):
            p.mutate("attach", self.root, scope, tasks, state, receipt, None)

    def test_cli_failed_batch_does_not_persist_partial_reservation(self):
        scope, tasks, state = self.active()
        path = self.root / "RUN_STATE.json"
        path.write_bytes(p.encode(state))
        a, b = self.job("PA-02"), self.job("PA-03")
        b["owned_paths"] = ["wrong"]
        request = self.root / "batch.json"
        request.write_bytes(p.encode({"jobs": [a, b]}))
        original = path.read_bytes()
        result = subprocess.run([sys.executable, str(Path(__file__).with_name("replan.py")), "reserve", "--workspace", str(self.root), "--input", str(request)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(path.read_bytes(), original)

    def test_successful_cli_reservation_survives_restart(self):
        scope, tasks, state = self.active()
        (self.root / "RUN_STATE.json").write_bytes(p.encode(state))
        request = self.root / "batch.json"
        request.write_bytes(p.encode({"jobs": [self.job("PA-02"), self.job("PA-03")]}))
        script = str(Path(__file__).with_name("replan.py"))
        result = subprocess.run([sys.executable, script, "reserve", "--workspace", str(self.root), "--input", str(request)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = p.read(self.root / "RUN_STATE.json")
        self.assertEqual(len(after["jobs"]), 2)
        self.assertEqual(after["revision"], state["revision"] + 1)
        restarted = subprocess.run([sys.executable, script, "guard", "--workspace", str(self.root), "--scheduled"], capture_output=True, text=True)
        self.assertEqual(restarted.returncode, 0)
        self.assertEqual(json.loads(restarted.stdout)["decision"], "yield")

    def test_full_budget_and_blocked_resume_preserve_work(self):
        scope, tasks, state = self.active()
        state["max_active_children"] = 1
        with self.assertRaisesRegex(p.Invalid, "budget"):
            p.reserve(scope, tasks, state, {"jobs": [self.job("PA-02"), self.job("PA-03")]})
        p.reserve(scope, tasks, state, {"jobs": [self.job("PA-02")]})
        self.attach(scope, tasks, state, "PA-02")
        self.assertEqual(p.decision(scope, tasks, state)["free_slots"], 0)
        p.mutate("pause", self.root, scope, tasks, state, {}, "Pause now")
        with self.assertRaisesRegex(p.Invalid, "Settle"):
            p.mutate("resume", self.root, scope, tasks, state, {}, "Resume")
        self.assertEqual(state["jobs"][0]["status"], "running")

    def test_disabled_schedule_receipt_cannot_reenable_paused_run(self):
        scope, tasks, state = self.active()
        p.mutate("schedule-intent", self.root, scope, tasks, state, {"client_request_id": "fixture-intent"}, None)
        receipt = {"id": "fixture-schedule", "enabled": True, "bound_thread_id": "test-supervisor", "interval_ms": 1800000, "evidence": "Fixture receipt"}
        p.mutate("schedule-record", self.root, scope, tasks, state, receipt, None)
        p.mutate("pause", self.root, scope, tasks, state, {}, "Pause")
        with self.assertRaises(p.Invalid):
            p.mutate("schedule-record", self.root, scope, tasks, state, receipt, None)
        receipt["enabled"] = False
        p.mutate("schedule-record", self.root, scope, tasks, state, receipt, None)
        self.assertFalse(state["schedule"]["enabled"])
        self.assertTrue(state["stop_requested"])

    def test_windows_alias_batch_is_rejected_atomically(self):
        scope, tasks, state = self.active()
        doc = p.read(self.plan / "TASKS.json")
        doc["tasks"][2]["owned_paths"] = ["track2./child"]
        self.save("TASKS.json", doc)
        path = self.root / "RUN_STATE.json"
        path.write_bytes(p.encode(state))
        a, b = self.job("PA-02"), self.job("PA-03")
        b["owned_paths"] = ["track2./child"]
        request = self.root / "alias-batch.json"
        request.write_bytes(p.encode({"jobs": [a, b]}))
        original = path.read_bytes()
        result = subprocess.run([sys.executable, str(Path(__file__).with_name("replan.py")), "reserve", "--workspace", str(self.root), "--input", str(request)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(p.read(path)["jobs"], [])

    def test_legacy_pack_is_refused_without_changes(self):
        legacy = Path(self.temp.name) / "legacy"
        (legacy / "powerplan/tools").mkdir(parents=True)
        (legacy / "powerplan/tools/powerplan.py").write_text("# pinned legacy helper\n", encoding="utf-8")
        (legacy / "RUN_STATE.json").write_text('{"stop_requested":true}\n', encoding="utf-8")
        before = {str(f.relative_to(legacy)): f.read_bytes() for f in legacy.rglob("*") if f.is_file()}
        with self.assertRaisesRegex(p.Invalid, "Legacy powerplan pack"):
            p.initialize(legacy, "Do not replace")
        for command in ("init", "validate", "pause"):
            args = [sys.executable, str(Path(__file__).with_name("replan.py")), command,
                    "--workspace", str(legacy), "--name", "Do not replace"]
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("pinned powerplan/tools/powerplan.py", result.stdout)
        after = {str(f.relative_to(legacy)): f.read_bytes() for f in legacy.rglob("*") if f.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((legacy / "replan").exists())
        self.assertFalse((legacy / ".replan-local").exists())

    def test_relative_paths_refuse_windows_aliases_and_devices(self):
        for value in ("track2./child", "track2 /child", "track/child.", "track/child ",
                      "CON", "nul.txt", "track/COM1.log", "track/lpt9", "track/COM¹",
                      "track/a?b", "track/a|b", 'track/a"b', "track/a\x00b"):
            with self.subTest(value=value), self.assertRaises(p.Invalid):
                p.relative(value)
        self.assertEqual(str(p.relative("track2.folder/child-name.txt")), "track2.folder/child-name.txt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
