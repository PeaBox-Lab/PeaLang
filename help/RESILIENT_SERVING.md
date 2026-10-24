# Resilient Serving help

Wrap `PipelineRuntime` in `ResilientRuntime`. Configure `PEALANG_SERVE_RATE_LIMIT`, `PEALANG_SERVE_MAX_CONCURRENCY`, `PEALANG_SERVE_TIMEOUT`, `PEALANG_SERVE_AUDIT_RETENTION_DAYS`, and `PEALANG_SERVE_LOG_PATH`. Use correlation IDs for traceability and verify signatures before loading production artifacts.
