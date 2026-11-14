---
name: replan
description: Prepare purpose-specific execution packs in a meeting thread, then run an explicitly launched separate supervisor with bounded workers, review and checkpoints. Discussing autonomy never starts execution. Use for reusable autonomous project delivery, primarily in T3.
---

# RePlan

Convert the owner's discussion and research into durable project instructions, then implement the approved product. This skill defines a workflow, not a background service. T3 and the execution machine must be running for work to progress.

## Choose the mode

- **Meeting / prepare (default):** discuss, synthesize and prepare purpose-specific packs. Mentioning replan, autonomy, research or implementation does not authorize execution. The meeting thread must refuse to become the execution supervisor, even on a request to run the work here; prepare the handoff for a separate thread instead. This includes substantive research, runner qualification, workers and schedules, not just product implementation.
- **Launch:** only on an owner request to create/start a separate supervisor, launch the selected prepared pack in a new thread with its intended purpose. Preparation alone does not authorize thread creation. Follow [meeting and supervisor handoff](references/meeting.md); do not execute the pack in the meeting thread.
- **Execute (designated supervisor only):** verify the kickoff, purpose and actual thread binding; preserve approved scope, preflight, execute bounded tasks, review, integrate and checkpoint. Existing execution authorization counts within that purpose; do not demand a second ceremonial approval. A research supervisor cannot expand itself into implementation.
- **Pause/resume:** use the explicit stop protocol below. A new day or scheduler wake cannot clear an owner pause.
- **Adopt:** reconcile an existing project before creating files. Preserve existing instructions, task identifiers, evidence and work. Never reinitialize an existing pack. The helper implements the PA/FA schema; for an existing CB or other schema, retain its native validator/coordinator and map the workflow through a reviewed adapter. Do not feed incompatible state to this helper or silently rename it.

Read [meeting and supervisor handoff](references/meeting.md) before preparing or launching a pack; [the planning contract](references/planning.md) when making/adopting one; [the T3 adapter](references/t3.md) before launching, delegation or scheduling; [the execution contract](references/execution.md) before running, pausing or resuming. For another harness, read [portability](references/portability.md) and report unproven capabilities.

See [invocation examples](references/prompts.md) for discussion-to-plan, execution and pause/resume requests. For tested behavior and qualification limits see [validation](references/validation.md).

Before claiming a new runner operational, follow [T3 qualification](references/qualification.md). For a small discussion-first trial use [Tiny Notes](examples/tiny-notes/DISCUSS.md).

## Durable pack

Use `replan/` beneath the selected execution workspace and `RUN_STATE.json` at that workspace's root. The meeting may prepare separate purpose directories, such as `01-research/` and `02-implementation/`, each containing its own pack and state; see [workspace choices](references/meeting.md). Never let independent packs share a state file or binding. Use **PA-01** for tasks and **FA-01** for features; task slices may use `PA-12.1`. Task kinds distinguish research, planning, implementation, review, test, documentation and delivery. Do not renumber existing project IDs when adopting a running project.

Create a new pack with the bundled standard-library Python helper:

```text
python <skill>/scripts/replan.py init --workspace <project> --name "Project name"
python <skill>/scripts/replan.py validate --workspace <project>
python <skill>/scripts/replan.py ready --workspace <project>
```

`init` refuses existing packs/state and creates a **draft**, not an authorized run. It generates instructions and registers, not a fabricated product backlog. Populate the actual scope, features, tasks, acceptance criteria, source pins and first-review/full-release boundaries from the discussion. Empty registers are valid only while scope is draft. The helper never calls T3 or starts agents. See [helper operations](references/helper.md).

New packs include project-owned hash-pinned helper snapshots, source/asset/skill locks, an evidence schema, naming/format/engineering contracts and a validator. After initialization use `replan/tools/replan.py` in the integration workspace so later skill edits cannot silently change a running project's coordinator. Review and repin any deliberate helper upgrade. Existing AGENTS.md and .gitignore are preserved; merge the generated instruction fragment and ignored local directory if needed.

## Execution invariants

1. **Scope stays authoritative.** Record retained capabilities, deliberate exclusions, constraints and acceptance outcomes. First usable review is an intermediate milestone. Keep full parent requirements and release gates open until proved.
2. **Separate meeting and supervisor; at most three active children per supervisor.** The meeting prepares; an explicitly launched supervisor executes only its selected purpose. Reuse that supervisor on resume; do not create replacements or automatically launch later phases. The supervisor owns shared contracts, dependencies, task/feature status and integration. Use separate T3-owned worktrees and complete bounded briefs. No nested delegation by default. Do not create shell worktrees.
3. **Parallelize by dependency and ownership.** Run multiple ready PA tasks concurrently where contracts, files and lab resources are disjoint. UI/brand work can run alongside backend work once its own prerequisites are verified. Do not stall all tracks on a review. The scheduled recovery path still yields while known children run; it does not poll them or fill slots. Normal supervisor turns may reserve independent ready work.
4. **Implement early.** Source research resolves specific behavior or risk and ends in fixtures, decisions or reusable implementation inputs. Plan a real user-visible vertical slice early. Do not serialize the entire historical compatibility project ahead of every visible workflow without a concrete dependency.
5. **Keep execution factual.** Planned, implemented and verified mean different things. Record exact candidate commit/artifact digest, real commands/results, environments, failures, limitations and engineering review. A cross-build or mock cannot qualify native storage, restore or failure behavior. Independent review is bounded by risk; fix small findings directly and review substantial new changes with a new task.
6. **Recover from files.** Commit shared inputs before delegation. Checkpoint after integrated slices and at session/context boundaries. Persist reservations before external calls; unknown outcomes block replay. Reconcile actual terminal outcomes, never infer them from age or a stale PID.
7. **Continue within authorization.** T3 completion wakeups drive the loop. After the operational runner milestone passes, use one persistent 30-minute continuation bound to the same supervisor. Full runner qualification additionally requires actual automatic interval delivery; do not invent this proof to break the bootstrap dependency. Record actual settings and schedule IDs; no silent provider/model substitution. Honor the tools' returned `next` actions. No polling loops.
8. **Stop reliably.** An owner pause, exhausted diagnosed retries, missing indispensable authorization/access, or first-review milestone must stop the relevant work. Preserve explicit stop state and disable the recorded schedule. Settle or cancel unneeded children, preserve their work, hand off a stable checkpoint, and wait for explicit owner resumption. A review stop is not proof of full completion.

The suggested T3 profile is GPT-6.1 Sol / Extra High unless the owner selects another supported profile. Record actual provider/model/options for each role. Never copy another project's IDs, source paths, technology requirements, machine identities, brand assets, secrets or deployment permissions into a new project.

At the first review, use `review` and stop. Only an explicit owner instruction to proceed to the full release permits `advance`; this preserves review history and resets runtime preflight. Ordinary `resume` never grants that phase change. Every full feature/task remains required at `finish`.

## Return useful progress

Explain what now works, its evidence and practical limits, the next visible behavior, and any specific blocker. Prefer artifact links and observed outcomes over inventories of planning documents. Do not invent a completion date. On first review supply the exact private candidate, instructions, verified journeys, remaining scope and the explicit paused state.
