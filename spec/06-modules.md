# Modules

A module has a source identity and explicitly exported symbols. Imports resolve relative to the importing module or through package resolution. Non-exported symbols MUST NOT be visible through an imported namespace. Module implementations SHOULD cache an immutable source/package identity.

A dotted specifier such as `api.client` resolves to `modules/api/client.pea` or `modules/api/client/__init__.pea` before dependency lookup. Project manifests provide dependency paths, and dependency entries may be plain path strings or objects with a `path` field. The shared resolver derives a default binding name from the final specifier component and canonicalizes each import path for caching.

Aliased imports execute a module once and reuse its exported namespace. Aliased and side-effect imports participate in cycle detection; a circular aliased import MUST be reported instead of recursing indefinitely. Project analysis exposes nodes, edges, and cycles for discovered modules and reports `M201` for unresolved imports and `M203` for cycles.
