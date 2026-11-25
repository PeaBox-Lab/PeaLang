# Safe metaprogramming

Macro expansion is explicit and happens before parsing. It does not alter the
default source pipeline, so existing programs execute unchanged.

A `SafeMacro` declares a named pattern with named metavariables (`$name`) and a
template. Definitions are validated before registration: names, delimiter
balance, metavariable references, marker usage, and size limits are checked.
Invalid definitions are reported instead of silently changing source.

Expansion is bounded by pass, per-macro use, capture length, and total-work
limits. Repeated metavariables must capture identical text, and captures with
unbalanced delimiters are rejected. If expansion does not converge within the
safe pass limit, an `MG203` issue is reported.

Templates support hygiene markers (`@name`). With hygiene enabled, each marker
is replaced by a generated identifier before captures are substituted, so a
macro-introduced temporary cannot be captured by caller-supplied code. Hygiene
markers are invalid when hygiene is disabled.

`expand_source_macros()` returns expanded source or raises
`MacroExpansionError`; `compile_source_with_macros()` expands and then compiles
in one step. Legacy string macros remain available for compatibility but are not
part of the safe expansion pipeline.
