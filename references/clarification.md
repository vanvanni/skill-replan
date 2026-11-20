# Clarify consequential requirements

Use during discussion, preparation or an authorized scope change when ambiguity affects outcomes, access, cost, compatibility or irreversible action. If the conversation already settles the requirement, synthesize it; do not restart an interview. This does not authorize the pack's research backlog or execution.

## Resolve one uncertainty at a time

1. Read the owner's existing decisions, relevant code/docs and project glossary. Separate confirmed behavior, owner decisions, hypotheses and open questions. A reference implementation is evidence, not product authority.
2. State the concrete ambiguity and why it matters. Use a small scenario with an observable outcome rather than an abstract design question. For example: "Two people edit the same note offline. On reconnect, should both versions survive or should the last edit replace the other?"
3. Inspect available evidence before asking. If code and the requested behavior disagree, identify the discrepancy; do not silently treat either as the approved future behavior.
4. Propose a recommendation with its consequence. Resolve routine reversible choices from context and label assumptions. Ask the owner only for a material unresolved decision; continue independent preparation while waiting. Never record an unanswered recommendation as approval.
5. Capture the answer immediately in the authoritative scope/acceptance or existing decision record. Identify affected FA/PA acceptance, contracts, dependencies and review boundary. Keep dependent work unready while an indispensable answer is missing.

Stop clarification when the intended outcome is testable and remaining uncertainties are routine implementation choices or named bounded research tasks. Return the resulting decisions, any material open question and the next preparation step, rather than an inventory of documents.

## Shared language and decisions

Reuse the project's glossary and ADR layout when present. Clarify overloaded terms with a concrete distinction (for example, billing account versus login user), then record the settled domain meaning and use it in acceptance, task briefs and code. Create a glossary lazily only when a resolved ambiguity justifies it; keep implementation plans out of the glossary.

Use the pack's existing `DECISIONS.md` or link to a project ADR instead of duplicating decisions. Record a material decision when changing it would be costly, its rationale would surprise a future reader, and real alternatives were considered. Include the choice, rationale/tradeoff, relevant owner instruction or evidence, affected contracts and validation. Keep unresolved proposals visibly separate from accepted decisions.
