## 2.41.0 - Phase 34: Standard Library Completion (2026-11-24)
- Add 9 new standard library modules: std.sql, std.cache, std.uuid, std.cli, std.config, std.template, std.serialize, std.graph, std.queue, std.env
- Fix std.config JSON/TOML parse (was using undefined `p` instead of `path`)
- Fix std.template render_file (same undefined `p` bug)
- Fix std.queue priority queue (was pushing max-heap; now max-priority pops first)
- Add stdlib.Namespace.__getattribute__ so attribute access falls back to dict keys
- Add 10 test files covering each new module
- Update CHANGELOG.md with Phase 34 entry (1353 tests pass)