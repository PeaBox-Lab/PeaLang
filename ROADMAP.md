## 2.37.0 - Phase 35: Language Extension Type System (2026-11-25)
- Add `ExtensionTypeSystem` class integrating extension types with the interpreter's type system
- Add `pea ext type <name>` CLI command to show type details and methods
- Add `pea ext type info <name>` for detailed type inspection
- Register built-in extension types (Option, Result, Error) with methods
- Add tests: test_extension_type_system, test_pea_ext_type_info, test_pea_ext_type_cli
- All 1353 tests pass with type system integration