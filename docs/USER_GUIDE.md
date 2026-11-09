# PeaLang User Guide

This guide covers the PeaLang 1.0.0-experience layer on top of the 0.99.6 security baseline.

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
| `pea analyze <file.json|csv> [--json] [--head N]` | Profile a JSON/CSV dataset (analysis) |
| `pea web-openapi <file.pea> [--title T] [--version V]` | Extract OpenAPI from a file defining `app` |
| `pea hash <file> [--algo sha256]` | Compute file hash |
| `pea typecheck <paths...>` | Optional type checking |
| `pea semantic <paths...>` | Semantic analysis |
| `pea doctor` | Environment and dependency diagnostics |
| `pea templates` | List project templates |
| `pea init [path] [--name N] [--template T]` | Create a project (`default`, `webapp`, `analysis`, `library`, `interop`) |
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

Response/helpers: `web.json/html/text/redirect/error/file/sse/response`, `web.ok()`, `web.problem()`, `web.no_content()`, `web.created()`, `web.accepted()`, `web.bad_request()`, `web.unauthorized()`, `web.forbidden()`, `web.not_found()`, `web.method_not_allowed()`, `web.conflict()`, `web.gone()`, `web.unprocessable()`, `web.too_many_requests()`, `web.server_error()`, `web.not_modified()`, redirects (`moved_permanently`/`see_other`/`temporary_redirect`/`permanent_redirect`), `web.download()`, `web.status()`, `web.render_template()`, `web.set_cookie()`, `web.validate()`, `web.rate_limit()`, `web.bearer_auth()`, `web.parse_basic_auth()`, `web.request_id()`, `web.json_error()`, `web.etag()`, `web.cache_control()`, `web.basic_auth()`, `web.pagination()`, `web.security_headers()`, `web.parse_query()`/`web.build_query()`, `web.url_join()`. Apps also support `app.group()`, `patch/options`, and CORS (`app.enable_cors()`).

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

Key functions include: `profile`, `describe`, `summary`, `shape`, `correlation`, `corr_matrix`, `quantile`/`percentile`, `outliers`, `isna`, `notna`, `clean_missing`, `fillna`, `ffill`, `bfill`, `dropna`, `impute`, `replace_values`, `drop_duplicates`, `rename`, `cast`/`astype`, `select`, `sort_by`, `filter_rows`, `query`, `group_by`, `pivot`, `pivot_wider`, `crosstab`, `one_hot`, `join`/`merge`, `concat`, `add_column`, `cumsum`, `cummax`/`cummin`/`cumprod`, `normalize`, `sample`, `unique`, `value_counts`, `nunique`, `count`, `duplicated`, `nlargest`, `nsmallest`, `head`, `tail`, `between`, `clip`, `mode`, `melt`, `transpose`, `explode`, `where`, `split_column`, `shift`/`lag`/`lead`, `rank`, `pct_change`, `diff`, `rolling_mean`, `zscore`, `histogram`, `cut`, `str_transform`/`str_lower`/`str_upper`/`str_strip`/`str_contains`/`str_replace`, `schema`, `from_csv`, `from_json`, `to_json`, `to_records`, `to_dict`, `to_csv`, `to_markdown`, `to_html`, `bar_chart`, `line_chart`.

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

Current experience-layer validation baseline in this workspace: **671 passed, 1 skipped** (see release notes/changelog for details).
