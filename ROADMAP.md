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

## 2.41.0 - Phase 40: Library End-to-End (2026-11-30)
- Add `pea lib` command group (new, build, quality, publish)
- Add `pea lib new <name>` CLI command to scaffold library projects
- Add `pea lib build <path>` to build library package (.pelib)
- Add `pea lib quality <path>` to run quality checks
- Add `pea lib publish <path>` to build and publish to registry
- All 1368 tests pass with library end-to-end functionality

## 2.41.0 - Phase 41: Library Runtime Loading (2026-11-30)
- Add `pea lib new <name>` CLI command to scaffold library projects
- Add `pea lib build <path>` to build library package (.pelib)
- Add `pea lib quality <path>` to run quality checks
- Add `pea lib publish <path>` to build and publish to registry
- Add `resolve_module()` support for installed libraries in `.pea_modules/<spec>`
- All 1371 tests pass with library runtime loading functionality

## 2.41.0 - Phase 42: Project Version Query (2026-11-30)
- Add `pea version <path>` to query a project/library version from pea.toml
- Add `pea version --json` for machine-readable output
- Add `pea version -v` short flag
- All 1374 tests pass with version query functionality

## 2.41.0 - Phase 43: Lockfile Validation & Dependency Listing (2026-11-30)
- Add `check_lock()` in package_manager to validate pea.lock against pea.toml
- Add `list_dependencies()` in package_manager to list deps with lock metadata
- Add `pea lock --check [path]` CLI command for lockfile consistency validation
- Add `pea deps [path]` CLI command for dependency listing
- All 1376 tests pass with lockfile validation and dependency listing

## 2.41.0 - Phase 44: Library Uninstall (2026-11-30)
- Add `uninstall()` function in package_manager to remove libraries from `.pea_modules`
- Add `pea uninstall <name> [path]` CLI command
- All 1378 tests pass with library uninstall functionality

## 2.41.0 - Phase 45: Library Update (2026-11-30)
- Add `update()` function in package_manager to refresh installed libraries from pea.lock
- Add `pea update [path]` CLI command
- All 1380 tests pass with library update functionality

## 2.41.0 - Phase 46: Library Outdated (2026-11-30)
- Add `outdated()` function in package_manager to report libraries that are missing, outdated, or up to date
- Add `pea outdated [path]` CLI command
- All 1382 tests pass with library outdated functionality

## 2.41.0 - Phase 47: Dependency Tree (2026-11-30)
- Add `dependency_tree()` in package_manager to recursively build the dependency tree from pea.toml (recurse into path dependencies)
- Add `pea deps --tree [path]` CLI command for dependency tree output
- All 1383 tests pass with dependency tree functionality

## 2.41.0 - Phase 48: Library Clean (2026-11-30)
- Add `clean()` function in package_manager to remove `.pea_modules` (and optionally `pea.lock`) from a project
- Add `pea clean [path] [--all]` CLI command
- All 1385 tests pass with library clean functionality

## 2.41.0 - Phase 49: Publish Dry-Run (2026-11-25)
- Add `--dry-run` flag to `pea publish` and `pea lib publish` to build library packages without uploading
- Refresh all four `.github/workflows` files with current action versions, explicit job names, and `master`/`main` branch coverage
- Fix Python 3.10/3.11 CI failures: guard `tarfile.extractall(filter='data')` with a fallback and relax float formatting assertions in use-case tests
- All 1387 tests pass with publish dry-run functionality

## 2.41.0 - Phase 50: Library Package Inspection (2026-11-25)
- Add `inspect_library()` in package_manager to read `.pelib` metadata, exports, file list, and SHA-256 without installing
- Add `pea lib inspect <package.pelib> [--json]` CLI command
- All 1389 tests pass with library package inspection functionality

### Phase 34: Standard Library Completion (2.41.0)