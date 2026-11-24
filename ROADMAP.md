## 2.41.0 - Phase 34: Standard Library Completion (2026-11-24)
- Add 9 new standard library modules: std.sql, std.cache, std.uuid, std.cli, std.config, std.template, std.serialize, std.graph, std.queue, std.env
- Fix std.config JSON/TOML parse (was using undefined `p` instead of `path`)
- Fix std.template render_file (same undefined `p` bug)
- Fix std.queue priority queue (was pushing max-heap; now max-priority pops first)
- Add stdlib.Namespace.__getattribute__ so attribute access falls back to dict keys
- Add 10 test files covering each new module
- Update CHANGELOG.md with Phase 34 entry (1353 tests pass)

### Phase 35: Language Extension Type System (2.37.0)
- **`pealang/extension_type_system.py`**: New module integrating extension types with the type system.
- **`pea ext type <name>`**: CLI command to show extension type details and available methods.
- **Extension types**: Custom types registered via ExtensionRegistry can be used in PeaLang with method calls, type checking, and constructor support.
- Added tests: test_extension_type_system, test_pea_ext_type_info, test_pea_ext_type_cli.
- All 1353 tests pass with type system integration.

## 2.38.0 - Phase 36: Marketplace CLI Extension (2026-11-26)
- Add `pea market register <name> <version> ...` CLI command to create marketplace entries
- Add `pea market download <name>` CLI command to record library downloads
- Extend `create_marketplace()` usage for CLI subcommands

### Phase 37: Library Install & Runtime (2.39.0)
- Add `pea install <name>[@version]` CLI command to install libraries from registry into project
- Add `install_remote()` function in package_manager for remote library installation
- Add tests: test_pea_install_cli, test_pea_install_remote
- All 1358 tests pass with library install functionality

## 2.39.0 - Phase 38: Library Publishing Workflow (2026-11-28)
- Add `pea publish` CLI command for library publishing
- Add `publish()` function in package_manager
- Add tests: test_pea_publish_cli, test_pea_publish_remote, test_pea_publish_invalid_path
- All 1361 tests pass with library publishing functionality

## 2.40.0 - Phase 39: Library Quality Gates (2026-11-29)
- Add `pea quality` CLI command for library quality checks
- Add `quality_check()` function in package_manager
- Add tests: test_pea_quality_cli, test_quality_check_function, test_quality_check_valid_project
- All 1364 tests pass with library quality gates

### Phase 40: ...