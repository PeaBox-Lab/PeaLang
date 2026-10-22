# TypeScript and React Integration

PeaLang 0.29 adds a TypeScript client and React integration for the runtime sidecar.

## TypeScript

`@pealang/client` provides `PeaLangClient`, portable `PeaValue` types, compile/load/invoke calls, and health/readiness probes.

```ts
const pea = new PeaLangClient("http://127.0.0.1:8787");
const result = await pea.invoke({module:"bonus", function:"calculate", args:[100000,0.15]});
```

## React

`@pealang/react` provides `PeaLangProvider`, `usePeaLang`, and `usePeaFunction`.

```tsx
const {invoke,loading,error}=usePeaFunction<number>("bonus","calculate");
```

## UI schemas

React integration renders a deliberately small schema (`text`, `button`, `stack`) rather than arbitrary JSX or HTML. This keeps extension UI data-controlled and host-rendered.

## Browser-safe capabilities

The initial browser profile permits only `console`, `storage.read`, `storage.write`, and `http.fetch`. Process execution and server filesystem access are rejected.
