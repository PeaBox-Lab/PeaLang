
# Java and React Interoperability Direction

## Java

Version 0.18 establishes a language-neutral exported-function model. The next practical Java integration should be a sidecar runtime using gRPC or HTTP. A future JVM VM can implement the same module, value, permission, and error contracts without changing PeaLang scripts.

## React

React applications should initially invoke PeaLang through a FastAPI or Java backend. Browser execution requires a JavaScript or WebAssembly runtime and must expose only browser-safe capabilities. PeaLang scripts should return validated data or UI schemas rather than arbitrary JSX.

## Shared value contract

Portable host values are null, boolean, integer, float, string, list, and string-keyed map. Host-specific objects must be converted to this contract before crossing the runtime boundary.

