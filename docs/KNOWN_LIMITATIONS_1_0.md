# Known Limitations for PeaLang 1.0

- Browser PEAC-to-native-WASM execution is Preview.
- Distributed compute/serving and agent/ML extensions are Preview unless a specific API is marked Stable.
- Portable upsert is guaranteed for SQLite; other SQL dialects require adapter-specific conformance evidence.
- External services such as Redis, Kafka, cloud object stores and Microsoft Graph require their optional dependencies and real credentials.
- A successful local test run does not substitute for retained Windows, Linux and macOS CI evidence or external security review.
