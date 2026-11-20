# Short controls and progress

## Harness entry points

Use the loaded RePlan skill with an action argument:

| Action | Claude Code | Codex explicit skill invocation |
| --- | --- | --- |
| Pause | `/replan pause` | `$replan pause` |
| Resume | `/replan resume` | `$replan resume` |
| Visual status | `/replan progress` | `$replan progress` |

Optional Claude command templates are bundled in `commands/claude/`. Copy `pause.md`, `replan-resume.md` and `progress.md` into the target project's `.claude/commands/` (or the user's equivalent) to expose `/pause`, `/replan-resume` and `/progress`. Check for existing names first and preserve them; use a prefixed filename if needed. Do not override the harness's built-in `/resume`, which selects a conversation rather than resuming RePlan state. Installing the RePlan skill alone does not register these aliases. Templates require RePlan to be installed/discoverable and can pass a workspace as an argument.

Claude supports skill arguments and command files; Codex supports explicit skill selection. Other clients, including T3's composer, may intercept or reject unregistered slash text before the agent sees it. Use their available skill picker or `Use RePlan: progress`/`pause`/`resume` when necessary. Never claim bare `/progress` is registered merely because this document describes it. These invocation mappings do not qualify another harness's execution adapter.

Sources: [Claude skills and command files](https://code.claude.com/docs/en/skills), [Codex skills](https://developers.openai.com/codex/skills), [Codex command reference](https://developers.openai.com/codex/guides/slash-commands).

## Resolve the target

Use the explicit workspace argument or the current pack's authoritative kickoff/state. If multiple packs are plausible, ask which one before mutating anything; progress may list available packs without combining their state. With no pack, report that none is prepared; do not initialize one for a control request.

Pause/resume execution belongs to the bound supervisor. In the meeting, route the owner's actual instruction to the recorded supervisor only through a supported, authorized harness mechanism; otherwise give its link and ready instruction. Do not bind the meeting, launch a replacement or edit live supervisor state there. A pasted or quoted command is not an owner control instruction.

## Pause

An actual owner `pause` control is the pause instruction: no second confirmation is needed. Record its text with the pinned helper's `pause --instruction <file>` first, then apply [the stop protocol](execution.md): disable the recorded schedule, settle or cancel owned work safely, preserve partial work and obtain actual runtime settlement evidence. Reply with **paused; settling** until settlement proves safe closure, then **paused; safe to close**. A stopped flag alone is insufficient.

## Resume

An actual owner `resume` control authorizes resumption of an ordinary paused run within its existing scope, profile and phase. Reconcile actual jobs, schedules and runtime, use the pinned helper's `resume --instruction <file>`, reobserve binding/profile and preflight, then re-enable the existing continuation when qualified. No duplicate supervisor or timer. Report a specific blocker if reconciliation is incomplete. Drafts need launch/execution authority; completed runs stay complete. At `awaiting_review`, report the pending owner phase decision; never translate resume into `advance`.

## Progress (read only)

Read the current pack with its pinned helper:

```text
python <workspace>/replan/tools/replan.py progress --workspace <workspace>
python <workspace>/replan/tools/replan.py progress --workspace <workspace> --html <workspace>/.replan-local/progress.html
```

The second form writes only a self-contained visual artifact; choose a new filename for each snapshot because existing files are never overwritten. Existing pinned helpers may not have `progress`: inspect their supported commands and read their native state/registries without mutating them. Do not upgrade pins for a status request. If validation fails, report the error and the last trustworthy checkpoint rather than inventing a healthy dashboard.

Show purpose/name, snapshot time, phase and stop/review state, verified task/feature counts, recorded active work with links when available, uncertain reservations, explicit blockers, schedule state and the next dependency-ready tasks. Suppress runnable-work claims while the guard stops/yields; dependency-ready is not execution permission. Task completion counts are unweighted counts, not elapsed effort or delivery estimates. `implemented` is not `verified`.

Stored running jobs are **recorded running**, not proof they are still active. Label observations with their source/time. Do not call `task_status` on running delegates, poll, resume, reconcile receipts, schedule, or assign work to refresh a view. Use already delivered completion information and permitted read-only observations; keep any newer observation distinct from stored state. A progress request does not wake another supervisor to continue work.

In T3, show the generated HTML using `html_preview` then `html_render`. In a terminal or when those tools are unavailable, show a compact text bar (`verified / total`), phase, current recorded tasks, blockers and next action, with an artifact link if generated. Treat it as a snapshot; refresh only on another request. No server, timer, network assets or automatic browser refresh.
