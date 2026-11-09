# PeaLang 1.0.0-experience Release Notes

**Date:** 2026-11-08  
**Base:** PeaLang 0.99.6 security-hardened runtime/tooling foundation  
**Scope:** Comprehensive developer-experience layer for language ergonomics, web apps, data analysis, cross-language interop, and CLI/tooling.

## Summary

This release delivers a broad, practical application-development surface on top of PeaLang's existing interpreter/VM, embedding, security, and integration foundations. It focuses on making PeaLang useful for day-to-day work: building web services, analyzing data, integrating with Python/native/process/HTTP systems, and working efficiently from the CLI.

## Highlights

### 1) Language Ergonomics
- **Comprehensions:** list comprehensions (`[x*2 for x in xs if cond]`) and dict comprehensions (`{k:v for [k,v] in items(d)}`), including destructuring patterns in comprehension targets.
- **Optional chaining / null coalescing:** `obj?.field`, `arr?.[i]`, `fn?.()`, `value ?? fallback`.
- **Anonymous functions:** `function(x){ return x + 1 }`.
- **Pattern matching:** `match` as statement and expression with literal patterns, wildcard `_`, OR patterns (`1,2 => ...`), and guards.
- **Destructuring:** `let [a,b]=...`, `let {name,score}=...`, and destructuring in `for` loops (`for [k,v] in pairs`, `for {name} in users`).
- **Operators & builtins:** `in` / `not in`; builtins including `enumerate`, `zip`, `sorted`, `reversed`, `map`, `filter`, `sum`, `any`, `all`, `min`, `max`, `abs`, `items`, `list`, `dict`, `bool`, `float`.

### 2) Web Applications (`web` / `std.web`)
- Lightweight `web.app()` with routing (`get/post/put/delete/patch/options`), route groups (`app.group("/api")`), middleware, static files, and custom 404/error handlers.
- Request model: method/path/headers/query/params/cookies/body/json/form helpers.
- Response helpers: `web.json/html/text/redirect/error`, `render_template`, `set_cookie`.
- CORS support with preflight handling/header application (`app.enable_cors()`).
- OpenAPI 3.0 generation from registered routes (`web.openapi(app, title, version)`), including path parameter conversion.

### 3) Data Analysis (`analysis` / `std.analysis`)
- Profiling/stats: `profile`, `describe`, `summary`, `correlation`, `corr_matrix`, `quantile`, `outliers`.
- Cleaning/transforms: `clean_missing`, `fillna`, `impute`, `normalize`, `rename`, `drop_duplicates`, `sort_by`, `select`, `filter_rows`, `query`, `add_column`, `cumsum`.
- Reshaping/combining: `group_by`, `pivot`, `join`/`merge`, `concat`, `sample`, `unique`, `value_counts`, `top_values`, `head`, `tail`.
- Output/visualization: `to_csv`, `to_markdown`, `to_html`, `bar_chart`, `line_chart`.

### 4) Cross-Language Interop (`interop` / `std.interop`)
- Python bridge (`call_python`, `import_python`) and native ctypes bridge (`load_library`, `call_native`).
- Process execution (`run`), JSON piping (`pipe_json`), executable discovery (`which`), and environment access (`env`).
- HTTP helpers (`http_get`, `http_post`) and JSON-RPC (`json_rpc`).
- Client/stub generation: `generate_typescript`, `generate_java`, `generate_python_stub`.

### 5) UX, CLI, and Project Templates
- `ux`/`std.ux`: `doctor`, `explain`, `suggest`.
- CLI additions/improvements: `pea eval -e`, `pea lint`, `pea doctor`, `pea templates`, `pea info`, `pea new`, `pea serve-web`, template-aware `pea init --template`.
- Templates: `default`, `webapp`, `analysis`, `library`, `interop`.

## Compatibility and Security Notes
- Builds on the **0.99.6** security baseline (SSH/SFTP fail-closed behavior, signing hardening, type-system ReDoS protections as documented for 0.99.6).
- Interop/process/native features can access host capabilities; use only in trusted contexts or with explicit runtime controls/permissions.
- Existing security, capability, and embedding controls remain the recommended boundary for untrusted extensions.

## Validation

```bash
python -m pytest -q
```

**Result:** 693 passed, 1 skipped.

New/updated coverage includes: language ergonomics (comprehensions, `in`/`not in`, `**`, match/destructuring, helpers/builtins), web routing/groups/CORS/OpenAPI/validation/SSE/file/auth/cache/status/redirect/security/health/envelope/validation/accepts helpers, analysis profiling/transforms/stats/IO/charts/melt/zscore/histogram/cut/shape/string/reshape/timeseries/encoding/columns/aggregates/jsonl/expanding, interop (Python/native/process/HTTP/JSON-RPC/env/files/paths/copy/hash/walk/temp/host-info/codegen), UX/templates, and CLI (`eval -e/-f`, `check/lint --json`, `analyze`, `web-openapi`/`openapi`, `hash`, `tree`, `env`, `version --json`, `quickstart`, `info`, `new`, `serve-web`, templates/doctor).

## Additional Batch Notes (v112)
- **Builtins:** `gcd`, `lcm`, `sign`, `is_even`/`is_odd`, `lerp`, `rotate`, `interleave`, `windows` (sliding), `dedupe_by`, `assoc`, `dissoc`, `rename_keys`, `format_number`, `between` (scalar).
- **Analysis:** `rolling_std`, `expanding_sum`/`expanding_max`/`expanding_min`, `sample_frac`, `ewm_mean`, `standardize`.
- **Web:** `accepts`, `accepts_json`, `accepts_html`, `no_cache`, `vary`, `link_header`.
- **Interop (host, trusted):** `cpu_count`, `hostname`, `user`, `pid`.
- **CLI/Templates:** `pea env <NAME>` / `--keys`, `automation` template.

## Additional Batch Notes (v111)
- **Builtins:** `group_by` (list), `frequencies`, `scan`, `hex_encode`/`hex_decode`, `ensure_str`/`ensure_int`/`ensure_float`, `pipe`, `apply`.
- **Analysis:** `mean_col`/`sum_col`/`min_col`/`max_col`/`median_col`, `skew`, `kurtosis`, `expanding_mean`, `corr` (alias), `to_jsonl`/`from_jsonl`.
- **Web:** `validation_error`, `content_type`, `merge_headers`, `query_int`/`query_bool`, `api_key_auth`, `method_is`.
- **Interop (host, trusted):** `env_all`, `expanduser`, `expandvars`, `touch`, `head_file`/`tail_file`.
- **CLI/Templates:** `pea tree [path]`, `pea version --json`, `etl` project template.

## Additional Batch Notes (v110)
- **Builtins:** `min_by`, `max_by`, `without`, `xor`, `zip_object`, `ensure_list`, `ensure_dict`, `size`, `random_choice`, `sample_list`, `clone`, `deep_clone`, `deep_equal`, `nth`, `initial`, `rest`.
- **Analysis:** `drop_columns`, `keep_columns`, `assign`, `round_col`, `abs_col`, `variance`, `std`, `covariance`, `idxmax`, `idxmin`.
- **Web/UX:** `web.health`, `web.envelope`, `web.with_links`, `web.negotiate`, `web.request_logger`; `ux.quickstart`, `ux.commands`.
- **Interop (host, trusted):** `walk`, `readlines`, `writelines`, `tempfile`.
- **CLI/Templates:** `pea openapi` alias, `pea quickstart`, `api` project template.

## Additional Batch Notes (v109)
- **Builtins:** `has_path`, `set_path` (immutable), `map_values`, `map_keys`, `pick_by`, `omit_by`, `shuffle`, `product`, `median`, `parse_int`, `parse_float`, `strip_prefix`, `strip_suffix`, `sha256`, `url_encode`, `url_decode`, `html_escape`, `title_case`, `center`.
- **Analysis:** `shift`, `lag`, `lead`, `cummax`, `cummin`, `cumprod`, `replace_values`, `one_hot`, `split_column`, `percentile` (alias).
- **Web:** `bad_request`, `server_error`, `not_modified`, `moved_permanently`, `see_other`, `temporary_redirect`, `permanent_redirect`, `security_headers`, `parse_query`, `build_query`.
- **Interop (host, trusted; `remove_file` destructive):** `copy_file`, `remove_file`, `list_dir`, `stat`, `hash_file`.
- **CLI:** `pea web-openapi <file> [--title T] [--version V]`, `pea hash <file> [--algo sha256]`.

## Additional Batch Notes (v108)
- **Builtins:** `is_empty`, `compact`, `defaults`, `invert`, `to_pairs`, `from_pairs`, `sum_by`, `avg`, `capitalize`, `snake_case`, `kebab_case`, `slugify`, `truncate`, `union`, `intersection`, `difference`.
- **Analysis:** `explode`, `where`, `shape`, `isna`, `notna`, `astype` (alias), `to_records`, `to_dict`, `str_transform`/`str_lower`/`str_upper`/`str_strip`/`str_contains`/`str_replace`.
- **Web:** `unauthorized`, `forbidden`, `conflict`, `too_many_requests`, `gone`, `unprocessable`, `download`, `status`.
- **Interop (host, trusted):** `join_path`, `extname`, `stem`, `is_file`, `is_dir`, `abspath`, `cwd`, `platform`.
- **CLI:** `pea check --json` / `pea lint --json`, `pea analyze <file.json|csv> [--json] [--head N]`.

## Additional Batch Notes (v107)
- **Builtins:** `get_path`, `deep_merge`, `take`, `drop`, `partition`, `count_by`, `first`, `last`.
- **Analysis:** `duplicated`, `nlargest`, `nsmallest`, `pivot_wider`.
- **Web:** `not_found`, `method_not_allowed`, `url_join`.
- **Interop (host, trusted):** `glob`, `exists`, `mkdir_p`, `tempdir`, `basename`, `dirname`.

## Additional Batch Notes (v106)
- **Builtins:** type predicates (`is_null/is_list/is_dict/is_string/is_number/is_bool`), `identity`, `tap`, `pad_start`, `pad_end`, `lines`, `words`, `floor`, `ceil`, `log`, `exp`, `pow`.
- **Analysis:** `ffill`, `bfill`, `dropna`, `cast`, `crosstab`.
- **Web:** `ok`, `problem` (RFC7807-style), `pagination`, `parse_basic_auth`.
- **Interop:** `read_text`, `write_text`, `read_json`, `write_json` (host access; use in trusted contexts).
- **CLI:** `pea test -k` filter alias.

## Additional Batch Notes (v105)
- **Builtins:** `coalesce`, `repeat`, `times`, `find`, `find_index`, `pluck`, `index_by`, `sort_by` (list by key).
- **Analysis:** `zscore`, `histogram`, `cut`.
- **Web:** `cache_control`, `basic_auth`, `no_content`, `created`, `accepted`.
- **CLI:** `pea eval -f <file>`.

## Additional Batch Notes (v104)
- **Builtins:** `chunk`, `flatten`, `uniq`, `pick`, `omit`, `clamp`, `uuid`, `randint`, `b64encode`, `b64decode`, `now_iso`.
- **Analysis:** `rank`, `pct_change`, `diff`, `rolling_mean`, `schema`.
- **Web:** `request_id` middleware, `json_error`, `etag`.
- **CLI:** `pea new`, `pea serve-web <file>` (best-effort).

## Additional Batch Notes (v103)
- **`**` power operator** added; `//` is intentionally kept as line-comment syntax for compatibility (use `int(a/b)` for floor division).
- **Builtins/helpers:** `get`, `has`, `merge`, `push`, `pop`, `slice`, `contains`, `trim`, `replace`, `starts_with`, `ends_with`, `json_parse`, `json_dump`, `safe`, `now_ms`.
- **Web:** route groups, `patch`/`options`, CORS preflight, `validate`, `file`, `sse`, `response`, `rate_limit`, `bearer_auth`.
- **Analysis:** `from_csv`/`from_json`/`to_json`, `between`, `clip`, `mode`, `nunique`, `count`, `melt`, `transpose`.
- **Interop/CLI:** `json_rpc`, `pipe_json`, `env`; `pea eval -e`, `pea info`.

## Upgrade/Adoption Guidance
- Start with `pea doctor` and `pea templates`.
- For a web service: `pea init myapi --template webapp`.
- For data workflows: use `analysis.*` / `std.analysis.*` and `pea eval -e` for quick checks.
- For host integration: prefer the embedding/service APIs and explicit capability controls; use `interop` only where host access is intended and trusted.