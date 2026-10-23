# PeaLang 0.44.0 Release Notes

0.44 adds PeaLang Data SQL/database integration. SQLite is directly executable without an extra dependency. DuckDB, PostgreSQL, MySQL/MariaDB, SQL Server and Oracle are supported through optional driver adapters. The API includes parameterized querying, table/column discovery, transactional execution, batched DataFrame inserts and SQLite upserts.

Database-specific merge/upsert behavior outside SQLite remains dialect-specific and is not falsely represented as portable.
