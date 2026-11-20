# Execution, review, and recovery

## Ordinary supervisor turn

This loop is for the designated supervisor only. A meeting thread must follow [the preparation and launch boundary](meeting.md) instead. Verify the kickoff purpose before any execution: research authorization does not authorize implementation, even if later implementation tasks appear in planning inputs.

1. Read project instructions, scope, latest handoff and state. Verify actual binding/profile and acquire the integration workspace lease for state changes. Never write worker-local state as if it were the project authority.
2. Process actual completions first. Preserve returned candidate commits and immutable evidence; reconcile terminal records only with known outcomes. Do not expire unresolved claims or delegate uncertain work again.
3. Check authorization, pause/review boundary and preflight. Honor any applicable tool `next`. Scheduled wakes with running children yield; ordinary turns may assign additional independent ready tasks within the budget.
4. Select bounded ready work by dependencies, acceptance, file ownership and test-resource ownership. Persist a batch reservation before external delegation. Reserve at most three total live/reserved entries. Never reserve the same task or ancestor/descendant ownership twice. The helper enforces literal owned paths and resource names, not the semantics of shared APIs.
5. Implement real behavior; run checks appropriate to the changed behavior and runtime. Avoid duplicative ceremony for small reversible edits. Independent storage/auth/protocol review is worthwhile where it adds evidence; repeated exhaustive review without a changed candidate is not progress.
6. Integrate checked worker commits. Resolve shared interfaces centrally. Recheck changes that invalidate evidence; keep exact original candidate proof separate from final integrated proof. Update task/feature status only against acceptance. Partial slices keep parent work open.
7. Update the handoff and exact-candidate evidence, report what works and the next visible outcome. Use completion wakeups, not polling, when waiting. Stop at the agreed review milestone.

## Runtime contract

Preflight the actual target: Linux containers/systemd/FUSE/restore need Linux evidence; browser journeys need real browser checks; hardware/device behavior needs the device. Windows builds, mocks and schema validation do not qualify these. Verify project ownership before resets and preserve unrelated targets. Use disposable data for destructive failure injection.

Pin source revisions and adopted dependencies. Record a material change to schema/protocol/auth/storage/backup/update contracts with its compatibility, consumers and tests. Use idiomatic project technology; this workflow does not prescribe Go or any VM platform.

Three materially unsuccessful attempts at one blocker require a diagnosed change before retry; after the limit, record the blocker and pursue independent work. Respect quota/reset signals. Do not automatically buy capacity or create endless replacement workers. If nothing useful is authorized and runnable, stop and identify the specific missing input.

## Owner pause

The helper stores **intent and observed state**, not external effects. Perform these in order:

1. Persist `stop_requested=true`, `phase=paused` and the actual owner instruction with `pause`. New reservations now fail even if a scheduler fires.
2. Disable the exact existing schedule in T3. Capture and record its actual receipt; do not set `enabled=false` merely because disable was requested. If the outcome is unknown, record it and do not claim the schedule is settled.
3. Stop assigning work. Let bounded jobs finish when practical or cancel the actual task IDs. Preserve worktrees/commits/uncommitted work. Record actual terminal results; cancellation requested is not yet cancellation confirmed. Preserve uncertain reservations rather than fabricating failures.
4. Reconcile spawned shell/test processes and project-owned VMs. A terminal agent does not prove its processes stopped. Finish/interrupt native operations safely and record their status. Stop only owned VMs if requested or needed for shutdown.
5. Update HANDOFF with commits, changed/uncommitted paths, test results, live/terminal jobs, unresolved effects, lab state and exact next work. Use runtime-record for actual owned resources, then runtime-audit with a real complete reconciliation artifact and settlement to report remaining blockers. `guard` reports stop, but **stop alone does not mean safe to shut down**. Confirm safe closure only when schedule, children, reservations and relevant runtime processes are settled. Pause invalidates any earlier runtime audit; terminal agent status alone cannot supply a fresh one.

## Resume and restart

On process restart inspect actual harness outcomes and runtime state before replaying commands. A stopped/paused run stays stopped. Never infer owner resume from opening T3, the next day, a timer or a worker completion.

An explicit owner resume instruction may use `resume` only after ordinary pause, actual disabled schedule and terminal work/runtime reconciliation. It records the instruction and keeps continuation disabled. Re-observe binding/model and runtime/preflight, then re-enable the existing schedule and record the receipt. If there is no prior schedule, create one only after the usual preflight and intent protocol. An awaiting-review boundary needs a separate documented owner phase decision; advance implements that explicit transition without erasing review history. Ordinary resume refuses to reopen it automatically.

When a delegation call's outcome is unknown, keep its reservation. Follow T3's recovery instructions and actual completion notifications. The helper offers no age-based takeover or unsafe reservation deletion command. A confirmed call that never created a child may be recorded with `resolve-reservation` and cited harness evidence.

## Exact-candidate review

Follow [review and targeted changes](review.md) for separate requirement/engineering findings, stable finding IDs and change-focused rechecks. Worker success is implemented, not automatically integrated/verified. Assign reviewers disjoint new test/evidence paths and an actual candidate; they do not alter shared acceptance or ownership.

Before the first review stop, demonstrate the agreed real user journeys, provide private launch/access instructions, identify the exact commit/binary and limitations, and retain full release tasks. Never use the milestone to reduce full product scope. Never publish or deploy to production merely because a local review build exists.

## Return useful progress

Explain what now works, its evidence and practical limits, the next visible behavior, and any specific blocker. Prefer artifact links and observed outcomes over planning-document inventories. Do not invent a completion date. On first review include the exact private candidate, access instructions, verified journeys, remaining scope and explicit paused state.
