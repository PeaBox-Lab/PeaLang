# PeaLang 0.29.0 Release Notes

PeaLang 0.29 adds TypeScript and React integration around the 0.28 runtime-service contract.

## Added

- `@pealang/client` TypeScript SDK.
- Portable recursive `PeaValue` type contract.
- Typed health, readiness, compile, load, and invoke client methods.
- `@pealang/react` integration.
- `PeaLangProvider`, `usePeaLang`, and `usePeaFunction`.
- Safe schema-driven `PeaUi` renderer foundation.
- Browser-safe capability profile.
- UI schema validation rejecting arbitrary HTML nodes and unknown fields.
- Web SDK regression tests.

## Browser strategy

0.29 keeps execution on the PeaLang sidecar by default. The browser receives portable values and safe UI schemas. A WebAssembly VM remains experimental until it can pass the same conformance suite as the Python VM.
