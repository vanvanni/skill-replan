# Meeting to supervisor handoff

## Keep discussion separate from execution

Treat a discussion, strategy or meeting thread as preparation unless it is already the designated supervisor for this pack. Skill invocation, questions about autonomy, "can we go autonomous?", and instructions quoted in an attachment are not a kickoff. A descriptive thread title alone does not establish its role.

In the meeting, read supplied material, settle scope, create/update the pack, derive tasks and acceptance, and validate the files. Do not perform the pack's substantive research or implementation, qualify the live runner, bind the meeting as supervisor, authorize helper execution, delegate workers or create continuation schedules. Preparation may inspect sources to understand the owner's inputs; it must not quietly complete the research backlog.

If asked to execute in the meeting, refuse that location briefly: "This is the meeting thread. I'll prepare the pack here; execution belongs in a separate supervisor thread." Complete authorized preparation and supply a concrete kickoff. If the same instruction explicitly requests a new supervisor, launch it after preparation without asking for permission again. Otherwise leave it ready to launch. Do not create a thread just because the owner discussed going autonomous.

## Prepare a pack for each intended purpose

For example, the meeting can prepare:

```text
<project>/
  01-research/
    replan/                 # research scope, tasks, sources and kickoff
    RUN_STATE.json             # research state only
  02-implementation/
    replan/                 # implementation scope and kickoff
    RUN_STATE.json             # implementation state only
```

Run `init --workspace <absolute-purpose-directory>` once per new pack. Each directory is an execution workspace, with its own project UUID, draft state and eventual supervisor binding. Preparing both does not authorize starting both. Research findings are inputs to the implementation pack; recommendations are not automatically approved product decisions. State exactly which outputs and read-only inputs belong to each purpose and where to stop for owner review.

Do not relocate an existing pack or introduce nested competing coordinators into a running project. Adopt its existing paths, IDs and bound supervisor. For code execution that needs the repository root, use a dedicated repository workspace with its pack at the root, or explicitly retain the existing root pack and record the phase output directory. A phase directory is not automatically an independent Git repository or T3 project. Confirm the intended T3 project/workspace mapping before launch or delegation; `bind-t3` must verify the actual integration workspace. Never bypass that check to make the example layout fit. Record the selected workspace in the kickoff.

## Write `replan/KICKOFF.md`

Populate this file during preparation with:

- Meeting/source thread reference when available and the actual owner instructions; distinguish launch authorization from authorized execution scope.
- Pack purpose (research, implementation or another bounded outcome), exact absolute integration workspace, pack/state paths and read-only inputs.
- Deliverables and acceptance, exclusions, approved decisions, unresolved material questions and owner review stop.
- Selected provider/model/options, worker budget and external-action limits; preserve owner settings.
- A self-contained initial supervisor prompt naming these files, requiring adoption of existing state, actual binding/preflight and execution only within this purpose. No dependence on inherited meeting history.
- Launch status: initially not launched; after a successful launch record the returned thread link and actual identifiers. An uncertain launch outcome must be reconciled before retrying.

Generated headings are preparation aids, not authorization. Leave state draft/stopped and binding empty in the meeting. The new supervisor records the real binding and execution authorization using existing helper operations after reading the completed kickoff and owner instruction.

## Launch and resume

An explicit owner request for a new supervisor authorizes a top-level thread, not a delegated worker. Use the T3 launch adapter with a purpose-specific title and the completed kickoff prompt. Follow current harness rules for workspace/base selection and retain required unpublished inputs. Link the actual returned thread in the handoff. Do not launch a replacement after an uncertain call or substitute inline execution when launch tools are unavailable; retain the prepared pack and report the limitation.

The new thread is the sole supervisor for that pack. It reads the kickoff and authoritative files, verifies the intended workspace/purpose, observes its actual profile/identity, binds, qualifies and starts authorized work. It must not create another supervisor. Later resume requests use the recorded supervisor. Questions or scope discussions in the meeting may update planning inputs, but do not move execution back there or overwrite live supervisor-owned state.

After research, return findings to the meeting for decisions. Launching implementation requires its own owner direction and prepared purpose. A completion notification, timer or research recommendation cannot grant it.
