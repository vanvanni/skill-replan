# Local helper operations

Python 3.11+; standard library only. No package installation or live T3 calls. Use the available Python executable; `python` is just an example. `uv python find --offline` can locate an already installed interpreter without downloading one.

All commands take `--workspace <integration-root>`. Never point mutations at a worker worktree. Commands return JSON and exit 0 on a successfully performed/inspected operation, 2 on invalid input or lease contention. **Exit 0 is not execution permission:** inspect `decision`/`guard`. Decisions are `stop`, `yield`, `bootstrap`, or `ready`; a full budget can return `ready` with zero free slots. Stop persists; inspect/checkpoint operations work while stopped.

The helper uses a nonblocking OS file lock at `.replan-local/coordinator.lock`, a strict JSON reader, bound canonical workspace/project identity, full-state validation and same-directory flushed atomic replacement. Every state writer must use it. No stale-lock deletion, TTL, automatic claim expiry or truncate-in-place fallback. Leases span one local operation; durable reservations bridge separate tool calls. This is cooperative single-host coordination, not protection against arbitrary file editing, a distributed lease, or proof of power-loss durability. POSIX locking is implemented but only Windows execution was qualified for the initial package.

For v2 packs, TOOLS.lock must explicitly cover both canonical `tools/replan.py` and `tools/pack_contract.py` paths; an empty or incomplete lock fails validation in draft and approved scope. Hashes do not protect against arbitrary replacement of the validator and its locks by a writer who ignores the protocol.

`validate` checks IDs, DAG cycles, reciprocal feature/leaf ownership, full or explicitly qualified dependency completion, evidence references/acceptance, full release coverage, declared source pins, adopted dependency/skill review references and locked source/asset/helper bytes. It does not run commands, prove truthful receipts, verify a Git checkout's HEAD/cleanliness or semantically prove scope completeness. Source/dependency reviews remain real agent work. Plan edits are supervisor-owned and must be validated before delegation/integration. New packs vendor the helper and its contract module in replan/tools/; use that pinned copy after initialization.

## Commands

For receipt commands supply a JSON file using `--input <file>`; for owner actions supply the actual owner text in a file via `--instruction <file>`. These are caller attestations, not cryptographic authorization. Never manufacture tool results to satisfy the helper. Keep raw harness receipts alongside the normalized input, excluding secrets.

| Command | Effect / input |
| --- | --- |
| `init --name "Name"` | Create draft registers/docs/state; refuses existing pack/state |
| `validate` | Validate pack/state and exact-candidate evidence structure |
| `ready` | Report dependency-ready tasks and execution guard separately |
| `progress [--html <new-file>]` | Read-only JSON snapshot of phase, verified counts, recorded work, blockers, guard and settlement; optionally create a self-contained HTML artifact without overwriting an existing file |
| `guard [--scheduled]` | Report stop/yield/bootstrap/ready and free slots |
| `bind` | `{project_id, supervisor_thread_id, profile:{provider,model,options:{...}}}` from actual harness observation; existing binding cannot silently change |
| `bind-t3` | `{project:<raw t3_project_read>,thread:<raw t3_thread_configure>}`; normalize real receipts, check workspace, preserve distinct pack and T3 project IDs |
| `authorize --instruction file` | Start only a draft with approved scope and actual binding; records already-given owner implementation authorization |
| `preflight` | `{evidence:"evidence/runner.json"}`; preflight task must be verified, actual proof file must exist |
| `runner-ready` | Same evidence shape; requires the preflight task's verified operational milestone. Permits implementation and the one continuation before final automatic-interval proof |
| `reserve` | Atomically reserve one or more disjoint ready tasks; format below |
| `attach` | Record actual delegation receipt against a reservation; format below |
| `terminal` | `{key,status,terminal_evidence}`; status completed/failed/cancelled/interrupted, actual evidence required; does not verify PA task |
| `resolve-reservation` | `{key,status:"not_created",terminal_evidence}` only after confirmed no child was created |
| `schedule-intent` | `{client_request_id:"stable-unique-key"}` before initial scheduler creation; unresolved intent blocks another create |
| `schedule-record` | `{id,enabled,bound_thread_id,interval_ms:1800000,evidence,next_run_utc}` normalized actual receipt; updates only the same schedule |
| `schedule-resolve` | `{status:"not_created",evidence}` only after conclusively confirming no schedule was created; preserves resolved intent history |
| `continuation` | Render the bound project-specific continuation prompt; does not create a schedule |
| `pause --instruction file` | Immediately persist stop/paused; external schedule remains truthfully recorded until disabled receipt arrives |
| `resume --instruction file` | Explicit ordinary pause resume only; terminal work and disabled/non-pending schedule required; clears preflight and leaves schedule disabled |
| `review` | Verified first-review task required; persists stop/awaiting_review; ordinary resume refuses to reopen it |
| `advance --instruction file` | Explicit owner-directed transition from settled first review to full release; retains review history, resets preflight |
| `finish` | Every full task and feature verified; persist completed/stop, then disable the timer and settle actual runtime |
| `runtime-record` | `{key,status:"running"|"unknown"|"settled",evidence}`; track actual scoped processes, servers, lab jobs or VMs |
| `runtime-audit` | `{no_untracked_processes:true,evidence:"evidence/runtime-audit.json"}`; all tracked resources must be settled and actual reconciliation artifact present |
| `settlement` | Report safe_to_close and blockers; requires stop, disabled/nonpending schedule, terminal children and fresh complete runtime audit |
| `attempt` | `{pa_task,blocker,result:"failed"|"resolved",diagnosis,changed_approach?}`; three diagnosed failures block that task's readiness, independent tasks remain available |
| `checkpoint` | Record nonempty bookkeeping JSON without changing control flags |

Before actual runner qualification, `bootstrap` permits only research/planning/test tasks in the preflight task's dependency closure. This allows bounded completion/cancellation tests without pretending preflight already passed. Implementation, continuation and unrelated tasks wait for recorded preflight. Run normal local source/research work within authorization while infrastructure is genuinely blocked.

For staged qualification, define an operational milestone under the preflight task, record its exact evidence, and use runner-ready. Consumers may depend explicitly on that milestone. The parent preflight stays open until an actual automatic interval wake is observed; then verify its full acceptance and record preflight. This avoids a cyclic demand for timer proof before any timer is permitted.

`pause` can persist owner stop, and schedule-record can record an actual disabled receipt, even if task registers or locked files no longer validate. They still require a valid bound RUN_STATE and scope identity. Do not bypass genuinely corrupt state with an invented clean checkpoint; preserve the corruption, disable the known timer via actual harness controls and reconcile explicitly.

Pause preserves existing review and completed phases instead of converting them into ordinary paused execution. Repeated pauses are safe. `advance` also accepts the paused+awaiting_review checkpoint written by older v2 helpers, but only with explicit owner direction and settled work; ordinary resume still refuses that boundary. Completed release proof prevents resumption even when an older helper already changed its phase to paused.

Reserve shape:

```json
{"jobs":[{"key":"login-1","client_request_id":"project-login-1","pa_task":"PA-06","base_commit":"0123456789012345678901234567890123456789","owned_paths":["internal/auth","tests/auth"],"resources":[]}]}
```

`owned_paths`/`resources` must exactly match the task register. Use literal repository-relative file/directory roots, no globs. Paths compare case-insensitively conservatively for Windows. Components ending in a dot/space, Windows device names, control characters and Win32-invalid characters are rejected on every host. Ancestor/descendant paths and identical exclusive resource names conflict. Literal ownership checks are not a filesystem security boundary: do not assign symlink/junction, short-name or other filesystem aliases as separate ownership. Up to three live/reserved jobs total. A pending unknown receipt blocks new assignment; resolve it first. `completed` only means the child ended successfully; PA verification still needs integration checks and evidence.

Attach shape:

```json
{"key":"login-1","task_id":"actual-t3-task-id","child_thread_id":"actual-child-id","run_id":"actual-run-id","link":"actual-returned-link","profile":{"provider":"actual-provider","model":"actual-model","options":{"reasoningEffort":"xhigh"},"runtime_mode":"full-access"}}
```

Profile must match the bound selected profile. A role-specific alternate profile needs an explicit reviewed contract extension; do not silently override it. A failed/cancelled child receipt is still attached before terminal reconciliation. Keep raw outcomes and input files under the project's evidence/local area as appropriate. The event journal is bounded by the 4 MiB JSON limit: archive historical terminal state under a reviewed maintenance procedure before reaching it; never silently drop unknown work.

Run `scripts/test_replan.py` for local behavioral qualification. The installed helper and references can also be supplied by absolute skill path; generated project docs alone do not create a T3 scheduler or install discovery metadata.

Run `scripts/test_contracts.py` for the additional pack/receipt/milestone/settlement/retry contracts. Existing v1 packs retain their schema: no automatic migration, lock refresh or retroactive feature-map rewrite is performed. New packs use contract_version=2. This helper does not import arbitrary CB schemas; existing projects keep their native validator/coordinator until an explicit adapter is reviewed.
