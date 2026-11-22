# PeaLang SDK Examples

This directory contains example applications demonstrating how to use each
PeaLang host SDK to connect to a PeaLang runtime service.

## Prerequisites

Start a PeaLang runtime service:

```bash
python -m pealang.cli serve --port 8080
```

## Examples

| Language | Directory | Description |
|----------|-----------|-------------|
| Node.js/TypeScript | `node/` | TypeScript client using `fetch` |
| Go | `go/` | Go client using `net/http` |
| Python | `python/` | Python client using `urllib` |
| Java | `java/` | Java client using `HttpClient` |
| C# | `csharp/` | C# client using `HttpClient` |
| Rust | `rust/` | Rust async client using `reqwest` |
| Ruby | `ruby/` | Ruby client using `Net::HTTP` |
| PHP | `php/` | PHP client using `Guzzle` |

## Generated SDKs

Each example assumes the corresponding SDK has been generated with:

```bash
pea sdk generate <language> ./sdk
```

Or generated from `.pea` source:

```bash
pea sdk-codegen ./my_module.pea <language> ./sdk
```

## Running an Example

```bash
# 1. Start the PeaLang runtime service (in one terminal)
python -m pealang.cli serve --port 8080

# 2. Generate an SDK
pea sdk generate python ./sdk

# 3. Run the example (in another terminal)
cd examples/sdks/python
python example.py
```
