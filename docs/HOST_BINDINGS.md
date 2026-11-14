# Native FFI, plugin SDK, and multi-language host bindings (v1.9.0)

PeaLang provides bidirectional FFI, host SDK scaffolding, and OpenAPI importer.

## Host function registration

- `register_host_function(name, module, function, arg_types, return_type)` — register host function

## Export decorators

- `generate_python_export(func_name, arg_types, return_type)` — Python @pea_export
- `generate_typescript_export(func_name, arg_types, return_type)` — TypeScript @peaExport
- `generate_java_export(func_name, arg_types, return_type)` — Java @PeaExport

## Host SDK scaffolding

- `scaffold_go_sdk(target_dir)` — scaffold Go SDK
- `scaffold_node_sdk(target_dir)` — scaffold Node.js/TypeScript SDK

## OpenAPI/GraphQL importer

- `import_openapi(spec)` — parse OpenAPI spec
- `generate_connector_package(imported)` — generate PeaLang connector package