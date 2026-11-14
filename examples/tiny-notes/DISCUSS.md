# Tiny Notes — a discussion-first RePlan trial

This is a proposed test project, not an already approved product backlog or a started run. Discuss it with the owner first; then let the skill generate a new pack from the resulting conversation. Do not copy evidence, source paths, runtime IDs or authorization from another project.

## Suggested small product

A private local browser page with a text field, Add button and list of notes. Notes survive restarting the app. Keep it intentionally small: no accounts, cloud service, synchronization, rich editor or public deployment. Bind only to localhost. Use the language/runtime the owner prefers; an existing Python installation and its standard library are sufficient for a small server and persistence adapter.

First review: add a nonempty plain-text note, see it in the list, restart and see it again; empty input shows a clear error and the page displays user text safely. Full release adds deleting one note, unknown-note/error cases, a short run guide and final regression checks. The first review must not silently mark those later tasks finished.

Ask only these project choices if they remain unanswered:

1. Is a local browser UI the right test, or does the owner prefer a CLI?
2. Are add/list/persistence first and delete after review a useful two-stage scope?
3. Where should the separate disposable T3 project live? Use an owner-selected absolute workspace, referred to below as `<tiny-notes-workspace>`.

The selected model can remain GPT-6.1 Sol / Extra High, with one supervisor and at most three children. This is a workflow trial, not a performance comparison or a reason to buy infrastructure.

## First message to discuss it

> Use $replan to discuss Tiny Notes: a tiny localhost notes page that can add/list notes and keep them after restart, then add delete after the first review. Workspace: <tiny-notes-workspace>. No accounts, cloud or public deployment. First discuss the few choices with me; do not start implementation, workers or schedules yet.

After the discussion, ask:

> Turn our agreed Tiny Notes discussion into the full RePlan pack in this separate project. Use PA task and FA feature IDs, bounded research, explicit acceptance, independent frontend/backend tracks, runner qualification and distinct first-review/full-release gates. Plan only and validate the generated files. Do not manufacture test evidence or start a timer.

When satisfied with the plan, request a separate supervisor:

> Create a new supervisor thread for the approved Tiny Notes implementation pack. Give it the completed KICKOFF.md and exact workspace. Use GPT-6.1 Sol / Extra High and up to three disjoint T3-owned workers. The supervisor must follow the skill's live qualification recipe, including actual completion wakeups, one automatic 30-minute continuation, pause/resume and a stop at first review. Local disposable files/processes/tests are authorized. No public publication, paid provisioning, production changes or changes to unrelated projects. Keep this meeting thread for discussion.

## Expected small task graph

The skill must derive actual acceptance and numbering from the final discussion; this is a sizing example, not a mandatory numbered template:

- Scope/data/API decision and tightly bounded runtime research.
- Runner preflight with an operational milestone; full automatic-interval proof stays open.
- Store/API implementation and static UI implementation in parallel under stable contracts.
- Local integration: add/list/restart/error behavior.
- Bounded independent review, then the first private review stop after full runner qualification.
- After explicit owner continuation: delete/error cases, run guide and complete private release proof.

Each implementation task should be a few files and a few acceptance cases. Avoid a framework, migrations, distributed architecture or an artificial source-parity exercise. An empty upstream-source inventory and no external brand assets are legitimate, explicitly reasoned decisions here.

See [the live qualification gates](../../references/qualification.md). The product is tiny; proving the unchanged 30-minute continuation cadence still takes a real interval. A quicker manually triggered scheduler smoke test can be recorded separately but cannot replace it.
