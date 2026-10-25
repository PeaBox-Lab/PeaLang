
# PeaLang 0.70.0 Release Notes

PeaLang 0.70 makes DAG execution operationally durable. It adds SQLite-backed run state, retry/backoff policies, deterministic idempotency, interval schedules and backfills while preserving the v0.69 DAG API.

## Upgrade
No breaking change is intended for the 0.69 DAG API. Existing DAGs may opt into `DurableDAGRunner`.

