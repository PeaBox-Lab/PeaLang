# VM Exceptions, Closures, Defaults, and Modules

PeaLang 0.22 extends compiled execution with structured handlers and module loading.

## Exceptions

```pea
try {
    throw "Unable to calculate"
} catch error {
    print error
} finally {
    print "cleanup"
}
```

The compiler emits `PUSH_HANDLER`, `POP_HANDLER`, and `RAISE`. The VM unwinds frames until it finds a handler, restores the operand stack, binds the catch value, and resumes at the catch target. `finally` executes after normal completion and after handled exceptions.

## Default parameters

```pea
function calculate(amount, rate=0.10) {
    return amount * rate
}
```

Version 0.22 serializes literal defaults in PEAC code objects. Non-literal default expressions remain interpreter-only.

## Shared closures

Compiled functions now retain a shared lexical environment reference. A function can observe a captured variable updated after function creation.

## Imports

```pea
import "bonus.pea" as bonus
print bonus.calculate(100000)
```

Imports resolve relative to the importing source file, compile to bytecode, expose only exported symbols, and use a per-VM module cache.
