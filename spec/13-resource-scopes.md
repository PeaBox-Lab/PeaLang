# Resource scopes

A resource scope binds a value to a lexical block and guarantees deterministic
cleanup when the block exits. Programs declare one with:

```pea
using connection = open_connection() {
    print connection.status
}
```

The binding is visible only inside the block. On exit — normal, `return`,
`break`, `continue`, or an exception — the runtime calls `close()` on the value
when that method exists, otherwise `dispose()` when it exists, otherwise no
cleanup is performed. Plain portable values are therefore valid `using`
subjects. Cleanup callbacks registered with a scope run in reverse registration
order (LIFO).

Scopes nest. A child scope inherits its parent's resource limits unless it
supplies explicit overrides, and a scope cannot be re-entered after closing.
The interpreter, bytecode VM, and async VM share the same scope primitives.
The bytecode VM represents scope entry and exit with `SCOPE_ENTER` and
`SCOPE_EXIT` instructions; exceptional unwinding closes all scopes opened after
the matching handler was installed.

Hosts may construct `ResourceScope` and `ResourceScopeManager` objects directly.
A manager exposes the active scope stack, `dispose()`, and portable snapshots.
The language-level `scopes` namespace exposes `current()`, `snapshot()`, and
`dispose()` with the same semantics.

Static project analysis records `using` bindings and reports `R201` when the
same binding name is declared twice in one block and `R202` when a `using`
binding is reassigned inside its scope.
