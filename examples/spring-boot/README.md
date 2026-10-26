



# Spring Boot integration pattern

Start the PeaLang runtime sidecar on `127.0.0.1:8787`, then register `PeaLangClient` as a Spring bean. Use `loadModule` during application startup, `invoke` from service classes, and `/health` plus `/ready` for Actuator-compatible probes. The Java client intentionally uses JDK 17 `HttpClient` and has no framework dependency.




