---
name: ops-implement
description: Use this skill when the user explicitly asks to change the repository, prompts, configuration, or implementation details behind Event Intelligence OS.
---

# Ops Implement Skill

You are operating in implementation mode for Event Intelligence OS.

## Preconditions
Use this skill only when:
- the user explicitly asks for a code/config change, and
- implementation mode has been granted, and
- you are ready to inspect repository files and run targeted checks.

## Workflow
1. Restate the requested change in implementation terms.
2. Inspect the relevant code/config/prompt files.
3. Produce a short plan before editing.
4. Make focused changes only.
5. Run targeted tests/checks.
6. Summarize what changed, residual risks, and how the system behavior is affected.
7. If relevant, create or update chat memory notes and action records.

## Guardrails
- Do not combine repository edits with live-trading control changes in one step.
- Prefer minimal, auditable diffs.
- If the change implies behavioral risk, call that out explicitly.
- Log all edits via the normal repo/audit workflow.
