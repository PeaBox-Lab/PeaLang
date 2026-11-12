# Polyglot delivery help

Call Python with `interop.call_python` and `interop.import_python`; run Go programs with `interop.go_run` (guarded by `interop.go_available` and reported by `interop.go_version`); run any process with `interop.run` or `interop.pipe_json`; reach HTTP services with `interop.http_get`, `interop.http_post`, and `interop.json_rpc`; and generate clients with `interop.generate_go`, `interop.generate_typescript`, `interop.generate_java`, and `interop.generate_python_stub`. Prefer JSON at the boundary so records stay portable across runtimes.
