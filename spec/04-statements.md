# Statements

Statements include variable/constant declarations, assignment, expression/print statements, conditional and loop control, `return`, `break`, `continue`, `throw`, `try/catch/finally`, imports, exports and function declarations. An implementation MUST preserve source-order side effects.

`for target in iterable { ... }` obtains one iterator from `iterable`, binds each produced value to `target` (including list and map destructuring patterns), and MUST close that iterator when the loop exits by exhaustion, `break`, `continue`, or an exception. The bytecode implementation reports a compile error for destructuring targets until parity is available. Explicit iterator values expose `next` and `has_next`; `has_next` performs non-consuming lookahead.
