# PeaLang React SDK (5.26.0)

The shipped `@pealang/react` package provides a client provider, hooks, and a
small UI renderer. Historical source-generator notes are not part of this
package contract.

## Exports

- `PeaLangProvider` — supplies a `PeaLangClient` from `@pealang/client`.
- `usePeaLang` — returns the provider's client.
- `usePeaFunction(module, fn)` — invokes a module function with array args and
  exposes `loading` and `error` state.
- `PeaUi` — renders `text`, `button`, and `stack` nodes with an `onAction`
  callback.

Version: 5.26.0.
