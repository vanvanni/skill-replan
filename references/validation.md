# Validation and qualification

The local helper requires **Python 3.11+** and uses only the standard library. Its **49 behavioral tests pass** on Windows with Python 3.14. Skill metadata, Python syntax, local documentation links and a freshly generated project's pinned validator also pass.

From the skill folder, run:

```text
python -B -m unittest discover -s scripts -p "test_*.py" -v
```

The tests cover scope/feature/task contracts, dependency milestones, exact-candidate evidence, source/asset/tool locks, isolated ownership, parallel reservations, strict JSON, atomic state replacement, cross-process leases, interrupted work, scheduler receipt bookkeeping, explicit pause/resume, review advancement, full release, runtime settlement, bounded retries and refusal to modify legacy packs. Temporary synthetic projects and fake harness receipts are used; no agents, schedules or application runtimes are launched.

The skill-creator metadata validator can also be used when available. Its PyYAML dependency is for that maintainer tool only; the skill helper has no third-party runtime dependencies.

## Meeting boundary checks

The current 49 helper tests, skill metadata validation and local Markdown link checks pass. A freshly initialized purpose workspace includes `KICKOFF.md` and remains draft/stopped with no binding, jobs or schedule.

The thread-role boundary is an agent instruction, not a harness permission or a helper-enforced identity check. The helper has no live thread context. These conversation behaviors still require live qualification:

- Discussing whether to go autonomous stays in the meeting with no execution or thread launch.
- Preparing research and implementation packs creates distinct draft workspaces/state without executing either.
- A request to run in the meeting is redirected to a prepared separate-supervisor handoff.
- An explicit separate-thread launch request launches only the selected purpose; the new supervisor executes without asking again for already supplied authorization.
- A bound supervisor resumes in place, and research completion does not start implementation.

## Optional agent-behavior checks

Follow [the local case protocol](agent-tests.md) when evaluating routing, clarification or review behavior. Store optional fixtures and runs in gitignored `.agent-tests/`; they are not part of helper tests, CI or published qualification. The protocol remains available in a clean clone without requiring private fixtures. Cases that have only been prepared are **not run** and establish no behavioral pass.

## Remaining live gates

Local checks do not qualify actual T3 worktree isolation, child completion/cancellation, automatic interval delivery, real scheduler disable, machine/runtime recovery or product behavior. Complete [the live T3 qualification recipe](qualification.md) in each target environment before claiming those gates pass. POSIX helper execution and Claude/DeepSeek harness adapters remain unqualified.

Use [Tiny Notes](../examples/tiny-notes/DISCUSS.md) for a small discussion-first trial. It has not been launched by skill validation. This package does not install itself globally or start an autonomous run.
