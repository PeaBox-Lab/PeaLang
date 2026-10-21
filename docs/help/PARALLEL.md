# Parallel Help
`parallel { expression ... }` returns a list of results in source order. The runtime uses at most eight worker threads. Keep expressions independent and avoid assumptions about side-effect order. There is no cancellation or per-expression timeout syntax in v0.5.
