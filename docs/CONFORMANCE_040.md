# PeaLang Conformance Gate 0.40

0.40 introduces a deterministic 500-case interpreter/VM differential corpus, lexer/parser fuzz harness, security-boundary suite, and GitHub Actions matrices for Windows/Linux/macOS with Python 3.10-3.13.

Run `pea conformance`.

Important: 500 generated cases are now executable and gated, but the roadmap's >=90% parser/VM coverage and 100% security-boundary coverage are not claimed until measured by CI coverage evidence. Local release testing verifies functionality, not every operating-system/Python matrix combination.

