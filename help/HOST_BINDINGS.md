# Native FFI, plugin SDK, and multi-language host bindings (v1.9.0)

PeaLang provides bidirectional FFI, host SDK scaffolding, and OpenAPI importer.

## Key functions

- `analysis.register_host_function(name, module, function, arg_types, return_type)` — register host function
- `analysis.generate_python_export(func_name, arg_types, return_type)` — Python export
- `analysis.generate_typescript_export(func_name, arg_types, return_type)` — TS export
- `analysis.generate_java_export(func_name, arg_types, return_type)` — Java export
- `analysis.scaffold_go_sdk(target_dir)` — Go SDK
- `analysis.scaffold_node_sdk(target_dir)` — Node SDK
- `analysis.import_openapi(spec)` — OpenAPI importer
- `analysis.generate_connector_package(imported)` — connector package