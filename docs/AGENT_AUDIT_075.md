



# PeaLang v0.75 Durable Agent Audit and Approvals

v0.75 hardens the v0.74 governance layer with persistent approval and audit evidence.

## Added
- SQLite-backed append-only governance audit events.
- Durable pending/approved/denied approval records.
- Deterministic approval request IDs.
- Approval actor and reason capture.
- Tool-execution audit evidence when an audited approval gate is used.
- Reuse of previously resolved approval decisions after reopening the audit database.

This is additive to the v0.74 dry-run, deny-policy, approval and tool-budget APIs.




