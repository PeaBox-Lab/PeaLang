# PeaLang 0.28.0 Release Notes

PeaLang 0.28 begins first-class Java interoperability through a runtime sidecar and Java SDK.

## Added

- Transport-neutral `RuntimeService` API.
- HTTP runtime sidecar through `pea serve`.
- Health and readiness endpoints.
- Compile, module-load, and exported-function invocation endpoints.
- Semantic validation before remote compilation.
- SHA-256 compilation cache with configurable capacity.
- Structured request IDs, service error codes, and elapsed timing.
- Java 17 SDK using `java.net.http.HttpClient`.
- Java exception mapping foundation.
- Spring Boot integration example guidance.
- Seven runtime-service regression tests.

## Security

The service binds to `127.0.0.1` by default. Authentication, TLS termination, multi-tenant isolation, and remote exposure policy are deployment responsibilities in 0.28. Do not expose the development sidecar directly to untrusted networks.
