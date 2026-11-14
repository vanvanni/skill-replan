"""Extended contracts and recovery checks, all synthetic and local."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
import test_replan as base
p = base.p


class Contracts(unittest.TestCase):
    setUp = base.Workflow.setUp
    save = base.Workflow.save
    populated = base.Workflow.populated
    active = base.Workflow.active
    verify = base.Workflow.verify
    job = base.Workflow.job
    attach = base.Workflow.attach

    def cli(self, command, data=None, instruction=None):
        args = [sys.executable, str(Path(__file__).with_name("replan.py")), command, "--workspace", str(self.root)]
        if data is not None:
            request = self.root / "input.json"
            request.write_bytes(p.encode(data))
            args += ["--input", str(request)]
        if instruction is not None:
            path = self.root / "instruction.txt"
            path.write_text(instruction, encoding="utf-8")
            args += ["--instruction", str(path)]
        return subprocess.run(args, capture_output=True, text=True)

    def test_generated_project_has_self_contained_pinned_tools(self):
        required = ["LOCAL_START.md", "NAMING.md", "MANIFEST.md", "SKILLS.md", "SKILLS.lock.json", "BRAND.lock.json", "SOURCE_INVENTORY.json", "EVIDENCE.schema.json", "TOOLS.lock.json", "validate-plan.py", "tools/replan.py", "tools/pack_contract.py"]
        self.assertTrue(all((self.plan / name).is_file() for name in required))
        result = subprocess.run([sys.executable, str(self.plan / "validate-plan.py")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        target = self.plan / "tools/replan.py"
        target.write_bytes(target.read_bytes() + b"\n# changed\n")
        with self.assertRaisesRegex(p.Invalid, "Locked file changed"):
            p.load_pack(self.root)

    def test_existing_owner_instructions_not_overwritten(self):
        extra = self.root.parent / "existing"
        extra.mkdir()
        (extra / "AGENTS.md").write_text("Existing owner instruction", encoding="utf-8")
        (extra / ".gitignore").write_text("Existing pattern\n", encoding="utf-8")
        p.initialize(extra, "Existing")
        self.assertEqual((extra / "AGENTS.md").read_text(), "Existing owner instruction")
        self.assertEqual((extra / ".gitignore").read_text(), "Existing pattern\n")

    def test_sources_need_exact_pins_and_assets_need_matching_bytes(self):
        self.populated()
        self.save("SOURCES.lock.json", {"sources": [{"id": "ref", "kind": "git", "location": "https://example.invalid/ref", "commit": "main"}]})
        with self.assertRaisesRegex(p.Invalid, "Unpinned"):
            p.load_pack(self.root)
        self.save("SOURCES.lock.json", {"sources": []})
        target = self.plan / "asset.txt"
        target.write_bytes(b"approved")
        self.save("BRAND.lock.json", {"applicability": "applicable", "reason": "Approved test asset", "files": [{"path": "asset.txt", "sha256": hashlib.sha256(b"approved").hexdigest(), "bytes": 8}]})
        p.load_pack(self.root)
        target.write_bytes(b"altered")
        with self.assertRaisesRegex(p.Invalid, "Locked file changed"):
            p.load_pack(self.root)

    def test_adopted_dependency_needs_version_and_review(self):
        self.populated()
        self.save("DEPENDENCIES.json", {"decisions": [{"id": "example", "status": "adopted", "rationale": "Fixture"}]})
        with self.assertRaisesRegex(p.Invalid, "Unreviewed adopted"):
            p.load_pack(self.root)

    def test_feature_leaf_mapping_is_enforced(self):
        self.populated()
        doc = p.read(self.plan / "FEATURES.json")
        doc["features"][0]["acceptance_map"]["User journey works"][0]["acceptance_item"] = "invented outcome"
        self.save("FEATURES.json", doc)
        with self.assertRaisesRegex(p.Invalid, "Unknown feature leaf"):
            p.load_pack(self.root)

    def test_raw_t3_binding_distinguishes_pack_and_harness_project(self):
        scope, tasks, _, state = self.populated()
        receipt = {"project": {"structuredContent": {"id": "actual-t3-project", "workspaceRoot": str(self.root)}},
                   "thread": {"structuredContent": {"threadId": "actual-supervisor", "runtimeMode": "full-access", "modelSelection": {"instanceId": "codex", "model": "gpt-6.1-sol", "options": [{"id": "reasoningEffort", "value": "xhigh"}]}}}}
        p.mutate("bind-t3", self.root, scope, tasks, state, receipt, None)
        self.assertEqual(state["binding"]["project_id"], scope["project_id"])
        self.assertEqual(state["binding"]["harness_project_id"], "actual-t3-project")
        self.assertEqual(state["binding"]["profile"]["options"], {"reasoningEffort": "xhigh"})
        receipt["project"]["structuredContent"]["workspaceRoot"] = str(self.root.parent)
        with self.assertRaisesRegex(p.Invalid, "workspace mismatch"):
            p.mutate("bind-t3", self.root, scope, tasks, state, receipt, None)

    def test_mcp_error_and_duplicate_actual_profile_options_rejected(self):
        with self.assertRaises(ValueError):
            p.contracts.unwrap({"isError": True, "structuredContent": {"fake": True}})
        with self.assertRaises(ValueError):
            p.contracts.profile({"options": [{"id": "effort", "value": "high"}, {"id": "effort", "value": "low"}]})

    def test_pause_and_disable_work_when_task_register_is_broken(self):
        scope, tasks, state = self.active()
        state["schedule"].update(id="schedule", enabled=True)
        (self.root / "RUN_STATE.json").write_bytes(p.encode(state))
        (self.plan / "TASKS.json").write_text("broken JSON", encoding="utf-8")
        result = self.cli("pause", instruction="Pause now")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = p.read(self.root / "RUN_STATE.json")
        self.assertTrue(after["stop_requested"])
        receipt = {"id": "schedule", "enabled": False, "bound_thread_id": "test-supervisor", "interval_ms": 1800000, "evidence": "Actual synthetic disable receipt"}
        result = self.cli("schedule-record", receipt)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(p.read(self.root / "RUN_STATE.json")["schedule"]["enabled"])

    def test_partial_runner_milestone_unlocks_without_verifying_full_task(self):
        scope, tasks, state = self.active()
        doc = p.read(self.plan / "TASKS.json")
        parent = doc["tasks"][0]
        parent.update(status="in_progress", evidence=[])
        proof = p.read(self.plan / "evidence/PA-01.json")
        proof.update(milestone_id="operational", full_task_verified=False)
        self.save("evidence/operational.json", proof)
        parent["milestones"] = {"operational": {"status": "verified", "acceptance": ["Outcome 1"], "evidence": ["evidence/operational.json"]}}
        for task in doc["tasks"][1:3]:
            task["dependency_milestones"] = {"PA-01": "operational"}
        self.save("TASKS.json", doc)
        scope, tasks, _, _ = p.load_pack(self.root)
        state["preflight"] = None
        p.mutate("runner-ready", self.root, scope, tasks, state, {"evidence": "evidence/operational.json"}, None)
        self.assertEqual(state["preflight"]["stage"], "operational")
        self.assertIn("PA-02", p.ready_tasks(tasks, state))
        self.assertEqual(tasks["PA-01"]["status"], "in_progress")
        p.mutate("schedule-intent", self.root, scope, tasks, state, {"client_request_id": "one-real-interval"}, None)
        self.assertIsNotNone(state["schedule"]["intent"])

    def test_review_advance_requires_owner_and_preserves_boundary_history(self):
        scope, tasks, state = self.active()
        for tid in ("PA-02", "PA-03", "PA-04"):
            self.verify(tid)
        scope, tasks, _, _ = p.load_pack(self.root)
        p.mutate("review", self.root, scope, tasks, state, {}, None)
        with self.assertRaises(p.Invalid):
            p.mutate("advance", self.root, scope, tasks, state, {}, None)
        p.mutate("advance", self.root, scope, tasks, state, {}, "I reviewed it; finish the full private release")
        self.assertEqual(state["review_status"], "reviewed")
        self.assertEqual(state["delivery_stage"], "full_release")
        self.assertIsNone(state["preflight"])
        self.assertEqual(p.decision(scope, tasks, state)["decision"], "bootstrap")
        p.mutate("pause", self.root, scope, tasks, state, {}, "Pause full release work")
        p.mutate("resume", self.root, scope, tasks, state, {}, "Resume full release work")
        self.assertEqual(state["delivery_stage"], "full_release")

    def test_settlement_requires_fresh_runtime_audit_and_actual_settled_processes(self):
        scope, tasks, state = self.active()
        p.mutate("runtime-record", self.root, scope, tasks, state, {"key": "owned-server", "status": "running", "evidence": "Synthetic process receipt"}, None)
        p.mutate("pause", self.root, scope, tasks, state, {}, "Pause")
        self.assertFalse(p.settlement(state)["safe_to_close"])
        with self.assertRaises(p.Invalid):
            p.mutate("runtime-audit", self.root, scope, tasks, state, {"no_untracked_processes": True, "evidence": "evidence/PA-01.json"}, None)
        p.mutate("runtime-record", self.root, scope, tasks, state, {"key": "owned-server", "status": "settled", "evidence": "Synthetic confirmed process exit"}, None)
        self.assertFalse(p.settlement(state)["safe_to_close"])
        p.mutate("runtime-audit", self.root, scope, tasks, state, {"no_untracked_processes": True, "evidence": "evidence/PA-01.json"}, None)
        self.assertTrue(p.settlement(state)["safe_to_close"])
        p.mutate("pause", self.root, scope, tasks, state, {}, "Confirm pause again")
        self.assertFalse(p.settlement(state)["safe_to_close"])

    def test_three_diagnosed_failures_block_only_affected_track(self):
        scope, tasks, state = self.active()
        for i in range(3):
            p.mutate("attempt", self.root, scope, tasks, state,
                     {"pa_task": "PA-02", "blocker": "fixture-failure", "result": "failed", "diagnosis": f"Cause {i}", "changed_approach": f"Change {i}"}, None)
        self.assertNotIn("PA-02", p.ready_tasks(tasks, state))
        self.assertIn("PA-03", p.ready_tasks(tasks, state))
        with self.assertRaisesRegex(p.Invalid, "exhausted"):
            p.mutate("attempt", self.root, scope, tasks, state, {"pa_task": "PA-02", "blocker": "fixture-failure", "result": "failed", "diagnosis": "Same cause"}, None)
        p.mutate("attempt", self.root, scope, tasks, state, {"pa_task": "PA-02", "blocker": "fixture-failure", "result": "resolved", "diagnosis": "Verified root cause fixed"}, None)
        self.assertIn("PA-02", p.ready_tasks(tasks, state))
        self.assertEqual(len(state["attempts"]), 4)

    def test_continuation_prompt_bound_and_no_template_fields(self):
        scope, tasks, state = self.active()
        state["binding"]["harness_project_id"] = "actual-fixture-project"
        prompt = p.contracts.render_prompt(self.root, state)
        self.assertIn(str(self.root), prompt)
        self.assertIn("test-supervisor", prompt)
        self.assertIn("guard --scheduled", prompt)
        self.assertNotIn("<project>", prompt)

    def test_full_synthetic_lifecycle_through_final_feature_release(self):
        scope, tasks, state = self.active()
        p.reserve(scope, tasks, state, {"jobs": [self.job("PA-02"), self.job("PA-03")]})
        for tid in ("PA-02", "PA-03"):
            self.attach(scope, tasks, state, tid)
            p.mutate("terminal", self.root, scope, tasks, state, {"key": tid, "status": "completed", "terminal_evidence": "Synthetic actual fixture completion"}, None)
            self.verify(tid)
        self.verify("PA-04")
        scope, tasks, _, _ = p.load_pack(self.root)
        p.mutate("review", self.root, scope, tasks, state, {}, None)
        self.assertEqual(p.decision(scope, tasks, state)["decision"], "stop")
        p.mutate("advance", self.root, scope, tasks, state, {}, "Proceed to full release")
        p.mutate("preflight", self.root, scope, tasks, state, {"evidence": "evidence/PA-01.json"}, None)
        self.assertIn("PA-05", p.ready_tasks(tasks, state))
        self.verify("PA-05")
        scope, tasks, _, _ = p.load_pack(self.root)
        with self.assertRaisesRegex(p.Invalid, "feature acceptance"):
            p.mutate("finish", self.root, scope, tasks, state, {}, None)
        features = p.read(self.plan / "FEATURES.json")
        features["features"][0].update(status="verified", evidence=["evidence/PA-05.json"])
        self.save("FEATURES.json", features)
        p.mutate("finish", self.root, scope, tasks, state, {}, None)
        self.assertTrue(state["stop_requested"])
        self.assertEqual(state["phase"], "completed")
        p.mutate("runtime-audit", self.root, scope, tasks, state, {"no_untracked_processes": True, "evidence": "evidence/PA-05.json"}, None)
        self.assertTrue(p.settlement(state)["safe_to_close"])

    def test_full_release_cannot_use_partial_milestone_as_full_completion(self):
        self.populated()
        self.verify("PA-01")
        self.verify("PA-02")
        self.verify("PA-03")
        self.verify("PA-04")
        self.verify("PA-05")
        doc = p.read(self.plan / "TASKS.json")
        parent = doc["tasks"][0]
        parent.update(status="in_progress", evidence=[])
        proof = p.read(self.plan / "evidence/PA-01.json")
        proof.update(milestone_id="operational", full_task_verified=False)
        self.save("evidence/operational.json", proof)
        parent["milestones"] = {"operational": {"status": "verified", "acceptance": ["Outcome 1"], "evidence": ["evidence/operational.json"]}}
        for task in doc["tasks"][1:3]:
            task["dependency_milestones"] = {"PA-01": "operational"}
        self.save("TASKS.json", doc)
        with self.assertRaisesRegex(p.Invalid, "partial milestones"):
            p.load_pack(self.root)

    def test_required_lock_cannot_be_removed_to_skip_verification(self):
        self.populated()
        (self.plan / "BRAND.lock.json").unlink()
        with self.assertRaisesRegex(p.Invalid, "Required portable pack resource"):
            p.load_pack(self.root)

    def test_confirmed_no_schedule_created_preserves_reservation_history(self):
        scope, tasks, state = self.active()
        p.mutate("schedule-intent", self.root, scope, tasks, state, {"client_request_id": "confirmed-rejected-create"}, None)
        with self.assertRaises(p.Invalid):
            p.mutate("schedule-resolve", self.root, scope, tasks, state, {"status": "unknown", "evidence": "Outcome not known"}, None)
        p.mutate("schedule-resolve", self.root, scope, tasks, state, {"status": "not_created", "evidence": "Synthetic authoritative rejection before creation"}, None)
        self.assertIsNone(state["schedule"]["intent"])
        self.assertEqual(len(state["schedule"]["resolved_intents"]), 1)
        self.assertEqual(p.decision(scope, tasks, state)["decision"], "ready")

    def test_read_only_source_inventory_verifies_external_pinned_root(self):
        self.populated()
        source = self.root.parent / "read-only-reference"
        source.mkdir()
        (source / "reference.txt").write_bytes(b"source foundation")
        self.save("SOURCES.lock.json", {"sources": [{"id": "foundation", "kind": "git", "location": "https://example.invalid/reference", "commit": "a" * 40, "local_path": str(source)}]})
        self.save("SOURCE_INVENTORY.json", {"applicability": "applicable", "reason": "Read-only test source", "files": [{"source_id": "foundation", "path": "reference.txt", "sha256": hashlib.sha256(b"source foundation").hexdigest()}]})
        p.load_pack(self.root)
        self.assertEqual((source / "reference.txt").read_bytes(), b"source foundation")

    def test_live_child_cannot_attest_final_runtime_audit_before_it_finishes(self):
        scope, tasks, state = self.active()
        p.reserve(scope, tasks, state, {"jobs": [self.job("PA-02")]})
        self.attach(scope, tasks, state, "PA-02")
        with self.assertRaisesRegex(p.Invalid, "live children"):
            p.mutate("runtime-audit", self.root, scope, tasks, state, {"no_untracked_processes": True, "evidence": "evidence/PA-01.json"}, None)

    def test_cli_repeated_pause_at_review_still_allows_explicit_owner_advance(self):
        scope, tasks, state = self.active()
        for tid in ("PA-02", "PA-03", "PA-04"):
            self.verify(tid)
        (self.root / "RUN_STATE.json").write_bytes(p.encode(state))
        self.assertEqual(self.cli("review").returncode, 0)
        for _ in range(2):
            result = self.cli("pause", instruction="Keep it paused while I review")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.cli("runtime-audit", {"no_untracked_processes": True, "evidence": "evidence/PA-01.json"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(self.cli("settlement").stdout)["safe_to_close"])
        original = (self.root / "RUN_STATE.json").read_bytes()
        self.assertEqual(self.cli("resume", instruction="Resume").returncode, 2)
        self.assertEqual((self.root / "RUN_STATE.json").read_bytes(), original)

        result = self.cli("advance", instruction="I reviewed it; proceed to full release")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = p.read(self.root / "RUN_STATE.json")
        self.assertEqual(after["phase"], "executing")
        self.assertEqual(after["delivery_stage"], "full_release")
        self.assertEqual(after["review_status"], "reviewed")
        self.assertIsNone(after["preflight"])
        self.assertFalse(after["schedule"]["enabled"])

    def test_cli_advance_recovers_existing_paused_awaiting_review_state(self):
        scope, tasks, state = self.active()
        for tid in ("PA-02", "PA-03", "PA-04"):
            self.verify(tid)
        state.update(stop_requested=True, phase="paused", review_status="awaiting_review")
        (self.root / "RUN_STATE.json").write_bytes(p.encode(state))
        self.assertEqual(self.cli("advance").returncode, 2)
        result = self.cli("advance", instruction="Proceed after my review")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_pause_preserves_completed_release_and_cannot_resume(self):
        scope, tasks, state = self.active()
        for tid in ("PA-02", "PA-03", "PA-04", "PA-05"):
            self.verify(tid)
        features = p.read(self.plan / "FEATURES.json")
        features["features"][0].update(status="verified", evidence=["evidence/PA-05.json"])
        self.save("FEATURES.json", features)
        scope, tasks, _, _ = p.load_pack(self.root)
        state.update(delivery_stage="full_release", review_status="reviewed")
        p.mutate("finish", self.root, scope, tasks, state, {}, None)
        (self.root / "RUN_STATE.json").write_bytes(p.encode(state))
        for _ in range(2):
            self.assertEqual(self.cli("pause", instruction="Leave the completed project stopped").returncode, 0)
        after = p.read(self.root / "RUN_STATE.json")
        self.assertEqual(after["phase"], "completed")
        original = (self.root / "RUN_STATE.json").read_bytes()
        self.assertEqual(self.cli("resume", instruction="Resume").returncode, 2)
        self.assertEqual((self.root / "RUN_STATE.json").read_bytes(), original)

        # Older helpers may already have rewritten completed -> paused.
        # Full task verification must still prevent re-entering execution.
        after["phase"] = "paused"
        (self.root / "RUN_STATE.json").write_bytes(p.encode(after))
        original = (self.root / "RUN_STATE.json").read_bytes()
        self.assertEqual(self.cli("resume", instruction="Resume this older checkpoint").returncode, 2)
        self.assertEqual((self.root / "RUN_STATE.json").read_bytes(), original)

    def test_multiple_source_roots_can_inventory_the_same_relative_filename(self):
        self.populated()
        sources, rows, originals = [], [], []
        for source_id in ("primary", "backup"):
            source = self.root.parent / source_id
            source.mkdir()
            payload = (source_id + " read-only foundation").encode()
            target = source / "README.md"
            target.write_bytes(payload)
            originals.append((target, payload))
            sources.append({"id": source_id, "kind": "git", "location": "https://example.invalid/" + source_id, "commit": "a" * 40, "local_path": str(source)})
            rows.append({"source_id": source_id, "path": "README.md", "sha256": hashlib.sha256(payload).hexdigest()})
        # A portable snapshot has its own namespace, separate from both sources.
        (self.plan / "README.md").write_bytes(b"portable snapshot")
        rows.append({"path": "README.md", "sha256": hashlib.sha256(b"portable snapshot").hexdigest()})
        self.save("SOURCES.lock.json", {"sources": sources})
        self.save("SOURCE_INVENTORY.json", {"applicability": "applicable", "reason": "Two pinned foundations plus one portable snapshot", "files": rows})
        result = self.cli("validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for target, payload in originals:
            self.assertEqual(target.read_bytes(), payload)
        rows.append(dict(rows[0]))
        self.save("SOURCE_INVENTORY.json", {"applicability": "applicable", "reason": "Duplicate within the same foundation", "files": rows})
        result = self.cli("validate")
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate SOURCE_INVENTORY.json", result.stdout)

    def test_standalone_validator_rejects_missing_required_tool_lock_entries(self):
        self.populated()
        original = p.read(self.plan / "TOOLS.lock.json")
        scope = p.read(self.plan / "SCOPE.json")
        for status in ("draft", "approved"):
            scope["status"] = status
            self.save("SCOPE.json", scope)
            for omitted in ("tools/replan.py", "tools/pack_contract.py", "all"):
                with self.subTest(status=status, omitted=omitted):
                    changed = copy.deepcopy(original)
                    changed["files"] = [] if omitted == "all" else [r for r in changed["files"] if r["path"] != omitted]
                    self.save("TOOLS.lock.json", changed)
                    result = subprocess.run([sys.executable, "-B", str(self.plan / "validate-plan.py")], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("Required helper lock coverage", result.stdout)

    def test_standalone_validator_rejects_changed_unlisted_helper_module(self):
        self.populated()
        doc = p.read(self.plan / "TOOLS.lock.json")
        doc["files"] = [r for r in doc["files"] if r["path"] != "tools/pack_contract.py"]
        self.save("TOOLS.lock.json", doc)
        module = self.plan / "tools/pack_contract.py"
        module.write_bytes(module.read_bytes() + b"\n# Independent review reproduction\n")
        result = subprocess.run([sys.executable, "-B", str(self.plan / "validate-plan.py")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Required helper lock coverage", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
