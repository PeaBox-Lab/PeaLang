



# PeaLang 0.65 Scalable Execution

Version 0.65 extends the 0.64 engine-neutral compute layer with bounded-memory data movement.

## Added
- `PartitionSpec` and deterministic hash/round-robin partitioning.
- Projection and predicate pushdown for JSONL scans.
- Memory-bounded batch scanning and spill files.
- `CheckpointStore` for materialized pipeline recovery points.
- `DistributedLazyFrame.partitioned()` and `.checkpoint()`.

## Example
```python
from pealang.distributed_compute import distributed, PartitionSpec, partition_frame
plan = distributed(frame).partitioned(8, "employee_id").select("employee_id", "country")
result = plan.collect()
plan.checkpoint("employees_clean")
```

For large JSONL inputs, use `scan_jsonl()` to consume batches without loading the complete source file in memory.




