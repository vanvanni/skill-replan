<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/replan-logo-cream.svg" />
    <img src="assets/replan-logo-forest.svg" alt="RePlan (T3) by VanVanni" width="400" />
  </picture>
</p>

# RePlan

**From discussion to coordinated execution.**

[![skills.sh](https://skills.sh/b/vanvanni/skill-replan)](https://skills.sh/vanvanni/skill-replan)

An agent skill by [VanVanni](https://vanvanni.nl/) for preparing durable project plans and handing them to a dedicated supervisor for autonomous execution.

RePlan keeps the meeting separate from the work. Discussing autonomy does not start research, implementation, workers or schedules. The meeting prepares purpose-specific packs; an explicitly requested supervisor executes the selected purpose and stops at the agreed review boundary.

## How it works

1. **Discuss.** Settle outcomes, constraints, inputs and review boundaries in your meeting thread.
2. **Prepare.** Create separate packs for research, implementation or another bounded purpose. Each has scope, acceptance, tasks, evidence and a self-contained kickoff.
3. **Hand off.** Explicitly request a new supervisor thread for the selected pack.
4. **Execute and review.** The supervisor coordinates up to three workers, integrates results, checkpoints progress and stops for owner review. Resume uses the same supervisor.

Research completion does not authorize implementation. A timer cannot clear a pause. Plans, implemented work and verified results remain distinct.

## Install

Repository: `vanvanni/skill-replan`. Skill name: `replan`. Invocation: `$replan`.

Install with the [Skills CLI](https://github.com/vercel-labs/skills) using Node.js 22.20 or later:

```sh
npx skills add vanvanni/skill-replan --skill replan
```

This installs into the current project and lets you select your agent. For a user-wide Codex installation, including T3's Codex harness:

```sh
npx skills add vanvanni/skill-replan --skill replan --agent codex --global
```

The CLI handles installation; autonomous execution still requires the T3 capabilities described below.

Alternatively, clone the repository into a folder named `replan` under your harness's skill directory. For a Codex setup using `~/.agents/skills/`:

```sh
git clone https://github.com/vanvanni/skill-replan.git ~/.agents/skills/replan
```

PowerShell equivalent:

```powershell
git clone https://github.com/vanvanni/skill-replan.git "$env:USERPROFILE/.agents/skills/replan"
```

Use your configured skill directory if it differs. Reload skill discovery as required by your harness. You can also give the agent the absolute path to [SKILL.md](SKILL.md) without installing it globally.

## Start with a meeting

```text
Use $replan to turn our discussion into separate research and implementation
packs. Preserve our approved decisions and exclusions. Prepare the files and
kickoffs, but keep this as the meeting thread. Do not launch or execute yet.
```

When ready:

```text
Create a new supervisor thread for the prepared research pack only.
Give it the completed kickoff and exact workspace. Complete the research,
then stop for my review. Do not begin implementation.
```

See [invocation examples](references/prompts.md), [the meeting handoff](references/meeting.md) and the [Tiny Notes trial](examples/tiny-notes/DISCUSS.md).

## What a pack contains

Each execution workspace has a `replan/` directory and a workspace-root `RUN_STATE.json`. The pack includes scope and exclusions, feature acceptance, a task dependency graph, engineering contracts, source and tool locks, evidence, checkpoints and `KICKOFF.md` for the new supervisor. Task and feature identifiers retain the `PA-` and `FA-` formats.

The bundled Python helper creates drafts and manages local state. It uses Python 3.11+ and the standard library; it does not call agents, Git, the network or a scheduler.

```sh
python scripts/replan.py init --workspace /absolute/path/to/project --name "My project"
python /absolute/path/to/project/replan/tools/replan.py validate --workspace /absolute/path/to/project
```

Initialization creates a stopped draft, not an authorized autonomous run. Fill the pack from the owner's actual decisions. After initialization, use the project's pinned helper so skill updates cannot silently change a running coordinator.

## Requirements and limits

T3 is the primary orchestration adapter. Autonomous execution requires the relevant thread, worktree, completion and scheduling tools, plus a running harness and execution machine. RePlan is a skill and local coordinator, not a hosted background service. Other harnesses can use its planning files but need a qualified execution adapter.

The meeting/supervisor boundary is an agent instruction, not a harness permission system. Helper tests do not prove live worker isolation, automatic timer delivery, cancellation or product behavior. See [validation](references/validation.md), [T3 qualification](references/qualification.md) and [portability](references/portability.md).

## Existing Powerplan packs

RePlan was previously named Powerplan Autonimous. Existing `powerplan/` packs must keep their pinned helpers, locks, state, task IDs and supervisor bindings. The renamed helper refuses these workspaces; it does not migrate them. Continue using their existing `powerplan/tools/powerplan.py`. New packs use RePlan paths.

## Development

Run the local behavioral suite from the repository root:

```sh
python -B -m unittest discover -s scripts -p "test_*.py" -v
```

Tests use temporary projects and synthetic harness receipts. They do not launch agents, schedules or application runtimes. GitHub Actions runs the same suite on Windows and Linux with Python 3.11 and 3.14; remote CI results are separate from local validation.

Optional agent-behavior checks cover mode selection, clarification and targeted review changes. See [the local case protocol](references/agent-tests.md). Keep their fixtures, transcripts and generated workspaces under gitignored `.agent-tests/`; they can remain entirely local and are not required by CI. Prepared cases do not count as passed evaluations.

Check that the Skills CLI discovers the package without installing it:

```sh
npx --yes skills@1.8.1 add . --list
```

CI also runs this discovery check with telemetry disabled. The root `SKILL.md` is supported directly; no npm package or extra discovery manifest is needed.

### Publishing and skills.sh discovery

Push the validated commit to the public repository and check GitHub Actions:

```sh
git push -u origin main
```

Then perform a real installation from GitHub using one of the Skills CLI commands above. According to the [skills.sh listing FAQ](https://skills.sh/docs/faq), directory discovery is driven by installations with anonymous telemetry enabled. A local discovery check with `--list` does not register an installation. There is no separate npm publication or manual directory submission step.

After the installation is processed, check the [RePlan directory page](https://skills.sh/vanvanni/skill-replan/replan) and search:

```sh
npx skills find replan --owner vanvanni
```

Indexing and page caches can delay visibility; a successful install alone is not confirmation that the listing is live. The badge and directory link above are prepared for that listing.

## License

[MIT](LICENSE) · Copyright 2026 Joey de Vries / VanVanni.
