"""Portable execution-pack contracts; stdlib only, no external actions."""
from __future__ import annotations

import hashlib
from html import escape
import json
from pathlib import Path
import re


REQUIRED_TOOLS = ("tools/replan.py", "tools/pack_contract.py")


def render_progress(snapshot):
    """Self-contained, script-free snapshot. All pack text is untrusted HTML."""
    def e(value):
        return escape(str(value), quote=True)

    def rows(items, empty):
        return "<ul>" + "".join("<li>" + item + "</li>" for item in items) + "</ul>" if items else "<p class='muted'>" + e(empty) + "</p>"

    counts = snapshot["task_counts"]
    total, verified = snapshot["task_total"], counts["verified"]
    percent = round(verified / total * 100) if total else 0
    jobs = []
    for job in snapshot["jobs"]:
        label = e(job["task"]) + " · " + e(job["title"])
        link = job.get("link")
        if isinstance(link, str) and link.startswith(("https://", "http://")):
            label = '<a href="' + e(link) + '">' + label + '</a>'
        jobs.append(label + " <span class='badge'>" + ("recorded running" if job["status"] == "running" else "unresolved · " + e(job["status"])) + "</span>")
    tracked = {j["task"] for j in snapshot["jobs"]}
    jobs += [e(t["id"]) + " · " + e(t["title"]) + " <span class='badge'>in progress in register</span>" for t in snapshot["in_progress_tasks"] if t["id"] not in tracked]
    blockers = [e(t["id"]) + " · " + e(t["title"]) + ": " + e(t["blocker"]) for t in snapshot["blocked_tasks"]]
    blockers += [e(j["task"]) + ": unresolved external outcome" for j in snapshot["jobs"] if j["status"] != "running"]
    schedule = snapshot["schedule"]
    if schedule.get("intent"):
        blockers.append("Schedule creation outcome unresolved")
    guard = snapshot["guard"]
    eligible = ", ".join(snapshot["dependency_ready_tasks"]) or "None"
    status_counts = " · ".join(e(key.replace("_", " ")) + " " + str(counts[key]) for key in ("planned", "in_progress", "implemented", "verified", "blocked"))
    schedule_label = "enabled" if schedule["enabled"] else "disabled / none"
    schedule_label += " · " + str(schedule.get("id") or "no recorded ID")
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>RePlan progress</title>
<style>
:root{color-scheme:light dark;--foreground:light-dark(#172c28,#e2eee9);--muted:light-dark(#53665e,#a1b4ac);--card:light-dark(#f2f6f3,#15251f);--border:light-dark(#cad8ce,#344c40);--primary:light-dark(#216447,#8bd5a7);--radius:12px;--font-sans:system-ui,sans-serif}
body{font-family:var(--font-sans);color:var(--foreground);margin:0}h1{font-size:24px;margin:0 0 6px}h2{font-size:16px;margin:0 0 12px}p{margin:6px 0;line-height:1.5}.muted,small{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px}.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:16px}.wide{grid-column:1/-1}.badge{display:inline-block;font-size:12px;border:1px solid var(--border);border-radius:6px;padding:2px 6px;margin:3px 0}progress{width:100%;height:18px;accent-color:var(--primary)}ul{padding-left:20px;margin:0}li{margin:8px 0;overflow-wrap:anywhere}a{color:var(--primary)}.number{font-size:30px;font-weight:650}
</style></head><body>
''' + f'''<h1>{e(snapshot['name'])}</h1><p class="muted">Snapshot {e(snapshot['snapshot_utc'])} · stored state, not live monitoring</p>
<p><span class="badge">{e(snapshot['phase'])}</span> <span class="badge">{e(snapshot['delivery_stage'])}</span> <span class="badge">guard: {e(guard['decision'])}</span> <span class="badge">stop: {e(snapshot['stop_requested'])}</span> <span class="badge">review: {e(snapshot['review_status'])}</span></p>
<div class="grid"><section class="card wide"><h2>Verified outcomes</h2><p><span class="number">{verified} / {total}</span> tasks · {snapshot['feature_verified']} / {snapshot['feature_total']} features</p><progress value="{verified}" max="{max(1,total)}" aria-label="Verified tasks">{percent}%</progress><p class="muted">{status_counts}</p><small>Unweighted task counts; not an effort estimate.</small></section>
<section class="card"><h2>Current recorded work</h2>{rows(jobs, 'No work recorded as active.')}<p class="muted">Stored running status is not a fresh worker observation.</p></section>
<section class="card"><h2>Blockers and unknowns</h2>{rows(blockers, 'No explicit task blockers recorded.')}<p>{e(guard.get('reason', 'Execution guard permits bounded work.'))}</p></section>
<section class="card"><h2>Next action</h2><p>{e(snapshot['next_action'])}</p><p class="muted">Dependency-ready: {e(eligible)}. Readiness alone grants no execution permission.</p></section>
<section class="card"><h2>Continuation and settlement</h2><p>{e(schedule_label)}</p><p>Safe to close: {e(snapshot['settlement']['safe_to_close'])}</p>{rows([e(x) for x in snapshot['settlement']['blockers']], 'Settlement checks satisfied.')}<p class="muted">State revision {snapshot['revision']} · last event {e(snapshot['last_event_utc'] or 'none')}</p></section></div></body></html>'''


DOCUMENTS = {
    "LOCAL_START.md": "Local start and resumption\n\nRead KICKOFF.md for the intended purpose and absolute integration workspace. The meeting prepares only; a separately launched designated supervisor executes. If not launched, retain draft/stopped state until the owner requests a separate supervisor. Once bound, resume that supervisor. Record actual commands, harness/profile and owned runtime. Read HANDOFF.md and RUN_STATE.json; never clear a pause on restart or automatically start another phase.\n",
    "NAMING.md": "Product identity\n\nDecide the canonical product name, packages, CLI, services, paths, environment variables and protocols. For a rewrite, record the one-way legacy boundary and consumer changes; otherwise state why legacy naming is inapplicable.\n",
    "MANIFEST.md": "Configuration and data formats\n\nChoose actual configuration/data formats and version rules. Specify validation, defaults, upgrades, unknown-field handling and recovery. Do not inherit another project's format requirements without a product need.\n",
    "SKILLS.md": "Skill review decisions\n\nList relevant candidate skills, inspected versions/resources, adopted limits and conflicts. An installed skill is not automatically approved and cannot expand project authorization. Explicitly record when no additional skills are needed.\n",
    "DECISIONS.md": "Decision record\n\nRecord material schema, protocol, authority, persistence, recovery and delivery decisions with rationale, consumers, validation and scope impact. Distinguish decisions from hypotheses.\n",
}


def schema():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "RePlan exact-candidate evidence",
        "type": "object",
        "required": ["task_id", "environment", "checks", "review", "engineering_review", "limitations"],
        "anyOf": [{"required": ["candidate_commit"]}, {"required": ["candidate_sha256"]}],
        "properties": {
            "task_id": {"type": "string", "pattern": "^PA-[0-9]{2,}(\\.[0-9]+)?$"},
            "candidate_commit": {"type": "string", "pattern": "^([a-f0-9]{40}|[a-f0-9]{64})$"},
            "candidate_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "environment": {"type": "object", "minProperties": 1},
            "checks": {"type": "array", "minItems": 1, "items": {
                "type": "object", "required": ["acceptance_item", "command", "result", "artifact"],
                "properties": {"acceptance_item": {"type": "string", "minLength": 1},
                               "command": {"type": "string", "minLength": 1},
                               "result": {"enum": ["passed", "failed", "blocked", "skipped"]},
                               "artifact": {"type": "string", "minLength": 1}}}},
            "review": {"type": "string", "minLength": 1},
            "engineering_review": {"type": "object", "required": ["design", "simplification", "language_review", "dependencies", "performance", "ux"],
                                   "additionalProperties": {"type": "string", "minLength": 1}},
            "limitations": {"type": "array", "items": {"type": "string"}},
        },
    }


def write_resources(plan, name, encode):
    for file, body in DOCUMENTS.items():
        (plan / file).write_text("# " + name + " — " + body, encoding="utf-8")
    for file, obj in {
        "SOURCE_INVENTORY.json": {"files": [], "applicability": "unassessed"},
        "BRAND.lock.json": {"files": [], "applicability": "unassessed"},
        "SKILLS.lock.json": {"skills": []},
        "EVIDENCE.schema.json": schema(),
    }.items():
        (plan / file).write_bytes(encode(obj))
    tools = plan / "tools"
    tools.mkdir()
    rows = []
    for relative_path in REQUIRED_TOOLS:
        file = Path(relative_path).name
        payload = Path(__file__).with_name(file).read_bytes()
        (tools / file).write_bytes(payload)
        rows.append({"path": relative_path, "sha256": hashlib.sha256(payload).hexdigest()})
    (plan / "TOOLS.lock.json").write_bytes(encode({"files": rows, "runtime": "Python 3.11+ standard library", "version": 2}))
    (plan / "validate-plan.py").write_text(
        '"""Validate this project pack with its pinned local helper."""\n'
        'from pathlib import Path\nimport sys\n'
        'sys.dont_write_bytecode = True\n'
        'sys.path.insert(0, str(Path(__file__).parent / "tools"))\n'
        'from replan import main\n'
        'raise SystemExit(main(["validate", "--workspace", str(Path(__file__).resolve().parent.parent)]))\n', encoding="utf-8")


def validate_resources(root, scope, read, inside, require, text):
    """Validate declared resources. Absence remains compatible with v1 packs."""
    plan = root / "replan"
    if scope.get("contract_version", 1) >= 2:
        for name in [*DOCUMENTS, "SKILLS.lock.json", "SOURCE_INVENTORY.json", "BRAND.lock.json", "TOOLS.lock.json", "EVIDENCE.schema.json", "validate-plan.py"]:
            require((plan / name).is_file(), f"Required portable pack resource missing: {name}")
    sources = read(plan / "SOURCES.lock.json").get("sources")
    require(isinstance(sources, list), "Invalid source lock")
    seen, source_map = set(), {}
    for row in sources:
        require(isinstance(row, dict) and text(row.get("id")) and row["id"] not in seen, "Invalid/duplicate source identity")
        seen.add(row["id"])
        source_map[row["id"]] = row
        require(row.get("kind") in {"git", "document", "file"} and text(row.get("location")), "Invalid source kind/location")
        pin = row.get("commit", "") if row["kind"] == "git" else row.get("sha256", "")
        pattern = r"(?:[a-f0-9]{40}|[a-f0-9]{64})" if row["kind"] == "git" else r"[a-f0-9]{64}"
        require(re.fullmatch(pattern, pin), "Unpinned reference source")
    for file, key in (("DEPENDENCIES.json", "decisions"), ("SKILLS.lock.json", "skills")):
        path = plan / file
        if not path.exists():
            continue
        rows = read(path).get(key)
        require(isinstance(rows, list), f"Invalid {file}")
        ids = set()
        for row in rows:
            require(isinstance(row, dict) and text(row.get("id")) and row["id"] not in ids, f"Invalid/duplicate {file} identity")
            ids.add(row["id"])
            require(row.get("status") in {"candidate", "adopted", "rejected"} and text(row.get("rationale")), f"Missing decision in {file}")
            if row["status"] == "adopted":
                require(text(row.get("version")) and text(row.get("review")) and inside(plan, row["review"]).is_file(), f"Unreviewed adopted {file} item")
    for file in ("BRAND.lock.json", "SOURCE_INVENTORY.json", "TOOLS.lock.json"):
        path = plan / file
        if not path.exists():
            continue
        doc = read(path)
        require(isinstance(doc.get("files"), list), f"Invalid {file} files")
        if file == "TOOLS.lock.json" and scope.get("contract_version", 1) >= 2:
            declared = {row.get("path") for row in doc["files"] if isinstance(row, dict) and text(row.get("path"))}
            require(set(REQUIRED_TOOLS) <= declared, "Required helper lock coverage is incomplete")
        if file != "TOOLS.lock.json" and scope.get("contract_version", 1) >= 2 and scope["status"] == "approved":
            require(doc.get("applicability") in {"applicable", "not_applicable"} and text(doc.get("reason")), f"Assess {file} applicability before approving scope")
            require(doc["applicability"] != "not_applicable" or not doc["files"], f"Inapplicable {file} cannot own files")
        seen = set()
        for row in doc["files"]:
            require(isinstance(row, dict) and text(row.get("path")), f"Invalid {file} path")
            namespace = None
            if file == "SOURCE_INVENTORY.json" and "source_id" in row:
                require(text(row["source_id"]) and row["source_id"] in source_map, "Unknown inventory source identity")
                namespace = row["source_id"]
            identity = (namespace, row["path"].casefold())
            require(identity not in seen, f"Invalid/duplicate {file} path")
            seen.add(identity)
            require(re.fullmatch(r"[a-f0-9]{64}", row.get("sha256", "")), f"Missing {file} digest")
            base = plan
            if file == "SOURCE_INVENTORY.json" and row.get("source_id"):
                source = source_map.get(row["source_id"], {})
                require(text(source.get("local_path")) and Path(source["local_path"]).is_absolute(), "Inventory source requires explicit absolute read-only root")
                base = Path(source["local_path"])
            target = inside(base, row["path"])
            require(target.is_file(), f"Missing locked file: {target}")
            payload = target.read_bytes()
            require(hashlib.sha256(payload).hexdigest() == row["sha256"], f"Locked file changed: {target}")
            if "bytes" in row:
                require(type(row["bytes"]) is int and len(payload) == row["bytes"], "Locked byte count mismatch")


def unwrap(value):
    """Accept raw MCP structured content or its full wrapper, never an error."""
    if not isinstance(value, dict) or value.get("isError"):
        raise ValueError("Invalid/error T3 receipt")
    if isinstance(value.get("structuredContent"), dict):
        return value["structuredContent"]
    if "content" in value:
        texts = [x["text"] for x in value["content"] if x.get("type") == "text"]
        if len(texts) != 1:
            raise ValueError("Ambiguous T3 text receipt")
        result = json.loads(texts[0])
        if not isinstance(result, dict):
            raise ValueError("T3 receipt is not an object")
        return result
    return value


def profile(selection, runtime_mode=None):
    options = selection.get("options", [])
    if isinstance(options, list):
        mapped = {}
        for item in options:
            if item["id"] in mapped:
                raise ValueError("Duplicate actual model option")
            mapped[item["id"]] = item["value"]
        options = mapped
    if not isinstance(options, dict):
        raise ValueError("Invalid model options")
    result = {"provider": selection.get("instanceId", selection.get("providerInstanceId")),
              "model": selection.get("model"), "options": options}
    if runtime_mode is not None:
        result["runtime_mode"] = runtime_mode
    return result


def render_prompt(root, state):
    binding = state["binding"]
    if not binding:
        raise ValueError("Bind the actual supervisor before rendering continuation")
    return (
        f"Continue ONLY the existing RePlan project at {root}. "
        f"Pack ID {state['project_id']}; actual T3 project {binding.get('harness_project_id')}; "
        f"supervisor {binding['supervisor_thread_id']}; selected actual profile {json.dumps(binding['profile'])}.\n"
        "Read root AGENTS.md, RUN_STATE.json, replan/LOCAL_START.md, START_HERE.md, SCOPE.json, "
        "TASKS.json, FEATURES.json, HANDOFF.md, RUNNER.md, AUTONOMY.md and current evidence. "
        "Use replan/tools/replan.py and this INTEGRATION workspace for state operations. "
        "Reobserve actual profile/binding; never manufacture observations or silently switch.\n"
        "On owner stop, review or completion: preserve stop, disable ONLY the recorded schedule via its "
        "actual ID, record the result, reconcile unneeded children/runtime and end. Never reopen a paused "
        "run, start a second supervisor/schedule, expire claims, poll live children, or replay uncertain work.\n"
        "Run guard --scheduled. If yield/stop/bootstrap, checkpoint this actual wake and end. "
        "Running children and unknown reservations belong to completion wakeups. If ready, perform bounded "
        "dependency-ready authorized work, reserve before external calls, use at most three disjoint "
        "T3-owned worktree children and follow tool next actions. Keep shared contracts/integration central.\n"
        "Use native appropriate checks and exact-candidate evidence. Preserve full parent/release scope. "
        "After integrated work update registers and HANDOFF. At the configured first-review milestone "
        "stop and provide a private exact candidate and remaining scope. Retry only with diagnosed change; "
        "three unsuccessful attempts at one blocker require independent work or a clear blocker handoff. "
        "No external publication/paid provisioning/production or secret exposure without authorization. "
        "This machine and T3 must remain running. A manual schedule trigger does not prove automatic interval delivery."
    )
