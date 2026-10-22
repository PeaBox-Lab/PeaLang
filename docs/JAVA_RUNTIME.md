# Java Runtime Integration

PeaLang 0.28 provides a language-runtime sidecar and a dependency-light Java 17 client.

## Start the sidecar

```bash
pea serve --host=127.0.0.1 --port=8787
```

Endpoints:

- `GET /health`
- `GET /ready`
- `POST /v1/compile`
- `POST /v1/modules/load`
- `POST /v1/invoke`

## Load a module

```json
{
  "name": "bonus",
  "source_name": "bonus.pea",
  "source": "function add(a,b){return a+b}\nexport add"
}
```

## Invoke

```json
{
  "module": "bonus",
  "function": "add",
  "args": [10, 20]
}
```

The service performs semantic checks before compilation and caches bytecode by SHA-256 source hash. Responses include a request ID and elapsed time.

## Java 17 client

The bundled `java-sdk` contains `io.pealang:pealang-java-client:0.28.0`. It uses the JDK `HttpClient`, so it can be wrapped as a Spring Boot bean without requiring Spring inside the core SDK.
