# PeaLang Browser SDK (5.26.0)

The shipped `@pealang/browser` package exposes a minimal WebAssembly loader.
Source-generation helpers are historical tooling and are not part of the
browser package surface.

## Export

- `loadPeaWasm(url, imports)` — fetch a WebAssembly module, instantiate it with
  the supplied imports, and return the instance result.

Version: 5.26.0.
