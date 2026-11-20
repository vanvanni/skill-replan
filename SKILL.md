---
name: replan
description: Prepare purpose-specific execution packs in a meeting thread, then run an explicitly launched separate supervisor with bounded workers, review and checkpoints. Discussing autonomy never starts execution. Use for reusable autonomous project delivery, primarily in T3.
---

# RePlan

Turn the owner's discussion into durable project instructions, then deliver the authorized outcome through a separate supervisor. This is a workflow, not a background service: the harness and execution machine must be running.

## Select the mode

Read only the references needed for the current action. A discussion about RePlan itself does not start a project run.

| Mode | Entry and required guidance | Result / boundary |
| --- | --- | --- |
| Discuss / prepare (default) | Read [meeting](references/meeting.md). For unclear requirements use [clarification](references/clarification.md); when creating a pack read [planning](references/planning.md) and [helper operations](references/helper.md). | Purpose-specific draft pack and self-contained kickoff; no substantive backlog execution, runner qualification, workers or schedules. |
| Launch | Explicit owner request to create/start a separate supervisor; read [meeting](references/meeting.md) and [T3 adapter](references/t3.md). | Launch only the selected prepared purpose. Record the real thread link; do not execute in the meeting. |
| Execute | Designated supervisor with kickoff and actual binding; read [execution](references/execution.md), [T3 adapter](references/t3.md), and [qualification](references/qualification.md) before claiming a runner operational. | Integrate bounded work with exact-candidate evidence; stop at the agreed owner review. Research cannot expand itself into implementation. |
| Review / change | Read [review](references/review.md); for an owner milestone also read [execution](references/execution.md). | Requirement and engineering findings, actionable changes and bounded rechecks. Preserve pause and phase boundaries. |
| Pause / resume | Read the stop/recovery protocol in [execution](references/execution.md) and relevant [helper operations](references/helper.md). | Persist intent, reconcile actual external effects, and reuse the bound supervisor. A timer cannot clear a pause. |
| Adopt | Read [planning](references/planning.md) and [helper operations](references/helper.md) before writing files. | Reconcile existing IDs, scope, evidence, pinned tools and binding; never reinitialize a running pack. |

For another harness read [portability](references/portability.md) and report unproven capabilities. For a worker assignment read [worker brief](references/worker-brief.md). [Invocation examples](references/prompts.md) and [Tiny Notes](examples/tiny-notes/DISCUSS.md) illustrate use; [validation](references/validation.md) distinguishes helper checks from optional agent-behavior checks and live qualification.

## Shared invariants

- Owner scope and authorization remain authoritative. Preserve retained capabilities, exclusions and full-release acceptance across partial milestones; existing authorization does not need ceremonial reconfirmation.
- The meeting prepares; a separately launched supervisor executes only its selected purpose. Reuse that supervisor on resume. At most three active/reserved children, disjoint ownership, T3-owned worktrees and no nested delegation by default.
- Keep planned, implemented and verified distinct. Verification names the exact candidate and actual checks, environment, failures and limitations; structure or mocks alone cannot prove real runtime behavior.
- Recover from durable files and actual receipts. Reserve before external calls, preserve unknown outcomes and partial work, follow returned `next` actions, and never poll or replay uncertain operations.
- Stop on owner pause, the agreed review milestone, or an exhausted blocker with no independent authorized work. Persist stop first, settle actual schedules/children/runtime, and wait for explicit resumption. A review stop is not full completion.
- Keep each pack's state and binding separate. Use its project-owned pinned helper after initialization; review and repin deliberate upgrades. Preserve owner-selected provider/model/options and external-action limits; never inherit another project's identity, assets, paths or permissions.
