# Agents Help
`agent.define` creates an agent dictionary. `agent.run` performs one AI request. It does not automatically execute tools. `agent.tool` performs one explicit allowlist-checked tool call. If a call says “not permitted”, add the registered tool name to the agent only after reviewing that capability.
