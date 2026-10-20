# PeaLang v0.3.0 Release Notes
v0.3.0 is the Automation Standard Library release. It adds namespaced file/path, JSON, CSV, environment, date/time, regex, HTTP, and guarded process APIs without adding new grammar.

## Safety
Process launching is off by default, uses no shell, and requires explicit opt-in. HTTP defaults to a 15-second timeout. The runtime remains experimental and unsandboxed.

## Compatibility
All 18 v0.2 tests are retained. Existing v0.1 built-ins remain available for compatibility, although namespaced APIs are preferred for new programs.

## Validation
See `TEST_REPORT.md` for commands, environment and actual results.
