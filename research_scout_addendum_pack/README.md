# Autonomous Research Scout Addendum Pack

This pack adds an autonomous research subsystem to Event Intelligence OS.

## Included artifacts

- `docs/23_autonomous_research_scout_architecture.md`
- `db/05_research_scout_extension.sql`
- `api/openapi_research_scout.yaml`
- `prompts/context_deepener_*`
- `prompts/universe_discovery_scout_*`
- `prompts/candidate_promotion_reviewer_*`
- `prompts/research_brief_composer_*`

## Intent

The subsystem continuously:
1. deepens context for watched symbols, and
2. discovers new symbols that deserve monitoring.

It is designed to integrate with:
- inquiry orchestration
- ops chat copilot
- source registry / market profile
- event / forecast / postmortem ledgers
