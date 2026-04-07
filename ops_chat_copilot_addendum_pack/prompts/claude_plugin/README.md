# Claude Code Plugin Integration Notes

Suggested integration pattern:

- Put persistent role/context guidance in `CLAUDE.md`
- Add the skill prompts from `skills/`
- Expose Event OS via MCP servers:
  - read-only query server
  - controlled action server
  - optional admin/implementation server
- Add hooks for:
  - audit logging
  - mode fencing
  - dangerous tool confirmation
  - session metadata injection

Recommended visible session modes:
- OBSERVE
- ADVISE
- OPERATE
- IMPLEMENT
