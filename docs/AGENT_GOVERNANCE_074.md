# Agent Governance 0.74

PeaLang 0.74 adds deterministic safety gates around agent tool execution.

## Capabilities
- Dry-run tool planning without side effects.
- Per-tool deny policies.
- Approval-required tool policies with host-provided approval callbacks.
- Per-run tool-call budget enforcement.
- Serializable policy decisions for audit and UI integration.

## Example
```python
policy = AgentPolicy(approval_required=["deploy"], max_calls=8)
plan = runtime.tool(agent, "deploy", ["staging"], policy=policy, dry_run=True)
result = runtime.tool(agent, "deploy", ["staging"], policy=policy,
                      approval=lambda request: request["tool"] == "deploy")
```

Dry-run never invokes the underlying tool handler. Approval-required operations fail closed when no approver is provided.