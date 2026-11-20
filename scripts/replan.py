"""RePlan local planning/state helper. Python 3.11+, standard library only.

No harness, network, agent, schedule, Git or VM calls. Receipts are caller
attestations; the agent must obtain them from the actual harness.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_contract as contracts


class Invalid(ValueError):
    pass


TASK = re.compile(r"PA-[0-9]{2,}(?:\.[0-9]+)?\Z")
FEATURE = re.compile(r"FA-[0-9]{2,}\Z")
STATUSES = {"planned", "in_progress", "implemented", "verified", "blocked"}
KINDS = {"research", "planning", "implementation", "review", "test", "documentation", "delivery"}
TERMINAL = {"completed", "failed", "cancelled", "interrupted", "not_created"}


def require(condition, message):
    if not condition:
        raise Invalid(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def now():
    return datetime.now(timezone.utc).isoformat()


def plain(path):
    path = Path(path).absolute()
    for p in [path, *path.parents]:
        require(not p.is_symlink() and not (hasattr(p, "is_junction") and p.is_junction()),
                f"Linked coordinator path is unsupported: {p}")
    return path


def relative(value):
    require(text(value) and not re.search(r'[<>:"\\|?*\x00-\x1f]', value),
            f"Expected literal relative forward-slash path: {value}")
    parts = value.split("/")
    require(not value.startswith("/") and all(p not in {"", ".", ".."} for p in parts),
            f"Unsafe relative path: {value}")
    # Win32 strips trailing dots/spaces and interprets DOS devices, even with
    # extensions. Reject these spellings rather than comparing alias strings.
    # Apply the portable restriction on every host so a plan cannot change
    # ownership meaning when moved between operating systems.
    for part in parts:
        require(not part.endswith((".", " ")), f"Windows-aliased path component: {part}")
        require(not re.match(r"(?i)^(?:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³]|CONIN\$|CONOUT\$)(?:\.|$)", part),
                f"Reserved Windows device component: {part}")
    return PurePosixPath(value)


def inside(root, value):
    return plain(root / relative(value))


def pairs(items):
    result, seen = {}, set()
    for key, value in items:
        require(key.casefold() not in seen, f"Duplicate JSON key: {key}")
        seen.add(key.casefold())
        result[key] = value
    return result


def read(path):
    raw = plain(path).read_bytes()
    require(len(raw) <= 4 * 1024 * 1024, "JSON exceeds 4 MiB")
    data = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(Invalid(f"Invalid JSON number: {x}")))
    require(isinstance(data, dict), f"Expected JSON object: {path}")
    return data


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


@contextmanager
def lease(workspace):
    root = plain(workspace)
    require(root.is_dir(), "Workspace must exist")
    local = plain(root / ".replan-local")
    local.mkdir(exist_ok=True)
    lock = plain(local / "coordinator.lock")
    # Never unlink the lock; otherwise two callers could lock different inodes.
    with lock.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            if lock.stat().st_size == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise Invalid("Lease busy; yield without deleting the lock") from exc
        else:
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise Invalid("Lease busy; yield without deleting the lock") from exc
        try:
            yield root
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def atomic(path, value, expected):
    path = plain(path)
    payload = encode(value)
    require(path.read_bytes() == expected, "State changed outside the lease; reconcile")
    fd, tmp = tempfile.mkstemp(prefix=".replan-state-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        require(path.read_bytes() == expected, "State changed outside the lease; reconcile")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


DOCS = {
    "START_HERE.md": "Owner decisions and entrypoint\n\nRead KICKOFF.md, SCOPE.json, TASKS.json, FEATURES.json, HANDOFF.md and workspace-root RUN_STATE.json first.\nThe meeting prepares only; execution belongs in the separately launched, designated supervisor for this pack's purpose. Discussing autonomy is not execution or launch authorization. Record actual build/test/validate commands here. Resume the bound supervisor rather than launching a replacement.\n",
    "KICKOFF.md": "Meeting to supervisor handoff\n\nNot launched. This draft does not authorize execution.\n\n## Purpose and workspace\n\nRecord the bounded purpose, absolute integration workspace, pack/state paths, deliverables, read-only inputs and exclusions.\n\n## Owner instructions\n\nRecord actual scope authorization, separate-thread launch instruction, source meeting reference, review stop, selected profile and worker budget. Preparation alone grants neither launch nor execution.\n\n## Initial supervisor prompt\n\nWrite a self-contained prompt directing the separate supervisor to read these files, adopt existing state, verify purpose/workspace, observe and bind its actual identity, qualify and execute only authorized work. Do not launch another supervisor or automatically start later phases.\n\n## Launch record\n\nAfter an authorized launch, record the returned supervisor link and actual identifiers. Reconcile uncertain outcomes before retrying. The meeting must never bind itself as supervisor.\n",
    "PLAN.md": "Delivery strategy\n\nDefine dependency tracks, the first real user-visible slice, intermediate review and full release. Research tasks must unlock named implementation work.\n",
    "ENGINEERING.md": "Engineering contracts\n\nRecord actual technology, interfaces, authority, persistence, failure, security, compatibility, native tests and numeric workload budgets where relevant.\n",
    "FRONTEND.md": "User journeys and design\n\nRecord project-specific journeys, approved assets and hashes, accessibility, narrow views, real loading/error/offline behavior and validation.\n",
    "RUNNER.md": "Runner qualification\n\nRecord actual harness/profile, project/supervisor identity, owned runtime targets and native probes. Keep this machine awake and the harness running; no PC-off execution is promised.\n",
    "AUTONOMY.md": "Autonomous execution\n\nOne supervisor and at most three children, disjoint owned files/resources, committed briefs, exact-candidate proof, completion wakeups and one tested 30-minute continuation. Reserve before external calls. Never poll live children or expire uncertain claims. Stop on owner pause or first review.\n",
    "HANDOFF.md": "Current checkpoint\n\nDraft pack created; no execution, workers or schedule started. Populate scope and backlog from the owner discussion before authorization/preflight. Record commits, results, contracts, workers, blockers and next work here at every boundary.\n",
    "AGENTS.fragment.md": "Project instruction fragment\n\nRead replan/START_HERE.md, KICKOFF.md, SCOPE.json, TASKS.json, FEATURES.json, ENGINEERING.md, FRONTEND.md, RUNNER.md, AUTONOMY.md, HANDOFF.md and workspace-root RUN_STATE.json. Preserve approved scope and stop state. The meeting prepares files only and must refuse execution in that thread; launch a separate supervisor only on owner request. Only the designated supervisor may execute this pack's intended purpose with up to three disjoint T3-owned workers. Resume its existing binding; do not automatically launch later phases. Merge this into existing project instructions; do not overwrite them.\n",
}


def initialize(root, name):
    root = plain(root)
    require(not (root / "powerplan").exists(),
            "Legacy powerplan pack: use its pinned powerplan/tools/powerplan.py; do not reinitialize or rename it")
    root.mkdir(parents=True, exist_ok=True)
    with lease(root):
        require(not (root / "replan").exists() and not (root / "RUN_STATE.json").exists(),
                "Existing pack/state: adopt it, never overwrite it")
        plan = root / "replan"
        plan.mkdir()
        for folder in ("evidence", "briefs", "contracts"):
            (plan / folder).mkdir()
        scope = {"format_version": 1, "contract_version": 2, "project_id": str(uuid.uuid4()), "name": name,
                 "status": "draft", "outcomes": [], "exclusions": [], "constraints": [],
                 "authorization": {"allowed": [], "requires_separate_authorization": []},
                 "preflight_task": None, "first_review_task": None, "full_release_task": None}
        files = {"SCOPE.json": scope, "FEATURES.json": {"features": []},
                 "TASKS.json": {"tasks": []}, "SOURCES.lock.json": {"sources": []},
                 "DEPENDENCIES.json": {"decisions": []}}
        for file, data in files.items():
            (plan / file).write_bytes(encode(data))
        for file, body in DOCS.items():
            (plan / file).write_text("# " + name + " — " + body, encoding="utf-8")
        contracts.write_resources(plan, name, encode)
        # New projects are usable without silently overwriting existing owner instructions.
        if not (root / "AGENTS.md").exists():
            (root / "AGENTS.md").write_text((plan / "AGENTS.fragment.md").read_text(encoding="utf-8"), encoding="utf-8")
        if not (root / ".gitignore").exists():
            (root / ".gitignore").write_text(".replan-local/\n__pycache__/\n*.pyc\n", encoding="utf-8")
        state = {"format_version": 1, "project_id": scope["project_id"], "workspace": str(root.resolve()),
                 "revision": 0, "phase": "draft", "owner_start_authorized": False,
                 "stop_requested": True, "review_status": "not_ready", "binding": None,
                 "preflight": None, "max_active_children": 3, "jobs": [],
                 "delivery_stage": "first_review", "runtime": [], "runtime_audit": None,
                 "attempts": [], "schedule": {"id": None, "enabled": False, "intent": None}, "events": []}
        (root / "RUN_STATE.json").write_bytes(encode(state))
    return {"created": str(plan), "execution_started": False}


def terminal(job):
    return job.get("status") in TERMINAL and text(job.get("terminal_evidence"))


def live(state):
    return [j for j in state["jobs"] if not terminal(j)]


def validate_state(state, scope, root):
    require(state.get("format_version") == 1, "Unsupported state format")
    require(state.get("project_id") == scope["project_id"], "Project identity mismatch")
    require(state.get("workspace") == str(root.resolve()), "Use the bound integration workspace, not a worktree copy")
    require(type(state.get("revision")) is int and state["revision"] >= 0, "Invalid revision")
    for field in ("owner_start_authorized", "stop_requested"):
        require(type(state.get(field)) is bool, f"Invalid {field}")
    require(state.get("phase") in {"draft", "executing", "paused", "review", "completed"}, "Invalid phase")
    require(state.get("review_status") in {"not_ready", "awaiting_review", "reviewed"}, "Invalid review boundary")
    require(type(state.get("max_active_children")) is int and 1 <= state["max_active_children"] <= 3, "Invalid child budget")
    require(isinstance(state.get("jobs"), list), "Invalid jobs")
    seen, requests = set(), set()
    for job in state["jobs"]:
        require(isinstance(job, dict) and text(job.get("key")) and text(job.get("client_request_id")), "Invalid job identity")
        require(job["key"] not in seen and job["client_request_id"] not in requests, "Duplicate work identity")
        seen.add(job["key"])
        requests.add(job["client_request_id"])
        require(TASK.fullmatch(job.get("pa_task", "")), "Invalid job PA task")
        require(isinstance(job.get("owned_paths"), list) and job["owned_paths"], "Missing owned paths")
        for path in job["owned_paths"]:
            relative(path)
        require(isinstance(job.get("resources"), list) and all(text(r) for r in job["resources"]), "Invalid job resources")
    require(len(live(state)) <= state["max_active_children"], "Child budget exceeded")
    schedule = state.get("schedule")
    require(isinstance(schedule, dict) and type(schedule.get("enabled")) is bool, "Invalid schedule")
    require(not schedule["enabled"] or text(schedule.get("id")), "Enabled schedule needs actual ID")
    require(isinstance(state.get("events"), list), "Invalid event history")
    require(state.get("delivery_stage", "first_review") in {"first_review", "full_release"}, "Invalid delivery stage")
    require(isinstance(state.get("runtime", []), list) and isinstance(state.get("attempts", []), list), "Invalid runtime/attempt records")


def evidence(plan, task, milestone_id=None):
    covered = set()
    candidates = set()
    require(task.get("evidence"), f"Verified task has no evidence: {task['id']}")
    for name in task["evidence"]:
        item = read(inside(plan, name))
        require(item.get("task_id") == task["id"], "Evidence task mismatch")
        if milestone_id:
            require(item.get("milestone_id") == milestone_id and item.get("full_task_verified") is False,
                    "Milestone evidence must identify bounded scope and preserve full task")
        candidate = item.get("candidate_commit", "")
        digest = item.get("candidate_sha256", "")
        require(re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", candidate) or re.fullmatch(r"[a-f0-9]{64}", digest), "Missing exact candidate")
        candidates.add(candidate or digest)
        require(isinstance(item.get("environment"), dict) and item["environment"], "Missing environment")
        require(text(item.get("review")) and isinstance(item.get("limitations"), list), "Missing review/limitations")
        require(isinstance(item.get("engineering_review"), dict) and
                all(text(item["engineering_review"].get(k)) for k in ("design", "simplification", "language_review", "dependencies", "performance", "ux")), "Missing engineering review")
        require(isinstance(item.get("checks"), list) and item["checks"], "Missing checks")
        for check in item["checks"]:
            require(check.get("result") == "passed" and text(check.get("command")), "Verification includes non-passing check")
            require(inside(plan, check.get("artifact")).is_file(), "Missing check artifact")
            covered.add(check.get("acceptance_item"))
    require(len(candidates) == 1, "Do not merge verification from different candidates")
    require(set(task["acceptance"]) <= covered, f"Incomplete acceptance evidence: {task['id']}")


def dependency_verified(tasks, task, dependency):
    milestone = task.get("dependency_milestones", {}).get(dependency)
    if milestone:
        return tasks[dependency].get("milestones", {}).get(milestone, {}).get("status") == "verified"
    return tasks[dependency]["status"] == "verified"


def load_pack(root):
    plan = root / "replan"
    scope = read(plan / "SCOPE.json")
    contracts.validate_resources(root, scope, read, inside, require, text)
    tasks, features = read(plan / "TASKS.json").get("tasks"), read(plan / "FEATURES.json").get("features")
    require(scope.get("format_version") == 1 and text(scope.get("project_id")) and text(scope.get("name")), "Invalid scope identity")
    require(scope.get("status") in {"draft", "approved"}, "Invalid scope status")
    require(isinstance(tasks, list) and isinstance(features, list), "Invalid task/feature arrays")
    tm, fm = {}, {}
    for rows, mapping, pattern in ((tasks, tm, TASK), (features, fm, FEATURE)):
        for row in rows:
            require(isinstance(row, dict) and pattern.fullmatch(row.get("id", "")), "Invalid row ID")
            require(row["id"] not in mapping, f"Duplicate ID: {row['id']}")
            require(text(row.get("title")) and row.get("status") in STATUSES, "Invalid title/status")
            require(isinstance(row.get("acceptance"), list) and row["acceptance"] and all(text(x) for x in row["acceptance"]), "Missing acceptance")
            require(len(set(row["acceptance"])) == len(row["acceptance"]), "Duplicate acceptance item")
            require(isinstance(row.get("evidence"), list), "Missing evidence array")
            mapping[row["id"]] = row
    for task in tasks:
        require(task.get("kind") in KINDS and text(task.get("work")), "Missing task kind/work")
        require(isinstance(task.get("depends_on"), list) and len(set(task["depends_on"])) == len(task["depends_on"]), "Invalid dependencies")
        require(all(dep in tm for dep in task["depends_on"]), "Unknown dependency")
        require(isinstance(task.get("feature_ids"), list) and task["feature_ids"] and all(f in fm for f in task["feature_ids"]), "Unknown/missing task features")
        require(isinstance(task.get("owned_paths"), list) and task["owned_paths"], "Missing task ownership")
        for path in task["owned_paths"]:
            relative(path)
        require(isinstance(task.get("resources"), list) and all(text(x) for x in task["resources"]), "Invalid resources")
        require(isinstance(task.get("milestones", {}), dict) and isinstance(task.get("dependency_milestones", {}), dict), "Invalid milestone declarations")
        for dep, mid in task.get("dependency_milestones", {}).items():
            require(dep in task["depends_on"] and text(mid) and mid in tm[dep].get("milestones", {}), "Unknown qualified dependency")
        for mid, milestone in task.get("milestones", {}).items():
            require(text(mid) and isinstance(milestone, dict) and milestone.get("status") in STATUSES and
                    isinstance(milestone.get("acceptance"), list) and milestone["acceptance"] and all(text(x) for x in milestone["acceptance"]), "Invalid milestone")
            if milestone["status"] == "verified":
                evidence(plan, {"id": task["id"], **milestone}, mid)
        if task["status"] in {"in_progress", "implemented", "verified"} or any(m["status"] == "verified" for m in task.get("milestones", {}).values()):
            require(all(dependency_verified(tm, task, d) for d in task["depends_on"]), f"Unverified dependency: {task['id']}")
        if task["status"] == "verified":
            evidence(plan, task)
    visiting, visited = set(), set()

    def visit(key):
        require(key not in visiting, "Dependency cycle")
        if key not in visited:
            visiting.add(key)
            for dep in tm[key]["depends_on"]:
                visit(dep)
            visiting.remove(key)
            visited.add(key)
    for key in tm:
        visit(key)
    for feature in features:
        require(isinstance(feature.get("task_ids"), list) and feature["task_ids"] and all(t in tm for t in feature["task_ids"]), "Unknown/missing feature owners")
        for tid in feature["task_ids"]:
            require(feature["id"] in tm[tid]["feature_ids"], "Nonreciprocal feature ownership")
        if scope.get("contract_version", 1) >= 2 and scope["status"] == "approved":
            mapping = feature.get("acceptance_map")
            require(isinstance(mapping, dict) and set(mapping) == set(feature["acceptance"]), "Feature acceptance needs explicit task/leaf mapping")
            for entries in mapping.values():
                require(isinstance(entries, list) and entries, "Empty feature acceptance mapping")
                for entry in entries:
                    require(isinstance(entry, dict) and entry.get("task_id") in feature["task_ids"] and
                            entry.get("acceptance_item") in tm[entry["task_id"]]["acceptance"], "Unknown feature leaf acceptance")
        if feature["status"] == "verified":
            require(all(tm[t]["status"] == "verified" for t in feature["task_ids"]) and feature["evidence"], "Incomplete verified feature")
            for name in feature["evidence"]:
                require(inside(plan, name).is_file(), "Missing feature evidence")
    for task in tasks:
        require(all(task["id"] in fm[f]["task_ids"] for f in task["feature_ids"]), "Nonreciprocal task ownership")
    for key in ("outcomes", "exclusions", "constraints"):
        require(isinstance(scope.get(key), list) and all(text(x) for x in scope[key]), f"Invalid scope {key}")
    auth = scope.get("authorization")
    require(isinstance(auth, dict) and all(isinstance(auth.get(k), list) and all(text(x) for x in auth[k]) for k in ("allowed", "requires_separate_authorization")), "Missing authorization boundaries")
    if scope["status"] == "approved":
        require(scope["outcomes"] and tasks and features and auth["allowed"], "Approved scope is empty")
        boundaries = [scope.get(k) for k in ("preflight_task", "first_review_task", "full_release_task")]
        require(all(x in tm for x in boundaries) and len(set(boundaries)) == 3, "Missing/distinct preflight/review/release tasks")
        full, pending = set(), [scope["full_release_task"]]
        while pending:
            key = pending.pop()
            if key not in full:
                full.add(key)
                pending.extend(tm[key]["depends_on"])
        require(set(tm) <= full, "Full release must retain every task (including review and qualification)")
        if tm[scope["full_release_task"]]["status"] == "verified":
            require(all(t["status"] == "verified" for t in tasks), "Full release cannot substitute partial milestones for full tasks")
    state = read(root / "RUN_STATE.json")
    validate_state(state, scope, root)
    return scope, tm, fm, state


def decision(scope, tasks, state, scheduled=False):
    if state["stop_requested"] or not state["owner_start_authorized"] or state["phase"] in {"draft", "paused", "review", "completed"} or state["review_status"] == "awaiting_review":
        return {"decision": "stop", "reason": "Owner stop, missing authorization or review boundary"}
    if scope["status"] != "approved" or not state["binding"]:
        return {"decision": "yield", "reason": "Approved scope and actual binding required"}
    if state.get("delivery_stage", "first_review") == "first_review" and tasks.get(scope["first_review_task"], {}).get("status") == "verified":
        return {"decision": "stop", "reason": "First-review task verified; settle review stop"}
    if tasks.get(scope["full_release_task"], {}).get("status") == "verified":
        return {"decision": "stop", "reason": "Full release verified; settle completion"}
    jobs = live(state)
    if any(j["status"] != "running" for j in jobs) or state["schedule"]["intent"]:
        return {"decision": "yield", "reason": "Unknown external effect/reservation; reconcile without replay"}
    if scheduled and (jobs or not state["schedule"]["enabled"]):
        return {"decision": "yield", "reason": "Scheduled continuation yields to children or disabled schedule"}
    if not state["preflight"]:
        return {"decision": "bootstrap", "reason": "Only runner preflight and its research/planning/test prerequisites may be reserved", "free_slots": state["max_active_children"] - len(jobs)}
    return {"decision": "ready", "free_slots": state["max_active_children"] - len(jobs)}


def ready_tasks(tasks, state):
    claimed = {j["pa_task"] for j in live(state)}
    latest = {(a["pa_task"], a["blocker"]): a for a in state.get("attempts", [])}
    exhausted = {a["pa_task"] for a in latest.values() if a.get("result") == "failed" and a.get("failure_count", 0) >= 3}
    return [t["id"] for t in tasks.values() if t["status"] == "planned" and t["id"] not in claimed
            and t["id"] not in exhausted and all(dependency_verified(tasks, t, d) for d in t["depends_on"])]


def overlap(a, b):
    a, b = a.casefold(), b.casefold()
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def reserve(scope, tasks, state, data):
    current = decision(scope, tasks, state)["decision"]
    require(current in {"ready", "bootstrap"}, "Run is not ready")
    batch = data.get("jobs")
    require(isinstance(batch, list) and batch, "Nonempty jobs batch required")
    require(len(batch) + len(live(state)) <= state["max_active_children"], "Child budget exceeded")
    active = list(live(state))
    keys = {j["key"] for j in state["jobs"]}
    requests = {j["client_request_id"] for j in state["jobs"]}
    eligible = set(ready_tasks(tasks, state))
    if current == "bootstrap":
        ancestors, pending = set(), [scope["preflight_task"]]
        while pending:
            tid = pending.pop()
            if tid not in ancestors:
                ancestors.add(tid)
                pending.extend(tasks[tid]["depends_on"])
        eligible &= {tid for tid in ancestors if tasks[tid]["kind"] in {"research", "planning", "test"}}
    for job in batch:
        require(text(job.get("key")) and job["key"] not in keys, "Reused work key")
        require(text(job.get("client_request_id")) and job["client_request_id"] not in requests, "Reused request ID")
        require(job.get("pa_task") in eligible, "Task not dependency-ready or already claimed")
        task = tasks[job["pa_task"]]
        require(job.get("owned_paths") == task["owned_paths"] and job.get("resources") == task["resources"], "Reservation must match declared task ownership/resources")
        require(re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", job.get("base_commit", "")), "Full base commit required")
        for other in active:
            require(other["pa_task"] != job["pa_task"], "Duplicate task claim")
            require(not any(overlap(a, b) for a in job["owned_paths"] for b in other["owned_paths"]), "Overlapping live file ownership")
            require(not {r.casefold() for r in job["resources"]} & {r.casefold() for r in other["resources"]}, "Overlapping runtime resource")
        record = {k: job[k] for k in ("key", "client_request_id", "pa_task", "owned_paths", "resources", "base_commit")}
        record.update(status="reserved", reserved_utc=now())
        state["jobs"].append(record)
        state["runtime_audit"] = None
        active.append(record)
        keys.add(record["key"])
        requests.add(record["client_request_id"])


def mutate(command, root, scope, tasks, state, data, instruction):
    schedule = state["schedule"]
    if command == "bind":
        require(data.get("project_id") == scope["project_id"] and text(data.get("supervisor_thread_id")), "Binding identity mismatch")
        require(isinstance(data.get("profile"), dict) and all(text(data["profile"].get(k)) for k in ("provider", "model")) and isinstance(data["profile"].get("options"), dict), "Actual profile observation required")
        require(state["binding"] is None or state["binding"] == data, "Existing supervisor/profile binding differs; reconcile explicitly")
        state["binding"] = data
    elif command == "bind-t3":
        project, thread = contracts.unwrap(data["project"]), contracts.unwrap(data["thread"])
        require(text(project.get("id")) and plain(project["workspaceRoot"]).resolve() == root.resolve(), "Actual T3 project workspace mismatch")
        actual = {"project_id": scope["project_id"], "harness_project_id": project["id"], "harness": "t3",
                  "supervisor_thread_id": thread["threadId"], "profile": contracts.profile(thread["modelSelection"], thread["runtimeMode"])}
        require(all(text(actual["profile"].get(k)) for k in ("provider", "model", "runtime_mode")), "Incomplete actual T3 profile")
        require(state["binding"] is None or state["binding"] == actual, "Existing actual T3 binding/profile differs")
        state["binding"] = actual
    elif command == "authorize":
        require(text(instruction) and scope["status"] == "approved" and state["binding"], "Owner instruction, approved scope and binding required")
        require(state["phase"] in {"draft", "paused"} and not state["owner_start_authorized"] and not state["jobs"] and not schedule["id"] and not schedule["intent"], "Use resume for an existing run")
        state.update(owner_start_authorized=True, stop_requested=False, phase="executing")
    elif command in {"preflight", "runner-ready"}:
        if command == "preflight":
            require(tasks[scope["preflight_task"]]["status"] == "verified", "Preflight task is not verified")
        else:
            require(scope.get("contract_version", 1) >= 2 and
                    tasks[scope["preflight_task"]].get("milestones", {}).get("operational", {}).get("status") == "verified",
                    "Verified operational runner milestone required")
        require(text(data.get("evidence")) and inside(root / "replan", data["evidence"]).is_file(), "Actual harness/runtime preflight evidence required")
        require(state["binding"] is not None, "Observe and bind the actual supervisor first")
        state["preflight"] = data
        state["preflight"]["stage"] = "qualified" if command == "preflight" else "operational"
    elif command in {"pause", "review"}:
        require(text(instruction) if command == "pause" else scope.get("first_review_task") in tasks and tasks[scope["first_review_task"]]["status"] == "verified", "Owner pause instruction or verified review milestone required")
        state["stop_requested"] = True
        if command == "pause":
            # Pause is an owner stop intent, not a rollback of delivery stage.
            # Repeated pauses must not destroy review/completion boundaries.
            if state["phase"] not in {"review", "completed"}:
                state["phase"] = "paused"
        else:
            require(state["phase"] != "completed" and state.get("delivery_stage", "first_review") == "first_review", "Cannot reopen a completed or advanced review boundary")
            state["phase"] = "review"
        state["runtime_audit"] = None
        if command == "review":
            state["review_status"] = "awaiting_review"
    elif command == "resume":
        require(text(instruction) and state["owner_start_authorized"], "Explicit owner resume instruction required")
        require(state["phase"] == "paused" and state["stop_requested"] and state["review_status"] != "awaiting_review", "Cannot reopen a review/draft boundary")
        require(tasks.get(scope.get("full_release_task"), {}).get("status") != "verified", "Completed release cannot be resumed")
        require(not schedule["enabled"] and not schedule["intent"] and not live(state), "Settle schedule, children and reservations before resume")
        require(not any(r.get("status") != "settled" for r in state.get("runtime", [])), "Reconcile runtime before resume")
        state.update(stop_requested=False, phase="executing", preflight=None, runtime_audit=None)
    elif command == "advance":
        # Also accept the paused+awaiting_review state produced by older v2
        # helpers, while ordinary resume still cannot grant this phase change.
        require(text(instruction) and state["owner_start_authorized"] and state["phase"] in {"review", "paused"} and state["review_status"] == "awaiting_review" and state.get("delivery_stage", "first_review") == "first_review", "Explicit owner instruction at first review required")
        require(not schedule["enabled"] and not schedule["intent"] and not live(state), "Settle review schedule/work before advancing")
        require(not any(r.get("status") != "settled" for r in state.get("runtime", [])), "Reconcile runtime before advancing")
        state.update(stop_requested=False, phase="executing", review_status="reviewed", delivery_stage="full_release", preflight=None, runtime_audit=None)
    elif command == "finish":
        require(state.get("delivery_stage") == "full_release" and state["review_status"] == "reviewed", "Explicit owner advance after review required before final release")
        require(tasks[scope["full_release_task"]]["status"] == "verified" and all(t["status"] == "verified" for t in tasks.values()), "Every full task must be verified")
        features = read(root / "replan/FEATURES.json")["features"]
        require(all(f["status"] == "verified" for f in features), "Full feature acceptance remains unverified")
        state.update(stop_requested=True, phase="completed", runtime_audit=None)
    elif command == "reserve":
        reserve(scope, tasks, state, data)
    elif command in {"attach", "terminal", "resolve-reservation"}:
        found = [j for j in state["jobs"] if j["key"] == data.get("key")]
        require(len(found) == 1, "Unknown reservation")
        job = found[0]
        require(not terminal(job), "Terminal history is immutable")
        if command == "attach":
            require(job["status"] == "reserved", "Reservation already attached")
            require(all(text(data.get(k)) for k in ("task_id", "child_thread_id", "run_id", "link")), "Actual task/thread/run/link receipt required")
            require(isinstance(data.get("profile"), dict) and data["profile"] == state["binding"]["profile"], "Actual child profile differs from selected supervisor profile")
            job.update({k: data[k] for k in ("task_id", "child_thread_id", "run_id", "link", "profile")})
            job["status"] = "running"
            state["runtime_audit"] = None
        else:
            require(text(data.get("terminal_evidence")), "Actual terminal evidence required")
            expected = {"not_created"} if command == "resolve-reservation" else TERMINAL - {"not_created"}
            require(data.get("status") in expected, "Invalid terminal outcome")
            require(job["status"] == ("reserved" if command == "resolve-reservation" else "running"), "Reconcile the actual delegation receipt first")
            job.update(status=data["status"], terminal_evidence=data["terminal_evidence"], terminal_utc=now())
    elif command == "schedule-intent":
        require(decision(scope, tasks, state)["decision"] == "ready", "Run is not ready")
        require(not schedule["id"] and not schedule["intent"] and text(data.get("client_request_id")), "Existing or unresolved schedule; do not create another")
        schedule["intent"] = data
    elif command == "schedule-resolve":
        require(schedule["intent"] and schedule["id"] is None and text(data.get("evidence")) and data.get("status") == "not_created", "Confirmed no schedule created evidence required")
        schedule["resolved_intents"] = schedule.get("resolved_intents", []) + [{"intent": schedule["intent"], **data}]
        schedule["intent"] = None
    elif command == "schedule-record":
        require(text(data.get("id")) and type(data.get("enabled")) is bool and text(data.get("evidence")), "Actual schedule receipt required")
        require(state["binding"] and data.get("bound_thread_id") == state["binding"]["supervisor_thread_id"], "Schedule must bind to this supervisor")
        require(data.get("interval_ms") == 1800000, "Expected single 30-minute interval")
        require((schedule["id"] is None and schedule["intent"]) or schedule["id"] == data["id"], "No intent or different existing schedule ID")
        if data["enabled"]:
            require(not state["stop_requested"] and state["review_status"] != "awaiting_review" and state["preflight"], "Cannot enable continuation while stopped or unqualified")
        schedule.update(data)
        schedule["intent"] = None
    elif command == "runtime-record":
        require(text(data.get("key")) and data.get("status") in {"running", "unknown", "settled"} and text(data.get("evidence")), "Actual scoped runtime identity/status/evidence required")
        runtime = state.setdefault("runtime", [])
        existing = next((r for r in runtime if r["key"] == data["key"]), None)
        if existing is None:
            runtime.append(dict(data))
        else:
            existing.update(data)
        state["runtime_audit"] = None
    elif command == "runtime-audit":
        require(data.get("no_untracked_processes") is True and text(data.get("evidence")) and inside(root / "replan", data["evidence"]).is_file(), "Actual complete runtime reconciliation artifact required")
        require(not live(state), "Settle live children/reservations before final runtime audit")
        require(not any(r.get("status") != "settled" for r in state.get("runtime", [])), "Known runtime still unresolved")
        state["runtime_audit"] = {**data, "recorded_utc": now()}
    elif command == "attempt":
        require(data.get("pa_task") in tasks and text(data.get("blocker")) and data.get("result") in {"failed", "resolved"} and text(data.get("diagnosis")), "Task/blocker/diagnosis/result required")
        attempts = state.setdefault("attempts", [])
        previous = [a for a in attempts if a["pa_task"] == data["pa_task"] and a["blocker"] == data["blocker"]]
        failures = previous[-1]["failure_count"] if previous else 0
        require(failures < 3 or data["result"] == "resolved", "Three failed attempts exhausted; continue independent work")
        if failures and data["result"] == "failed":
            require(text(data.get("changed_approach")), "Diagnosed changed approach required before retry")
        attempts.append({**data, "failure_count": failures + 1 if data["result"] == "failed" else 0, "recorded_utc": now()})
    elif command == "checkpoint":
        require(isinstance(data, dict) and data, "Checkpoint data required")
        state["checkpoint"] = {"recorded_utc": now(), "data": data}
    else:
        raise Invalid(f"Unknown mutation: {command}")
    event = {"command": command, "recorded_utc": now()}
    if instruction:
        event["owner_instruction"] = instruction
    state["events"].append(event)
    state["revision"] += 1
    validate_state(state, scope, root)


def settlement(state):
    blockers = []
    if not state["stop_requested"]:
        blockers.append("Project is not stopped")
    if state["schedule"]["enabled"] or state["schedule"]["intent"]:
        blockers.append("Schedule enabled or unresolved")
    if live(state):
        blockers.append("Children/reservations unresolved")
    if any(r.get("status") != "settled" for r in state.get("runtime", [])):
        blockers.append("Runtime resources unresolved")
    if not state.get("runtime_audit"):
        blockers.append("Fresh actual runtime audit required")
    return {"safe_to_close": not blockers, "blockers": blockers}


def progress(scope, tasks, features, state):
    """Read-only snapshot; stored job status is not a live harness observation."""
    guard = decision(scope, tasks, state)
    ready = ready_tasks(tasks, state)
    counts = {status: sum(t["status"] == status for t in tasks.values()) for status in sorted(STATUSES)}
    jobs = [{"task": j["pa_task"], "title": tasks.get(j["pa_task"], {}).get("title", j["pa_task"]),
             "status": j["status"], "link": j.get("link"), "key": j["key"]} for j in live(state)]
    latest_attempts = {(a["pa_task"], a["blocker"]): a for a in state.get("attempts", [])}
    retry_blockers = [{"id": a["pa_task"], "title": tasks.get(a["pa_task"], {}).get("title", a["pa_task"]),
                       "blocker": a["blocker"] + ": retry budget exhausted"} for a in latest_attempts.values()
                      if a.get("result") == "failed" and a.get("failure_count", 0) >= 3]
    return {"name": scope["name"], "snapshot_utc": now(), "source": "stored pack; not live monitoring",
            "revision": state["revision"], "last_event_utc": state["events"][-1].get("recorded_utc") if state["events"] else None,
            "phase": state["phase"], "delivery_stage": state.get("delivery_stage", "first_review"),
            "stop_requested": state["stop_requested"], "review_status": state["review_status"],
            "guard": guard, "task_counts": counts, "task_total": len(tasks),
            "feature_verified": sum(f["status"] == "verified" for f in features.values()), "feature_total": len(features),
            "jobs": jobs,
            "in_progress_tasks": [{"id": t["id"], "title": t["title"]} for t in tasks.values() if t["status"] == "in_progress"],
            "blocked_tasks": [{"id": t["id"], "title": t["title"], "blocker": t.get("blocker", "See HANDOFF.md")} for t in tasks.values() if t["status"] == "blocked"] + retry_blockers,
            "dependency_ready_tasks": ready,
            "schedule": dict(state["schedule"]), "settlement": settlement(state),
            "handoff": state.get("handoff"), "supervisor": state.get("binding"),
            "next_action": ("Await explicit owner phase decision" if state["review_status"] == "awaiting_review" else
                            "Remain stopped; inspect settlement and owner instructions" if guard["decision"] == "stop" else
                            guard.get("reason") or
                            ("Await completion notifications; worker budget is full" if guard.get("free_slots", 0) == 0 else
                             "Work eligible tasks within the guard and worker budget" if ready else
                             "Await completion notifications" if jobs else "Inspect remaining acceptance and blockers; no dependency-ready work"))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "validate", "ready", "guard", "progress", "bind", "bind-t3", "authorize", "preflight", "runner-ready", "pause", "resume", "advance", "finish", "review", "checkpoint", "reserve", "attach", "terminal", "resolve-reservation", "schedule-intent", "schedule-record", "schedule-resolve", "continuation", "runtime-record", "runtime-audit", "settlement", "attempt"])
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--name")
    parser.add_argument("--input", type=Path, help="JSON receipt/batch file; never put secrets here")
    parser.add_argument("--instruction", type=Path, help="File containing the actual owner instruction")
    parser.add_argument("--scheduled", action="store_true", help="Apply conservative scheduled-wake guard")
    parser.add_argument("--html", type=Path, help="Progress only: create a new HTML snapshot artifact")
    args = parser.parse_args(argv)
    try:
        require(args.html is None or args.command == "progress", "--html is only supported for progress")
        require(not (args.workspace / "powerplan").exists(),
                "Legacy powerplan pack: use its pinned powerplan/tools/powerplan.py; do not reinitialize or rename it")
        if args.command == "init":
            require(text(args.name), "Project name required")
            result = initialize(args.workspace, args.name)
        else:
            with lease(args.workspace) as root:
                raw = (root / "RUN_STATE.json").read_bytes()
                data = read(args.input) if args.input else {}
                # A malformed plan must never prevent the owner setting stop or
                # recording the actual disabled scheduler outcome.
                recovery_control = args.command == "pause" or (args.command == "schedule-record" and data.get("enabled") is False)
                if recovery_control:
                    scope = read(root / "replan/SCOPE.json")
                    state = read(root / "RUN_STATE.json")
                    validate_state(state, scope, root)
                    tasks, features = {}, {}
                else:
                    scope, tasks, features, state = load_pack(root)
                require((root / "RUN_STATE.json").read_bytes() == raw, "State changed during inspection; reconcile")
                if args.command == "validate":
                    result = {"valid": True, "scope": scope["status"], "tasks": len(tasks), "features": len(features)}
                elif args.command == "ready":
                    result = {"scope": scope["status"], "dependency_ready_tasks": ready_tasks(tasks, state), "guard": decision(scope, tasks, state)}
                elif args.command == "guard":
                    result = decision(scope, tasks, state, args.scheduled)
                elif args.command == "progress":
                    result = progress(scope, tasks, features, state)
                    if args.html:
                        # Exclusive creation prevents status output overwriting any
                        # existing source, plan, state, lock or evidence file.
                        with args.html.open("x", encoding="utf-8") as output:
                            output.write(contracts.render_progress(result))
                        result["html"] = str(args.html.resolve())
                elif args.command == "continuation":
                    result = {"prompt": contracts.render_prompt(root, state), "schedule_id": state["schedule"]["id"]}
                elif args.command == "settlement":
                    result = settlement(state)
                else:
                    instruction = args.instruction.read_text(encoding="utf-8").strip() if args.instruction else None
                    mutate(args.command, root, scope, tasks, state, data, instruction)
                    atomic(root / "RUN_STATE.json", state, raw)
                    result = {"recorded": args.command, "revision": state["revision"], "guard": decision(scope, tasks, state)}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (Invalid, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
