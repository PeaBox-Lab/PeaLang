# PeaLang Standard Library 0.35

The stable namespace is `std`. Modules: `std.collections`, `std.string`, `std.math`, `std.datetime`, `std.json`, `std.csv`, `std.regex`, `std.file`, `std.path`, `std.http`, `std.crypto`, `std.logging`, `std.testing`, and `std.concurrent`.

Sensitive capabilities are denied unless granted: `file.read`, `file.write`, `http.request`, `log`, and `concurrent`. Legacy top-level namespaces remain available during 0.x for compatibility; new programs SHOULD use `std.*`.
