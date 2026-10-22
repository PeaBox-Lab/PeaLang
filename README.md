# PeaLang 0.29.0

PeaLang is an embeddable extension language designed to extend Python, FastAPI, Java, Spring Boot, TypeScript, React, API services, workflows, and business applications.

## TypeScript

The source release includes `typescript-sdk` with `@pealang/client`.

```ts
const pea = new PeaLangClient("http://127.0.0.1:8787");
const result = await pea.invoke({module:"bonus",function:"calculate",args:[100000,0.15]});
```

## React

The `react-sdk` contains `PeaLangProvider`, `usePeaLang`, `usePeaFunction`, and the safe `PeaUi` schema renderer.

## Runtime integration coverage

- Python and FastAPI
- Java and Spring Boot through the runtime sidecar
- TypeScript and React through the service client
- Sync and native async VM embedding
- Optional static typing and semantic analysis
- PEAC compiler/VM and DAP
- Package manifests, locks, audit, and reproducible packages

See `docs/TYPESCRIPT_REACT.md`, `docs/JAVA_RUNTIME.md`, `docs/PACKAGES.md`, and `docs/ASYNC_VM.md`.
