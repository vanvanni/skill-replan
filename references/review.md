# Review and targeted changes

Use for substantive candidate review and owner feedback. Review the smallest candidate that changes risk; a small reversible edit can be checked directly. Independent review is proportional to risk, not a mandatory pair of agents. Reviewers follow [worker ownership](worker-brief.md); they do not edit shared scope or state.

## Establish the review inputs

Pin the base and exact candidate commit or artifact digest, approved acceptance and relevant project standards/contracts. Inspect the actual diff or artifact and existing evidence. If an input is missing, name the limitation; do not infer a pass. Include relevant uncommitted changes explicitly when reviewing work in progress. Never mutate the candidate merely to start a review.

Evaluate two distinct axes in one bounded pass, or separate reviewers when the risk warrants it:

- **Requirements:** missing/partial acceptance, incorrect behavior and unrequested behavior. Cite the FA/PA acceptance or owner decision and give a concrete failing scenario or evidence.
- **Engineering:** correctness, project standards, interfaces, persistence/failure/security, maintainability and applicable UX/performance. Cite the applicable contract/standard; label discretionary design suggestions as suggestions. Skip checks already conclusively covered by tooling unless the candidate invalidates them.

Report findings by axis, with stable IDs within the review series (for example `REQ-01`, `ENG-01`), impact, location, cited requirement/standard, observed problem, and the smallest useful correction and verification. Distinguish blocking defects from optional improvements. State covered areas and limitations even when no finding exists. Avoid reprinting passing checklists or creating separate tasks for every minor finding.

Link the review artifact from the existing evidence `review` string; put engineering assessments in the existing `engineering_review` fields. These instructions do not add schema fields or retroactively upgrade evidence in an adopted pack.

## Incorporate requested changes efficiently

1. Resolve feedback against existing finding IDs and the owner's requested outcome. Identify whether it is a defect correction, a changed requirement, or an optional suggestion. Owner feedback takes precedence over a reviewer's preference. Ask only when a material ambiguity remains; do not require a new full interview or plan for a localized change.
2. Update only affected acceptance, decisions, contracts and task dependencies. Preserve unrelated scope and history. Explain material scope or review-boundary changes; a suggestion does not authorize extra work. The supervisor fixes small findings directly; delegate only a substantial bounded change within existing authorization.
3. Pin the revised candidate and record what changed. Recheck the finding's reproduction and affected behavior/contracts. Broaden to integration or independent review when the change crosses a shared interface, changes material risk, invalidates prior evidence, or the owner requests it. Do not repeat a full review merely because a new commit exists.
4. Close each addressed finding with the candidate, check result and evidence link; keep unresolved/deferred items and their reasons visible. Keep earlier findings and failed proof immutable. A delta recheck is evidence for its stated scope, not a full pass on the new candidate. Previously unchanged observations may be cited as history; all acceptance still needs the exact-candidate proof required by the pack validator before verification/release.

Return a concise change summary: addressed IDs, what now works, remaining blockers, exact candidate and checks, and the next owner-visible outcome. Provide access/reproduction instructions when the owner needs to inspect behavior.

## Owner review milestone

At first review, demonstrate the agreed journeys, link the exact private candidate and launch/access instructions, state remaining full scope, then use `review` and settle the stop per [execution](execution.md). Do not publish merely because a review candidate exists.

Feedback can be clarified and prepared while stopped; it does not silently clear stop or advance to full release. Use the existing helper's supported explicit phase transition before execution. Ordinary `resume` cannot reopen `awaiting_review`, and `advance` means the owner explicitly authorized full release, not merely requested a revision. If the owner wants another first-review revision without full-release authorization, prepare the bounded change and report that this helper has no revision-only transition; keep the milestone stopped rather than bypassing its guard. Code-review rechecks during an authorized execution phase do not invoke the owner milestone `review` command.
