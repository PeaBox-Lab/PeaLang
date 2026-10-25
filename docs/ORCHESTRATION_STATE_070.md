
# PeaLang 0.70 Durable Orchestration

Version 0.70 extends the 0.69 DAG layer with operational execution semantics.

## Capabilities
- SQLite-backed durable task-run state and history.
- Per-task retry policies with exponential backoff and optional jitter.
- Deterministic idempotency keys and successful-run deduplication.
- Interval scheduling and inclusive backfill windows.
- Logical execution dates for reproducible pipeline runs.
- Attempt and state reporting per task.

## Example
```python
from pealang import DAG, DurableDAGRunner, RetryPolicy, SQLiteStateStore

dag = DAG("daily_hr")
@dag.task("extract")
def extract(): return [1, 2, 3]

runner = DurableDAGRunner(SQLiteStateStore("pea-runs.db"))
result = runner.run(dag, logical_date="2026-10-24", retry=RetryPolicy(max_attempts=3, initial_delay=1))
```

Idempotency is scoped to DAG, task, logical date, and canonicalized inputs. A repeated successful run is skipped and its stored result is returned.

