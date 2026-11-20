# Planning and adoption contract

## Intake from a long discussion

For consequential ambiguity, use [clarification](clarification.md): inspect evidence, test a concrete scenario, resolve the material question and capture the decision. Reuse the project's glossary and decision records; do not restart a settled interview.

Apply [meeting and supervisor handoff](meeting.md): prepare in the meeting and execute in a separately launched supervisor. Identify the pack's intended purpose before deriving tasks. Separate research and implementation packs when requested; do not treat research completion as permission to begin implementation.

Read the current conversation, project instructions and supplied research. Extract the desired product, users, retained capabilities, deliberate exclusions, technology/runtime constraints, sources and pins, UX/brand inputs, external integrations, migration requirements, validation environments, authorization and first-review outcome. Distinguish owner decisions, verified facts, hypotheses and unresolved questions. Resolve routine choices from context. Ask only questions whose answers change scope, access, cost or irreversible action.

Do not treat a reference project's implementation or this skill as stronger than the owner's scope. For greenfield work, source parity and migration may be inapplicable. For rewrites, preserve required public behavior and inspect source/tests; keep reference foundations read-only and pinned. Record review decisions for candidate dependencies and skills before adopting them. No blanket install of optional packages or skills.

## Files produced

### Create or adopt the workspace

Use `replan/` beneath the selected execution workspace and `RUN_STATE.json` at its root. Separate purpose packs must have separate state and binding; see [meeting workspace choices](meeting.md). New tasks use `PA-01`, features use `FA-01`, and task slices may use `PA-12.1`.

Initialize a new pack with the bundled standard-library Python helper:

```text
python <skill>/scripts/replan.py init --workspace <project> --name "Project name"
python <project>/replan/tools/replan.py validate --workspace <project>
python <project>/replan/tools/replan.py ready --workspace <project>
```

`init` refuses existing packs/state and creates a stopped draft, not an authorized run or fabricated backlog. Populate the actual scope, acceptance, tasks, pins and first-review/full-release boundaries from the discussion. Empty registers are valid only in draft. The helper never calls T3 or starts agents. After initialization use the project's hash-pinned helper; review and repin deliberate upgrades. Preserve existing `AGENTS.md` and `.gitignore`, merging the generated fragment and local ignore rule when needed. See [helper operations](helper.md).

When adopting, preserve existing paths, IDs, instructions, evidence, tools and supervisor binding. Never reinitialize or renumber an existing project. The bundled helper implements PA/FA; an existing CB or other schema retains its native validator/coordinator and needs a reviewed adapter. Do not feed incompatible state to this helper or silently rename it.

The helper generates the layout and document headings. Fill the documents with project-specific decisions rather than maintaining generic placeholder prose.

| File | Responsibility |
| --- | --- |
| `SCOPE.json` | Product authority: approved/draft, outcomes, exclusions, constraints, authorization, review/release task IDs |
| `FEATURES.json` | FA IDs, acceptance outcomes, leaf coverage and reciprocal owning PA IDs |
| `TASKS.json` | PA DAG, kinds, bounded work, acceptance, verified dependencies, paths/resources, evidence |
| `SOURCES.lock.json` | Reference repository URL/commit or document URL/hash and inspection date |
| `SOURCE_INVENTORY.json` | Hashed source snapshots or explicit read-only roots and per-source file mappings; assess applicability |
| `BRAND.lock.json` | Portable approved asset paths, hashes and byte lengths, or a specific no-external-assets decision |
| `SKILLS.md` / `SKILLS.lock.json` | Candidate/adopted/rejected skill versions, actual inspected resources and limits |
| `DEPENDENCIES.json` | Candidate/adopted/rejected dependency and skill decisions, versions, rationale and review evidence |
| `START_HERE.md` | Entry point, owner decisions and actual commands |
| `KICKOFF.md` | Meeting handoff, bounded purpose, workspace, owner instructions, supervisor prompt and actual launch record |
| `PLAN.md` | Delivery strategy, dependency tracks and first visible vertical slice |
| `ENGINEERING.md` | Versioned interfaces, authority, persistence, failure, security and runtime contracts |
| `FRONTEND.md` | Actual journeys, design assets/pins, offline/error state, accessibility and narrow viewport requirements |
| `RUNNER.md` | Harness/model, repository binding, owned test targets, tested tools, machine uptime limits |
| `AUTONOMY.md` | Delegation budget, lease/state protocol, continuation, retry and stop boundaries |
| `HANDOFF.md` | Latest checkpoint first: commits, tests, changed contracts, workers, blockers, next work |
| `LOCAL_START.md` | Actual local runner entry/resume instructions and machine uptime limits |
| `NAMING.md` / `MANIFEST.md` | Canonical project identity and versioned configuration/data-format contracts; no prescribed product stack |
| `DECISIONS.md` / `contracts/` | Material ADRs and bounded cross-worker contracts |
| `TOOLS.lock.json` / `tools/` | Project-owned coordinator snapshot with exact digests |
| `EVIDENCE.schema.json` / `validate-plan.py` | Portable evidence schema and executable pack validator |
| `evidence/` and `briefs/` | Exact-candidate proof and immutable bounded worker assignments |
| root `RUN_STATE.json` | Supervisor binding, stop, continuation, reservations, children, handoff and retry state |

Root `AGENTS.md` should route to the pack; merge the generated `AGENTS.fragment.md` into existing instructions without overwriting them. Secrets stay in harness secret delivery or ignored local files, never the pack. Keep `.replan-local/` ignored; the helper does not edit an existing `.gitignore`.

## Task and feature format

```json
{
  "id": "PA-06",
  "title": "Implement owner login",
  "kind": "implementation",
  "status": "planned",
  "depends_on": ["PA-04"],
  "feature_ids": ["FA-02"],
  "work": "Persist the first owner and establish an authenticated session.",
  "acceptance": ["A valid login creates a session; a wrong password creates none."],
  "owned_paths": ["internal/auth", "tests/auth"],
  "resources": [],
  "evidence": []
}
```

Feature rows contain `id`, `title`, `status`, nonempty `acceptance`, `task_ids` and `evidence`. A verified feature requires all its tasks verified plus feature evidence. Delivery, research, review and test tasks also own relevant FA outcomes. Use the same statuses: planned, in_progress, implemented, verified, blocked. A blocked task needs its blocker recorded in the handoff or task row; independent ready work continues.

New packs use `contract_version=2`. Approved features require an `acceptance_map` object keyed by exact feature acceptance text, with nonempty arrays of `{task_id, acceptance_item}` referencing owned task acceptance. This makes leaf coverage checkable while preserving the distinction between structural mapping and semantic completeness. Approving a v2 scope also requires assessed source-inventory/brand applicability and rationale.

Each feature acceptance item needs a task/leaf acceptance mapping; document complex mappings in `contracts/` if a flat register is inadequate. Validator reciprocity is structural, not a semantic proof of exhaustive coverage. A first-review slice cannot verify its broader parent feature. Add explicit task milestones or bounded child tasks for partial dependencies; preserve full parent acceptance and full release coverage. Do not simply relabel incomplete prerequisites as verified.

For a partial dependency, a parent may declare `milestones: {operational: {status, acceptance, evidence}}`; the consumer declares `dependency_milestones: {"PA-02": "operational"}` alongside `depends_on: ["PA-02"]`. Verified milestone proof identifies `task_id`, `milestone_id`, `full_task_verified:false` and its exact bounded acceptance/candidate. The full parent remains open. Full release cannot pass while any full task is unverified, even when a milestone allowed earlier implementation.

## DAG shape and parallel work

Build the graph from actual contracts, not a fixed numbered waterfall. Typical tracks include:

- source/behavior research and runner preflight independently;
- stable architecture contracts followed by executable foundation;
- frontend/brand and backend primitives in parallel;
- user-visible end-to-end slice with authentic persistence and failure states;
- migration/compatibility and additional feature tracks where dependencies allow;
- native integration, recovery/security qualification and release packaging.

Create research tasks only for consequential unknowns. Bound their output and exit condition; research is not a standing permission to delay implementation. Deliverables should unlock named tasks. Design preflight and first-review tasks from project needs; do not copy CB-48 or CB-50 numbers.

Reserve a parallel batch atomically, at most three entries, before delegation. Assign repository-relative file roots and exclusive lab resources to each entry. Parent/child directories overlap, as do identical resources; those cannot be separate live owners. Shared schema/dependency/status edits remain supervisor-owned. Pass verified absolute read-only source paths because ignored references are not copied into worktrees.

## Evidence format

For a verified task, each evidence JSON referenced relative to `replan/` must contain:

```json
{
  "task_id": "PA-06",
  "candidate_commit": "0123456789012345678901234567890123456789",
  "environment": {"os": "actual OS", "architecture": "actual architecture", "tool_versions": {}},
  "checks": [{"acceptance_item": "exact acceptance text", "command": "actual command", "result": "passed", "artifact": "evidence/log.txt"}],
  "review": "Review outcome and bounded scope, with artifact link",
  "engineering_review": {"design": "assessment", "simplification": "assessment", "language_review": "idiomatic project-language assessment", "dependencies": "assessment", "performance": "assessment or specific inapplicability", "ux": "assessment or specific inapplicability"},
  "limitations": []
}
```

Use the actual full Git commit; alternatively supply `candidate_sha256` for a sealed artifact. Logs/receipts must exist. Every acceptance item needs a passed check at a common exact candidate; do not combine successes from incompatible candidates. Record earlier failed/skipped checks in immutable separate evidence rather than hiding them. Do not claim final integration qualification based on a pre-fix worker candidate. The helper checks structural proof; it cannot certify that a log or review is truthful or that a command qualifies native behavior.

Approved scope needs nonempty outcomes/features/tasks, explicit authorization boundaries, a runtime preflight task, first-review task and full-release task. All features' owning tasks must be transitively required by the full-release gate. Add meaningful project acceptance before setting `status` to `approved`; do not invent an owner approval event. Existing owner instruction to implement is sufficient execution authority when scope matches it.

## Lock record shapes

- Source: `{id, kind:"git"|"document"|"file", location, commit|sha256}`; use an exact Git commit or SHA-256, never a branch/tag as the immutable pin. Add `local_path` as an explicit absolute read-only root when used by source-inventory rows. Qualification of checkout HEAD/cleanliness remains a real source probe, not a JSON claim.
- Source inventory: `{applicability:"applicable"|"not_applicable", reason, files:[{source_id?,path,sha256,bytes?}]}`. With source_id the file path is relative to that locked source's explicit absolute local_path; without it the path refers to a portable snapshot under replan/. Identity is source_id plus case-folded relative path, with portable snapshots in a separate namespace. Two different source roots may both inventory README.md, while duplicates within the same source remain invalid. Inventory hashes are checked, but capability meaning still needs actual inspection.
- Brand lock: `{applicability,reason,files:[{path,sha256,bytes?}]}` with paths relative to replan/. Keep assets portable and preserve licenses. Greenfield projects may document no external foundation/assets; do not copy another project's assets or identity.
- Dependency/skill decision: `{id,status:"candidate"|"adopted"|"rejected",rationale,version?,review?}`; adopted records require an exact version and a real review artifact relative to replan/. Standard-library-only choices can be documented as a decision with no adopted third-party rows.

Locked helper/asset/source bytes are checked by validation. Any refresh needs a reviewed update to its pin and evidence; silently rewriting a lock to accept an unexplained mismatch is not validation.
