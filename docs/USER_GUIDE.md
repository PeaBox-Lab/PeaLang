# PeaLang User Guide

This guide covers the PeaLang 3.1.61 release (unified versioning; supersedes the 1.0.0-experience and 0.99.6 baselines).

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
| `pea lsp <file.pea> [--check] [--symbols] [--hover LINE CHAR]` | Query LSP v2 diagnostics and symbols |
| `pea dap-v2 <file.pea> [--check] [--breakpoint LINE]` | Run a deterministic DAP v2 session |
| `pea lint-v3 <path...> [--check] [--fail-on-warning]` | Report deterministic linter v3 findings |
| `pea test-v2 <path...> [--check] [--fail-fast]` | Run deterministic test framework v2 cases |
| `pea build-v2 <root> [--check] [--state FILE]` | Plan an incremental build with stable digests |
| `pea docs-v2 <root> [--check] [--state FILE]` | Inventory versioned documentation with stable digests |
| `pea migrate-v2 <root> [--check] [--state FILE]` | Plan migration assistants with stable digests |
| `pea templates-v2 <root> [--check] [--state FILE]` | Inventory project templates with stable digests |
| `pea devex-v2 <root> [--check] [--state FILE]` | Gate developer-experience evidence with stable digests |
| `pea finance-pack <root> [--check] [--state FILE]` | Gate finance sector-pack evidence with stable digests |
| `pea data-pack <root> [--check] [--state FILE]` | Gate data science sector-pack evidence with stable digests |
| `pea web-pack <root> [--check] [--state FILE]` | Gate frontend web sector-pack evidence with stable digests |
| `pea android-pack <root> [--check] [--state FILE]` | Gate Mobile (Android) sector-pack evidence with stable digests |
| `pea ios-pack <root> [--check] [--state FILE]` | Gate Mobile (iOS) sector-pack evidence with stable digests |
| `pea game-pack <root> [--check] [--state FILE]` | Gate Game Development sector-pack evidence with stable digests |
| `pea embedded-pack <root> [--check] [--state FILE]` | Gate Embedded / IoT / OS sector-pack evidence with stable digests |
| `pea cloud-pack <root> [--check] [--state FILE]` | Gate Cloud Infrastructure / DevOps sector-pack evidence with stable digests |
| `pea fmt-v3 <path...> [--check] [--write]` | Report or apply formatter v3 changes |
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

### Language server v2

```bash
pea lsp --capabilities
pea lsp app.pea --check --symbols --emit lsp.json
```

`LspV2Server` is additive to the v1 `LSPServer`. It advertises versioned
capabilities, keeps documents in a deterministic `DocumentStore`, and supports
full or incremental `didChange` edits. Diagnostics, document and workspace
symbols, hover, completion, definition, references, rename, formatting, folding
ranges, inlay hints, and semantic tokens are all pure, inspectable functions.
`lsp_v2_report()` summarizes the capability set and open documents with a stable
digest; `lsp_v2_gate()` recomputes the PASS/FAIL decision for CI checks.

### Debug adapter v2

```bash
pea dap-v2 --capabilities
pea dap-v2 app.pea --breakpoint 3 --check --emit dap.json
```

`DapV2Session` is additive to the existing `dap` and `vm-dap` servers. It
launches bytecode on the VM, applies verified breakpoints, and resumes or steps
while recording deterministic events and snapshot fingerprints. Conditions such
as `x == 1` and `hits == 2` are evaluated against stable local values; built-in
VM helpers and host-specific paths are excluded from fingerprints and digests.
Stack traces, scopes, variables, evaluation, exception info, threads, and
disconnect are available as reviewable responses. `dap_v2_report()` summarizes
the session and `dap_v2_gate()` recomputes the PASS/FAIL decision for CI checks.

### Formatter v3

```bash
pea fmt-v3 --capabilities
pea fmt-v3 app.pea --check --indent 2 --emit fmt.json
pea fmt-v3 app.pea --write
```

`format_source_v3()` is additive to `pea fmt` and `PeaFormatter`. A
`FormatProfile` validates indentation, line length, brace style, and EOF newline
settings. Formatting preserves comments and string content while normalizing
whitespace, operators, commas, braces, and blank lines around recomputed brace
indentation. Each `FormatResult` carries a unified diff, long-line numbers, an
idempotence check, and a bytecode fingerprint comparison. `pea fmt-v3 --check`
requires formatted input without applying changes, while `--write` applies them;
`formatter_v3_gate()` provides the CI-ready decision.

### Linter v3

```bash
pea lint-v3 --capabilities
pea lint-v3 app.pea --check --max-complexity 8 --emit lint.json
pea lint-v3 app.pea --check --fail-on-warning
```

`lint_source_v3()` is additive to `pea lint` and `PeaLinter`. A `LintProfileV3`
validates thresholds, rule toggles, and strict warning policy before analysis.
Each `LintDiagnosticV3` carries a stable rule code, severity, position, message,
and optional fix hint; diagnostics are sorted by position and rule. Line rules
cover long lines, trailing whitespace, and TODO/FIXME markers outside strings,
while AST rules cover naming, debug prints, cyclomatic complexity, unreachable
statements, and parse errors. `lint_v3_report()` produces a recomputable digest
that excludes source names, and `lint_v3_gate()` recomputes PASS/FAIL with
optional failure on warnings.

### Test framework v2

```bash
pea test-v2 --capabilities
pea test-v2 tests --check --filter auth --emit tests.json
pea test-v2 tests --check --fail-fast --max-failures 0
```

`run_test_source_v2()` is additive to `pea test` and the native testing helpers.
A `TestProfileV2` validates the text filter, fail-fast policy, and allowed
failure count before execution. Each `TestCaseV2` carries a stable ID derived
from the describe block, test name, and source line; cases are sorted
deterministically, and error text is normalized so raw host paths do not enter
the report. `test_v2_report()` summarizes results with a digest that excludes
elapsed timings, and `test_v2_gate()` recomputes PASS/FAIL from the reported
failure count and profile.

### Incremental build system v2

```bash
pea build-v2 --capabilities
pea build-v2 . --check --state build-state.json --emit build.json
pea build-v2 . --check --write-state --fail-on-dirty
```

`plan_build_v2()` is additive to `pea build`. A `BuildProfileV2` validates the
file limit, test inclusion, import checks, and dirty-failure policy before
planning. Each `BuildNodeV2` carries a relative path, a content digest, resolved
import dependencies, a clean/stale state, and reasons; nodes are ordered
topologically, and stale state propagates to importers. Missing imports and
dependency cycles become stable issue codes, while `write_build_state_v2()`
persists digests without absolute host paths. `build_v2_report()` summarizes
plans with a recomputable digest, and `build_v2_gate()` recomputes PASS/FAIL from
the reported error count, dirty count, and profile.

### Versioned docs

```bash
pea docs-v2 --capabilities
pea docs-v2 . --check --state docs-state.json --emit docs.json
pea docs-v2 . --check --write-state --fail-on-drift
```

`plan_docs_v2()` is additive to `pea docs`. A `DocsProfileV2` validates the file
limit, release-note inclusion, link checks, current version, and drift-failure
policy before inventorying. Each `DocEntryV2` carries a relative path, a content
digest, extracted version references, internal links, a clean/stale state, and
reasons; entries are sorted by path. Stale version references and broken links
become stable issue codes, while `write_docs_state_v2()` persists digests without
absolute host paths. `docs_v2_report()` summarizes plans with a recomputable
digest, and `docs_v2_gate()` recomputes PASS/FAIL from the reported error count,
drift count, and profile.

### Migration assistants

```bash
pea migrate-v2 --capabilities
pea migrate-v2 . --check --state migrate-state.json --emit migrate.json
pea migrate-v2 . --check --write-state --fail-on-dirty
```

`plan_migration_v2()` is additive to `pea migrate`. A `MigrationProfileV2`
validates the migration limit, test-migration inclusion, import checks, current
version, and dirty-failure policy before planning. Each `MigrationNodeV2`
carries a relative path, a content digest, imported names, provided script
names, resolved dependencies, a clean/stale state, and reasons; nodes are
ordered topologically, and dirty state propagates to importers. Missing scripts,
dependency cycles, and limit overruns become stable issue codes, while
`write_migration_state_v2()` persists digests without absolute host paths.
`migration_v2_report()` summarizes plans with a recomputable digest, and
`migration_v2_gate()` recomputes PASS/FAIL from the reported error count, dirty
count, and profile.

### Project templates v2

```bash
pea templates-v2 --capabilities
pea templates-v2 . --check --state template-state.json --emit templates.json
pea templates-v2 . --check --write-state --fail-on-drift
```

`plan_project_templates_v2()` is additive to `pea scaffold` and `pea templates`.
A `TemplateProfileV2` validates the template limit, community inclusion,
dependency checks, current version, and drift-failure policy before planning.
Each `TemplateNodeV2` carries a relative path, a manifest digest, name, version,
sorted file set, required names, entrypoints, resolved dependencies, a
clean/stale state, and reasons; nodes are ordered topologically, and drift
propagates to dependent templates. Missing dependencies, dependency cycles,
invalid manifests, entrypoints missing from files, and limit overruns become
stable issue codes, while `write_template_state_v2()` persists digests without
absolute host paths. `templates_v2_report()` summarizes plans with a
recomputable digest, and `templates_v2_gate()` recomputes PASS/FAIL from the
reported error count, drift count, and profile.

### Developer experience v2

```bash
pea devex-v2 --capabilities
pea devex-v2 . --check --state devex-state.json --emit devex.json
pea devex-v2 . --check --write-state --fail-on-incomplete
```

`plan_devex_v2()` is the Wave 3 capstone and is additive to the existing editor,
debug, format, lint, test, build, docs, migration, and template tools. A
`DevExProfileV2` validates the tool limit, experimental inclusion, evidence
checks, current version, and incomplete-failure policy before planning. Each
`DevExToolV2` carries a relative path, a manifest digest, name, version, format,
sorted evidence paths, required names, checks, resolved dependencies, a
clean/stale state, and reasons; tools are ordered topologically, and incomplete
state propagates to dependent tools. Missing dependencies, dependency cycles,
invalid manifests, missing evidence artifacts, and limit overruns become stable
issue codes, while `write_devex_state_v2()` persists digests without absolute
host paths. `devex_v2_report()` summarizes plans with a recomputable digest, and
`devex_v2_gate()` recomputes PASS/FAIL from the reported error count, incomplete
count, and profile.

### Enterprise/Finance/Banking sector pack

```bash
pea finance-pack --capabilities
pea finance-pack . --check --state finance-state.json --emit finance.json
pea finance-pack . --check --write-state --fail-on-incomplete
```

`plan_finance_pack()` opens Wave 4 and is additive to the existing SQL,
connector, capability, and audit layers. A `FinanceProfileV2` validates the
artifact limit, sandbox inclusion, interop/audit contract checks, current
version, and incomplete-failure policy before planning. Each
`FinanceArtifactV2` carries a relative path, a manifest digest, name, version,
kind, sorted evidence paths, sorted required names, sorted contracts, resolved
dependencies, a clean/stale state, and reasons; artifacts are ordered
topologically, and incomplete state propagates to dependent artifacts. Missing
dependencies, dependency cycles, invalid manifests, missing evidence artifacts,
interop bindings without contracts, and reference apps without audit rules
become stable issue codes, while `write_finance_state_v2()` persists digests
without absolute host paths. `finance_pack_report()` summarizes plans with a
recomputable digest, and `finance_pack_gate()` recomputes PASS/FAIL from the
reported error count, incomplete count, and profile.

### Data Science / AI / ML sector pack

```bash
pea data-pack --capabilities
pea data-pack . --check --state data-state.json --emit data.json
pea data-pack . --check --write-state --fail-on-incomplete
```

`plan_data_pack()` continues Wave 4 and is additive to the existing analysis,
timeseries, forecasting, AI/ML, Jupyter, and serving runtime layers. A
`DataProfileV2` validates the workflow limit, preview inclusion, parity and
benchmark checks, current version, and incomplete-failure policy before
planning. Each `DataWorkflowV2` carries a relative path, a manifest digest,
name, version, kind, sorted evidence paths, sorted required names, sorted
published metrics, resolved dependencies, a clean/stale state, and reasons;
workflows are ordered topologically, and incomplete state propagates to
dependent workflows. Missing dependencies, dependency cycles, invalid
manifests, missing evidence artifacts, pipelines without parity suites, and
models without published benchmarks become stable issue codes, while
`write_data_state_v2()` persists digests without absolute host paths.
`data_pack_report()` summarizes plans with a recomputable digest, and
`data_pack_gate()` recomputes PASS/FAIL from the reported error count,
incomplete count, and profile.

### Frontend Web sector pack

```bash
pea web-pack --capabilities
pea web-pack . --check --state web-state.json --emit web.json
pea web-pack . --check --write-state --fail-on-incomplete
```

`plan_web_pack()` continues Wave 4 and is additive to the browser SDK, React
SDK, TypeScript SDK, templates, and web ecosystem. A `WebProfileV2` validates
the app limit, canary inclusion, DSL and interop checks, current version, and
incomplete-failure policy before planning. Each `WebAppV2` carries a relative
path, a manifest digest, name, version, kind, sorted evidence paths, sorted
declared bridges, sorted required names, resolved dependencies, a clean/stale
state, and reasons; apps are ordered topologically, and incomplete state
propagates to dependent apps. Missing dependencies, dependency cycles, invalid
manifests, missing evidence artifacts, web apps without state models, and web
apps without TypeScript interop bridges become stable issue codes, while
`write_web_state_v2()` persists digests without absolute host paths.
`web_pack_report()` summarizes plans with a recomputable digest, and
`web_pack_gate()` recomputes PASS/FAIL from the reported error count,
incomplete count, and profile.

### Mobile (Android) sector pack

```bash
pea android-pack --capabilities
pea android-pack . --check --state android-state.json --emit android.json
pea android-pack . --check --write-state --fail-on-incomplete
```

`plan_android_pack()` continues Wave 4 and is additive to the host bindings,
Java client sidecar, and VM embedding foundations. An `AndroidProfileV2`
validates the app limit, preview inclusion, lifecycle/JVM/Gradle checks, current
version, and incomplete-failure policy before planning. Each `AndroidAppV2`
carries a relative path, a manifest digest, name, version, kind, sorted evidence
paths, sorted platform bindings, sorted required names, resolved dependencies, a
clean/stale state, and reasons; apps are ordered topologically, and incomplete
state propagates to dependent apps. Missing dependencies, dependency cycles,
invalid manifests, missing evidence artifacts, sample apps without lifecycle
bindings, sample apps without Kotlin/JVM bridges, and sample apps without Gradle
plugins become stable issue codes, while `write_android_state_v2()` persists
digests without absolute host paths. `android_pack_report()` summarizes plans
with a recomputable digest, and `android_pack_gate()` recomputes PASS/FAIL from
the reported error count, incomplete count, and profile.

### Mobile (iOS) sector pack

```bash
pea ios-pack --capabilities
pea ios-pack . --check --state ios-state.json --emit ios.json
pea ios-pack . --check --write-state --fail-on-incomplete
```

`plan_ios_pack()` continues Wave 4 and is additive to the host bindings,
Java client sidecar, and VM embedding foundations. An `IOSProfileV2` validates
the app limit, preview inclusion, Swift/Objective-C/XCFramework/Xcode checks,
current version, and incomplete-failure policy before planning. Each
`IOSAppV2` carries a relative path, a manifest digest, name, version, kind,
sorted evidence paths, sorted platform bindings, sorted required names, resolved
dependencies, a clean/stale state, and reasons; apps are ordered topologically,
and incomplete state propagates to dependent apps. Missing dependencies,
dependency cycles, invalid manifests, missing evidence artifacts, sample apps
without Swift bridges, sample apps without Objective-C compatibility layers,
sample apps without XCFrameworks, and sample apps without Xcode templates become
stable issue codes, while `write_ios_state_v2()` persists digests without
absolute host paths. `ios_pack_report()` summarizes plans with a recomputable
digest, and `ios_pack_gate()` recomputes PASS/FAIL from the reported error count,
incomplete count, and profile.

### Game Development sector pack

```bash
pea game-pack --capabilities
pea game-pack . --check --state game-state.json --emit game.json
pea game-pack . --check --write-state --fail-on-incomplete
```

`plan_game_pack()` continues Wave 4 and is additive to the host bindings,
Java client sidecar, and VM embedding foundations. A `GameProfileV2` validates
the game limit, preview inclusion, runtime/ECS/engine/hot-reload/input/render
checks, current version, and incomplete-failure policy before planning. Each
`GameAppV2` carries a relative path, a manifest digest, name, version, kind,
sorted evidence paths, sorted platform bindings, sorted required names, resolved
dependencies, a clean/stale state, and reasons; games are ordered topologically,
and incomplete state propagates to dependent games. Missing dependencies,
dependency cycles, invalid manifests, missing evidence artifacts, sample games
without native/WASM runtimes, ECS bindings, Unity/Unreal bridges, hot reload,
input APIs, or render APIs become stable issue codes, while
`write_game_state_v2()` persists digests without absolute host paths.
`game_pack_report()` summarizes plans with a recomputable digest, and
`game_pack_gate()` recomputes PASS/FAIL from the reported error count, incomplete
count, and profile.

### Embedded / IoT / OS sector pack

```bash
pea embedded-pack --capabilities
pea embedded-pack . --check --state embedded-state.json --emit embedded.json
pea embedded-pack . --check --write-state --fail-on-incomplete
```

`plan_embedded_pack()` continues Wave 4 and is additive to the host bindings,
Java client sidecar, and VM embedding foundations. An `EmbeddedProfileV2`
validates the firmware limit, preview inclusion, native/C-ABI/RTOS/static/bus/
safety/memory/signature checks, current version, and incomplete-failure policy
before planning. Each `EmbeddedAppV2` carries a relative path, a manifest digest,
name, version, kind, sorted evidence paths, sorted platform bindings, sorted
required names, resolved dependencies, a clean/stale state, and reasons; firmware
is ordered topologically, and incomplete state propagates to dependent firmware.
Missing dependencies, dependency cycles, invalid manifests, missing evidence
artifacts, firmware demos without native profiles, C ABIs, RTOS bindings, static
binaries, GPIO/I2C/SPI/CAN APIs, safety audits, bounded-memory bindings, or
signed-update bindings become stable issue codes, while
`write_embedded_state_v2()` persists digests without absolute host paths.
`embedded_pack_report()` summarizes plans with a recomputable digest, and
`embedded_pack_gate()` recomputes PASS/FAIL from the reported error count,
incomplete count, and profile.

### Cloud Infrastructure / DevOps sector pack

```bash
pea cloud-pack --capabilities
pea cloud-pack . --check --state cloud-state.json --emit cloud.json
pea cloud-pack . --check --write-state --fail-on-incomplete
```

`plan_cloud_pack()` completes Wave 4 and is additive to the package lifecycle CLI
and `frameworks.py` scaffolds. A `CloudProfileV2` validates the deployment limit,
preview inclusion, container/orchestration/pipeline/observability/IAM/source/
lockfile/signature/drift checks, current version, and incomplete-failure policy
before planning. Each `CloudAppV2` carries a relative path, a manifest digest,
name, version, kind, sorted evidence paths, sorted platform bindings, sorted
required names, resolved dependencies, a clean/stale state, and reasons;
deployments are ordered topologically, and incomplete state propagates to
dependent deployments. Missing dependencies, dependency cycles, invalid
manifests, missing evidence artifacts, deployments without container images,
Kubernetes manifests, CI pipelines, observability, IAM policies,
Go/Python/Bash/CDK/Terraform source bridges, lockfiles, signed packages, or drift
checks become stable issue codes, while `write_cloud_state_v2()` persists digests
without absolute host paths. `cloud_pack_report()` summarizes plans with a
recomputable digest, and `cloud_pack_gate()` recomputes PASS/FAIL from the
reported error count, incomplete count, and profile.

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
