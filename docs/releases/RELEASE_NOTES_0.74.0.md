



# PeaLang 0.74.0 Alpha 1 Release Notes

PeaLang 0.74 converts the next agent-safety roadmap target into working runtime controls. Agent tool calls can now be inspected with dry-run planning, blocked through explicit policies, protected with host approval callbacks, and bounded by a configurable call budget.

Repository hygiene is also improved: the cumulative development handover history is preserved under `docs/handover/` instead of occupying the project root.

## Compatibility
Existing `AgentRuntime.tool(agent, name, args)` calls remain valid. Governance arguments are optional and default to the prior allow-listed tool behavior.




