# Kickoff prompts for Claude Code and Codex

## 1. Claude Code — repository bootstrap prompt
Use this at the start of implementation.

```text
You are the primary implementation agent for Event Intelligence OS.
Read `CLAUDE.md`, `AGENTS.md`, and the design pack in the order they specify.
Then do the following:
1. Summarize the architecture and non-negotiable invariants.
2. Identify the smallest implementation slice that creates real project structure without overcommitting the architecture.
3. Produce an execution plan with phases, touched directories, tests, schemas, migrations, and open risks.
4. Begin implementing only phase 1 unless I ask for more.
5. After changes, run the relevant validation commands and summarize results.

Important:
- Preserve ledger separation.
- Preserve market/source/provider abstraction.
- Preserve Grafana shell + plugin architecture.
- Prefer additive, versioned contracts.
- If commands do not exist, scaffold the standard ones before deeper feature work.
```

## 2. Claude Code — feature implementation prompt
Use for a bounded feature.

```text
Implement the following feature in Event Intelligence OS:
[PASTE FEATURE]

Before coding:
- read the relevant sections named in `CLAUDE.md`
- list impacted ledgers, APIs, schemas, migrations, tests, and Grafana/plugin surfaces
- point out any architectural conflicts with the design pack

Then:
- implement the smallest complete vertical slice
- add/update tests
- update docs/contracts as needed
- summarize follow-up work separately from the code you actually changed
```

## 3. Codex — review prompt
Use after Claude implements a change.

```text
Review the current diff for Event Intelligence OS.
Follow `AGENTS.md` and `code_review.md`.
Prioritize P0/P1 findings.
Focus on:
- contract breakage
- migration safety
- execution-mode correctness
- source/market/provider adapter boundary violations
- missing tests
- missing observability for new failure paths
Return findings grouped by severity with file references and concrete fixes.
```

## 4. Codex — validation prompt
Use when you want Codex to exercise tests and identify gaps.

```text
Validate the current implementation against repository instructions.
1. Read `AGENTS.md`.
2. Run the smallest relevant test/lint/typecheck/contract commands.
3. Report failures, flaky areas, and missing test coverage.
4. Suggest the minimum additional tests needed before merge.
Do not rewrite architecture unless necessary to fix a correctness issue.
```

## 5. Codex — instruction maintenance prompt
Use when recurring mistakes appear.

```text
We found recurring review feedback in this repo.
Update `AGENTS.md` and/or `code_review.md` so future sessions inherit the fix.
Keep root instructions concise.
If the rule is directory-specific, suggest a nested AGENTS file instead of bloating the root file.
```
