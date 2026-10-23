# PeaLang 0.45.0 Release Notes

0.45 introduces the Connector SDK and ships REST plus GraphQL connectors. It includes a pluggable registry and transport, runtime authentication headers, retry/backoff handling, typed errors, REST page/link pagination, GraphQL variables and cursor pagination, and direct conversion of API records into PeaLang DataFrames.

The default transport uses the Python standard library, so the core connectors add no mandatory dependency.
