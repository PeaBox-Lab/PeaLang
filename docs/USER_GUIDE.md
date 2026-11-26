# PeaLang User Guide

This guide covers the PeaLang 3.1.43 release (unified versioning; supersedes the 1.0.0-experience and 0.99.6 baselines).

## Installation and Setup

Requirements: Python 3.10+.

```bash
git clone https://github.com/PeaBox-Lab/PeaLang.git
cd PeaLang
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e .
pea --help
pea doctor
```

## CLI Reference

| Command | Purpose |
|---|---|
| `pea run <file.pea>` | Run a PeaLang source file |
| `pea repl` | Interactive REPL |
| `pea eval -e "<code>"` / `-f <file>` | Evaluate code string or file |
| `pea check <paths...> [--json]` | Parse/check source files (JSON report supported) |
| `pea lint <paths...> [--json]` | Check with lint summary (JSON report supported) |
| `pea fmt <paths...>` | Format source files (`--check` supported) |
| `pea test [paths...]` | Run PeaLang/native tests (`--filter`, `--coverage`) |
| `pea compile <file.pea>` | Compile to `.peac` bytecode |
| `pea dis <file.peac>` | Disassemble bytecode |
| `pea vm <file.pea|.peac>` | Run via bytecode VM |
| `pea optimize <file.pea> [--verify]` | Optimize bytecode and report parity |
| `pea fast <file.pea> [--verify] [--benchmark]` | Run via the direct-handler fast interpreter |
| `pea jit <file.pea> [--verify] [--benchmark]` | Profile and run hot traces with JIT guards |
| `pea native <file.pea> [--verify] [--emit FILE.c]` | Lower to native IR and verify VM parity |
| `pea wasm-backend <file.pea> [--verify] [--emit FILE.wasm]` | Lower to WASM IR and verify VM parity |
| `pea parallel <file.pea> [--verify] [--tasks N] [--workers N]` | Run isolated bytecode tasks in order |
| `pea profiler <file.pea> [--verify] [--emit FILE.json]` | Capture deterministic execution counters |
| `pea perf-gate <file.pea> [--iterations N]` | Evaluate 4.0 performance gates |
| `pea analyze <file.json|csv> [--json] [--head N]` | Profile a JSON/CSV dataset (analysis) |
| `pea web-openapi` / `pea openapi <file.pea> [--title T] [--version V]` | Extract OpenAPI from a file defining `app` |
| `pea hash <file> [--algo sha256]` | Compute file hash |
| `pea tree [path]` | List `.pea` source files |
| `pea env <NAME>` / `--keys` | Get an environment variable (or list names) |
| `pea version [--json]` | Print version (JSON supported) |
| `pea typecheck <paths...>` | Optional type checking |
| `pea semantic <paths...>` | Semantic analysis |
| `pea quickstart` | Print quickstart commands |
| `pea doctor` | Environment and dependency diagnostics |
| `pea templates` | List project templates |
| `pea init [path] [--name N] [--template T]` | Create a project (`default`, `webapp`, `api`, `analysis`, `etl`, `automation`, `library`, `interop`) |
| `pea new [path] [--template T]` | Alias for `init` |
| `pea serve-web <file.pea> [--host H] [--port P]` | Run a file and serve its exported `app` (best-effort) |
| `pea project [path]` | Show project manifest info |
| `pea info` | Runtime/stdlib/command info |
| `pea serve [--host H] [--port P]` | Start runtime HTTP sidecar |
| `pea stdlib` | Print stdlib manifest |

## Language Basics

```pea
let name = "PeaLang"
const version = 1
print "Hello " + name

if version > 0 {
  print "ready"
}

for x in [1, 2, 3] {
  print x
}

function add(a, b) { return a + b }
print add(2, 3)
```

## Modern Ergonomics

### Comprehensions
```pea
let xs = [1,2,3,4]
let doubled = [x * 2 for x in xs if x > 1]
let pairs = [[1,10],[2,20]]
let values = [v for [k,v] in pairs]
let squares = {k: v*v for [k,v] in items({"a":2,"b":3})}
```

### Explicit iterators
```pea
let it = iter([1,2,3])
print has_next(it)      # true
print next(it)          # 1
for x in it { print x } # 2, 3
```
`iter()` returns a lazy iterator with non-consuming `has_next()` and `peek()`.
`next(it, default)` returns `default` at exhaustion. Iterators work in the
interpreter, bytecode VM, and async VM; existing eager helpers are unchanged.

### Structured async concurrency
```pea
async function fetch_all() {
    let jobs = [api.fetch("users"), api.fetch("orders")]
    return await concurrency.gather(jobs)
}

let task = concurrency.spawn(api.fetch("metrics"))
let value = await concurrency.result(task)
```
`concurrency` also provides `sleep`, `timeout`, and `cancel`. Spawned tasks
inherit a structured cancellation scope, so cancelling the VM token cancels
its children. Static analysis treats async functions as `Future<T>` and checks
`await` expressions with `A201`.

### Module resolution
```pea
import "api.client" as client
print client.value
```
Dotted module names resolve under `modules/` (including `__init__.pea`) or a
dependency declared in `pea.json`. The interpreter, VM, and async VM share the
same resolver, so aliased imports are cached and cycles are reported. Project
analysis exposes a module graph with `M201` unresolved-import and `M203` cycle
diagnostics.

### Safe metaprogramming
```pea
print double 3
```
Pass a `SafeMacro` with a whole-line pattern such as `print double $value` and a
template such as `print $value + $value` to `SafeMacroExpander`. `@name` markers
introduce hygienic temporaries. Expansion is explicit via
`expand_source_macros()` or `compile_source_with_macros()`, and reports
`MG101`-`MG203` issues instead of silently producing unbounded output.

### Resource scopes
```pea
using session = open_session() {
    print session.status
}
```
The binding lives only inside the block. On exit, a `close()` or `dispose()`
method on the value is called automatically, including when the block throws.
Nested `using` blocks close in reverse order, and each scope receives a bounded
resource budget derived from its parent. `scopes.current()` and
`scopes.snapshot()` expose runtime state; project analysis reports `R201` for a
duplicate binding and `R202` for reassigning a `using` binding inside its block.

### Conformance suite
```bash
pea conformance-v2
```
Run a curated set of language-core cases and inspect the JSON report. Runtime
cases must produce identical normalized output on the interpreter and bytecode
VM; other cases check macro expansion, static diagnostic codes, and module
graphs. `run_conformance_suite_v2()` is the equivalent host API, and
`conformance_gate_v2()` returns `PASS` or `FAIL` for CI gates.

### Frozen 3.0 core
```bash
pea freeze
```
The frozen-core gate checks that public API removals have not appeared, the v2
conformance suite passes, the specification is complete for the current release,
the version surfaces agree, and all declared `CORE_SURFACES` remain frozen.
`verify_core_freeze()` provides the same gate to host programs.

### Bytecode optimizer
```bash
pea optimize app.pea --verify
pea optimize app.pea -o app.opt.peac
```
Compile or load a `.peac` artifact and apply constant folding, dead literal
push/pop removal, and unreachable-code removal. The report shows pass counts,
before/after sizes, and a digest. `--verify` executes the original and optimized
modules on the VM and requires identical output and results. Individual passes
can be disabled with `--no-constant-folding`, `--no-dead-push-pop`, and
`--no-unreachable-code`. Host programs can use `optimize_bytecode()`,
`optimize_report()`, and `verify_optimization()` directly.

### Fast interpreter
```bash
pea fast app.pea --verify
pea fast app.pea --benchmark --optimize
```
Run bytecode through the direct-handler fast path when all instructions are
supported; otherwise the standard virtual machine executes the module. The
report includes the selected mode, eligibility, output, and module digest.
`--verify` requires identical VM and fast-path output and results, while
`--benchmark` reports median execution times. Host programs can use
`FastInterpreter`, `fast_path_supported()`, `verify_fast_parity()`, and
`fast_interpreter_report()` directly.

### Bytecode JIT
```bash
pea jit app.pea --verify
pea jit app.pea --benchmark --optimize --threshold 2
```
Profile the module, compile hot loop back-edges into bounded traces, and
specialize integer arithmetic behind type guards. The report shows the profile
totals, selected traces, guarded operations, deoptimizations, output, and a
module digest. `--verify` requires identical VM and JIT output and results.
Guard failures fall back to the standard VM, so unsupported value types and
modules cannot change program meaning. Host programs can use `JITRuntime`,
`profile_execution()`, `select_traces()`, `verify_jit_parity()`, and
`bytecode_jit_report()` directly.

### Native backend
```bash
pea native app.pea --verify
pea native app.pea --benchmark --optimize --emit app.c
```
Lower the supported bytecode subset to deterministic native IR and emit a
self-contained C source artifact. The report shows the artifact format, digest,
instruction count, source byte count, execution mode, output, result, and
optional parity and benchmark data. Modules outside the native subset run
entirely on the standard VM. Host programs can use `compile_native()`,
`NativeRuntime`, `verify_native_parity()`, and `native_report()` directly.

### WASM backend
```bash
pea wasm-backend app.pea --verify
pea wasm-backend app.pea --benchmark --optimize --emit app.wasm --wat app.wat
```
Lower the supported bytecode subset to typed WASM IR wrapped in a custom-section
WebAssembly module. The report shows the artifact format, digest, instruction
count, module and WAT byte counts, execution mode, output, result, and optional
parity and benchmark data. `inspect_wasm_backend()` reads the manifest and IR
from a saved artifact. Modules outside the WASM subset run entirely on the
standard VM. Host programs can use `compile_wasm_backend()`,
`WasmBackendRuntime`, `verify_wasm_backend_parity()`, and
`wasm_backend_report()` directly.

### Parallel runtime, profiler, and performance gates
```bash
pea parallel app.pea --verify --tasks 4 --workers 2
pea profiler app.pea --verify --emit profile.json
pea perf-gate app.pea --iterations 5
```
The parallel runtime executes independent bytecode tasks with copied globals and
a bounded worker pool, then publishes output and results in task order. Async or
module-importing tasks run sequentially on the standard VM. `build_parallel_plan()`
produces a deterministic digest, and `verify_parallel_parity()` requires the
sequential and parallel paths to agree.

The runtime profiler records opcode, function, and source-line counts through VM
instrumentation. `profile_module()` returns a deterministic report with hot spots
and a profile digest; `verify_profile_parity()` checks VM output and result
parity. The 4.0 gate combines timing budgets with parallel/profiler parity,
conformance, and frozen-core evidence through `performance_gate_report()`.

### Optional chaining and null coalescing
```pea
let city = user?.profile?.city ?? "unknown"
let id = request?.params?.id
let ok = handler?.()
```

### Anonymous functions and functional builtins
```pea
let mapped = list(map(function(x){ return x*10 }, [1,2,3]))
let evens = list(filter(function(x){ return x % 2 == 0 }, [1,2,3,4]))
print sorted([3,1,2])
print list(enumerate(["a","b"]))
print list(zip([1,2], [3,4]))
print sum([1,2,3])
print 2 in [1,2,3]
print "ell" in "hello"
print 2 ** 10
print get({"a":1}, "missing", 0)
print safe(function(){ return risky() }, "fallback")
```

### Pattern matching
```pea
let label = match status {
  200, 201 => "ok"
  404 => "not found"
  _ => "error"
}

match value {
  [a, b] => print a + b
  {name} => print name
  _ => print "unknown"
}
```

### Destructuring
```pea
let [a, b] = [10, 20]
let {name, score} = {"name":"Ada", "score":91}
for [k,v] in items({"a":1}) { print k }
for {name} in users { print name }
```

## Web Applications (`web` / `std.web`)

```pea
let app = web.app()
app.enable_cors("*")

function home(req) {
  return web.json({"ok": true, "path": req["path"], "query": req["query"]})
}

app.get("/", home)
app.get("/users/:id", function(req){ return web.json({"id": req["params"]["id"]}) })
app.post("/echo", function(req){ return web.json(req["json"] ?? {}) })

let api = app.group("/api")
api.get("/ping", function(req){ return web.text("pong") })

let spec = web.openapi(app, "Demo", "1.0.0")
print spec
# app.serve("127.0.0.1", 8080)
```

Request fields commonly available: `method`, `path`, `headers`, `query`, `params`, `cookies`, `body`, `json`, `remote_addr`.

Response/helpers: `web.json/html/text/redirect/error/file/sse/response`, `web.ok()`, `web.problem()`, `web.health()`, `web.envelope()`, `web.no_content()`, `web.created()`/`accepted()`, `web.bad_request()`/`unauthorized()`/`forbidden()`/`not_found()`/`method_not_allowed()`/`conflict()`/`gone()`/`unprocessable()`/`too_many_requests()`/`server_error()`/`validation_error()`, `web.not_modified()`, redirects, `web.download()`/`status()`/`negotiate()`, `web.render_template()`/`set_cookie()`/`with_links()`, `web.validate()`/`rate_limit()`/`bearer_auth()`/`api_key_auth()`/`parse_basic_auth()`/`request_id()`/`request_logger()`, `web.query_int()`/`query_bool()`/`method_is()`, `web.json_error()`/`etag()`/`cache_control()`/`security_headers()`/`content_type()`/`merge_headers()`/`parse_query()`/`build_query()`/`url_join()`/`pagination()`. Apps also support `app.group()`, `patch/options`, and CORS (`app.enable_cors()`).

## Data Analysis (`analysis` / `std.analysis`)

```pea
let data = [
  {"name":"Ada","score":91,"team":"a"},
  {"name":"Linus","score":84,"team":"a"},
  {"name":"Grace","score":97,"team":"b"}
]

print analysis.summary(data)
print analysis.profile(data)
print analysis.describe(data, "score")
let top = analysis.query(data, "score", ">", 85)
let by_team = analysis.group_by(data, "team", "score", "mean")
let clean = analysis.fillna([{"v":1},{"v":null}], 0, "v")
let deduped = analysis.drop_duplicates(data)
let renamed = analysis.rename(data, {"name":"person"})
let enriched = analysis.add_column(data, "grade", function(r){ return r["score"] > 90 })
print analysis.to_csv(top)
print analysis.bar_chart(data, "name", "score")
```

Key functions include: `profile`, `describe`, `summary`, `shape`, `correlation`/`corr`, `corr_matrix`, `mean_col`/`sum_col`/`min_col`/`max_col`/`median_col`, `quantile`/`percentile`, `variance`, `std`, `skew`, `kurtosis`, `covariance`, `outliers`, `isna`, `notna`, `clean_missing`, `fillna`, `ffill`, `bfill`, `dropna`, `impute`, `replace_values`, `drop_duplicates`, `rename`, `cast`/`astype`, `select`, `sort_by`, `filter_rows`, `query`, `group_by`, `pivot`, `pivot_wider`, `crosstab`, `one_hot`, `join`/`merge`, `concat`, `add_column`, `assign`, `drop_columns`/`keep_columns`, `round_col`/`abs_col`, `cumsum`, `cummax`/`cummin`/`cumprod`, `normalize`, `sample`, `unique`, `value_counts`, `nunique`, `count`, `duplicated`, `nlargest`/`nsmallest`, `idxmax`/`idxmin`, `head`/`tail`, `between`, `clip`, `mode`, `melt`, `transpose`, `explode`, `where`, `split_column`, `shift`/`lag`/`lead`, `rank`, `pct_change`, `diff`, `rolling_mean`, `rolling_std`, `expanding_mean`/`expanding_sum`/`expanding_max`/`expanding_min`, `ewm_mean`, `zscore`, `histogram`, `cut`, `sample_frac`, `standardize`, `str_transform`/`str_lower`/`str_upper`/`str_strip`/`str_contains`/`str_replace`, `schema`, `from_csv`, `from_json`/`from_jsonl`, `to_json`/`to_jsonl`, `to_records`, `to_dict`, `to_csv`, `to_markdown`, `to_html`, `bar_chart`, `line_chart`.

## Cross-Language Interop (`interop` / `std.interop`)

```pea
print interop.call_python("math", "sqrt", 81)
print interop.run("python", ["--version"])
let rpc = interop.json_rpc("https://example.com/rpc", "method", {"a":1})
let ts = interop.generate_typescript("http://127.0.0.1:8787")
print interop.which("python")
print interop.env("PATH")
```

Capabilities: Python module calls, ctypes/native library loading, process execution, JSON piping (`pipe_json`), HTTP GET/POST, JSON-RPC (`json_rpc`), environment lookup (`env`), `which`, host file/path helpers (`read_text`/`write_text`/`read_json`/`write_json`, `copy_file`, `remove_file` destructive, `list_dir`, `stat`, `hash_file`, `glob`, `exists`, `mkdir_p`, `tempdir`, `basename`, `dirname`, `join_path`, `extname`, `stem`, `is_file`, `is_dir`, `abspath`, `cwd`, `platform`, trusted contexts), and client stub generation for TypeScript/Java/Python.

Security note: interop functions can reach host capabilities. Use them only in trusted environments or behind explicit embedding/runtime controls.

## Standard Library

PeaLang exposes a stable `std.*` namespace (v1.0 manifest) including core modules plus `std.web`, `std.analysis`, `std.interop`, and `std.ux`.

Sensitive operations (filesystem, HTTP, logging, concurrency, process-related host features depending on runtime) require explicit permissions in embedded/controlled contexts.

Inspect modules:
```bash
pea stdlib
```

## Embedding and Runtimes

PeaLang supports interpreter execution, bytecode compilation/VM, embedding APIs, service/sidecar modes, and SDK integrations (Python/FastAPI, Java, TypeScript/React, browser/WASM directions). Use capability controls and resource limits for untrusted extensions.

## Testing

```bash
python -m pytest -q
pea test tests/
pea check .
pea lint .
```

Current experience-layer validation baseline in this workspace: **693 passed, 1 skipped** (see release notes/changelog for details).
