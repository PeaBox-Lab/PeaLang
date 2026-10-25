# PeaLang Data Roadmap

## 0.42 Data Foundation
Schemas, DataFrame/LazyFrame, connector registry, CSV/JSON/JSONL, core transforms.
## 0.43 DataFrame Engine
Joins, group-by/aggregations, windows, pivot/unpivot, null handling, expression engine, lazy optimizer, chunked execution.
## 0.44 SQL and Databases
DuckDB adapter; SQLite, PostgreSQL, MySQL/MariaDB, SQL Server, Oracle adapters; discovery, parameters, transactions, batching, upsert/merge.
## 0.45 Connector SDK
REST, GraphQL, OData, SFTP, S3, Azure Blob/Data Lake, GCS, SharePoint plus branded/custom connector packaging and certification tests.
## 0.46 Statistics and Analytics
Descriptive statistics, correlation/covariance, statistical tests, regression, time-series foundation, Python/R/Arrow exchange.
## 0.47 Unstructured Data
TXT/HTML/Markdown/PDF/DOCX/log ingestion adapters, extraction schemas, tokenization, chunking, OCR adapter contract.
## 0.48 Streaming and Scale
Kafka/Event Hubs/WebSockets, windows, micro-batches, checkpoints, backpressure, parallel execution and spill-to-disk.
## 0.49 Data Security and Governance
Source-scoped permissions, secret providers, TLS policy, data classification, masking, lineage, audit logs and connector allowlists.
## 0.50 Data Conformance Gate
Cross-engine conformance, connector contract suite, query-plan regression tests, performance/correctness thresholds and real data-pipeline pilots.
