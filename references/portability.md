# Other harnesses and installation

The entrypoint and project pack use ordinary Markdown/JSON. They can be supplied to Claude or DeepSeek-backed agents, but model access alone does not provide orchestration. T3 is the implemented orchestration contract; other harness execution is **not qualified** by this package.

New projects vendor their local coordinator in replan/tools with a digest lock, so another harness can keep the same local planning/state invariants while implementing its own live-tool adapter. Existing non-PA state formats require an explicit adapter, not silent reinterpretation. The Python helper performs no T3 calls and cannot create missing harness capabilities.

Before autonomous execution elsewhere, map and test these capabilities:

| Contract | Required evidence |
| --- | --- |
| Profile/binding | Actual provider/model/options, project and supervisor identity |
| Child isolation | Harness-owned checkout, bounded budget, complete brief |
| Durable task identity | Reservation, actual returned child IDs, idempotency/reconciliation |
| Completion | Push/wakeup or supported wait without polling storms |
| Cancellation | Scoped child termination and preservation of partial work |
| Continuation | One durable timer bound to the supervisor and explicit disable proof |
| Recovery | Unknown side effects remain claimed; no automatic duplicate runs |
| Stop | Pause persists across scheduler/restart; explicit owner resume only |

If the harness lacks a scheduler, offer manual resume/checkpointing and state the limitation. Do not emulate background execution with a shell sleep loop, promise work while the PC is off, silently switch providers, or call an unsupported adapter operational. The helper is local cooperative bookkeeping, not a distributed scheduler.

## Use from this folder

Give the agent the absolute `SKILL.md` path and ask it to use RePlan. This works without changing global skill discovery. The generated pack contains the durable instructions needed at later turns.

For Codex-backed T3 automatic discovery, install the folder as `replan` beneath that harness's actual skill root (commonly `~/.codex/skills/` or a configured shared `~/.agents/skills/`). Check the local harness documentation/settings first; T3 is not itself a universal skill installer. Reload discovery as required by that harness. For Claude or a DeepSeek harness, use its supported skill/instruction loader or the explicit path. This package does not change global configuration, install itself, start schedules, or grant execution permissions.

## Existing packs and boundaries

RePlan was previously named Powerplan Autonimous. New packs use `replan/`, `replan/tools/replan.py` and `.replan-local/`. Existing `powerplan/` packs must continue using their own pinned `powerplan/tools/powerplan.py`, existing lock directory, IDs, state, supervisor and schedules. Do not run the renamed helper against them, rename their files, repin their tools or reinitialize their workspace merely to match the brand. Any future migration requires a separately reviewed adapter and a settled runtime.

The workflow combines authoritative scope, source pins, a feature/task DAG, shared engineering/UX contracts, independent review, exact-candidate evidence, one supervisor/three children, checkpoints, a single continuation and a first-review stop. Product code/assets are not bundled. Product stacks, brands, machines, IDs, secrets and deployment authorization are project inputs, not universal defaults.
