# PeaLang AI Development Handover v0.8.0

## Architecture
v0.8 adds `agents.py`. `ToolRegistry` tracks handlers plus metadata; `AgentRuntime` performs one-shot AI calls and explicit allowlist-checked tool calls. Interpreter builds `tool` and `agent` namespaces and bridges user-defined `UserFunction` values into tool invocation.

## Security contract
`agent.tool` denies a registered tool unless its exact name occurs in the agent's configured `tools` list. Permission labels are metadata only. No automatic model-to-tool execution exists.

## Documentation invariant
Every future release must continue detailed README, full cumulative changelog, detailed release notes, roadmap, additions/improvements, language basics, foundations, user guide, help files, feature/reference docs, test report, cumulative version history and this handover.

## Next
v0.8.1 should add typed tool schemas, enforceable permission classes, approval/audit hooks and tooling hardening before any autonomous agent loop is considered.
