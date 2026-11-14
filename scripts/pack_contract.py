"""Portable execution-pack contracts; stdlib only, no external actions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


REQUIRED_TOOLS = ("tools/replan.py", "tools/pack_contract.py")


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
