# PeaLang Developer Guide & SDK Reference

# Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Standard Library Reference](#standard-library-reference)
   - [Core Modules](#core-modules)
   - [New Standard Libraries](#new-standard-libraries)
     - [std.sql - SQL Query Builder](#stdsql---sql-query-builder)
     - [std.cache - In-Memory Caching](#stdcache---in-memory-caching)
     - [std.uuid - UUID Generation](#stduuid---uuid-generation)
     - [std.cli - Command-Line Arguments](#stdcli---command-line-arguments)
     - [std.config - Configuration Files](#stdconfig---configuration-files)
     - [std.template - Template Engine](#stdtemplate---template-engine)
     - [std.serialize - Serialization](#stdserialize---serialization)
     - [std.graph - Graph Algorithms](#stdgraph---graph-algorithms)
     - [std.queue - Queue Data Structures](#stdqueue---queue-data-structures)
     - [std.env - Environment Variables](#stenv---environment-variables)
4. [Creating Your Own Libraries](#creating-your-own-libraries)
5. [Cross-Language Host SDKs](#cross-language-host-sdks)
6. [Extension System](#extension-system)
7. [Publishing to the Registry](#publishing-to-the-registry)
8. [Best Practices](#best-practices)

---

# Overview

PeaLang is a modern programming language designed for developer productivity, cross-runtime portability, and extensibility. This guide covers:

- The standard library (stdlib) and its modules
- How to create and publish your own PeaLang libraries
- How to extend PeaLang with custom extensions
- How to publish and consume libraries from the package registry

# Getting Started

## Installation

PeaLang is distributed as a Python package:

```bash
pip install pealang
```

Or from source:

```bash
git clone https://github.com/pealang/pealang.git
cd pealang
pip install -e .
```

## Running PeaLang Code

```bash
# Run a .pea file
pea run myscript.pea

# Run with REPL
pea

# Compile to bytecode
pea compile myscript.pea -o myscript.peac

# Run bytecode
pea vm myscript.peac
```

## Hello World

Create `hello.pea`:

```pea
print "Hello, World!"
```

Run it:

```bash
pea run hello.pea
# Output: Hello, World!
```

---

# Standard Library Reference

PeaLang comes with a comprehensive standard library organized into namespaces (e.g., `std.string`, `std.math`, `std.http`). All standard library modules are accessed via the `std` namespace:

```pea
import std.string
print std.string.upper("hello")  # Output: HELLO
```

## Core Modules

| Module | Description |
|--------|-------------|
| `std.collections` | Collection transforms and queries |
| `std.string` | Unicode string helpers |
| `std.math` | Mathematics and statistics |
| `std.datetime` | UTC-oriented date/time helpers |
| `std.json` | JSON encode/decode |
| `std.csv` | CSV file IO |
| `std.regex` | Regular expressions |
| `std.file` | Controlled filesystem IO |
| `std.path` | Path manipulation |
| `std.http` | HTTP client |
| `std.crypto` | Hashing, HMAC and random tokens |
| `std.logging` | Host logging |
| `std.testing` | Assertions for libraries |
| `std.concurrent` | Bounded parallel map |
| `std.web` | Web application toolkit |
| `std.analysis` | Data analysis helpers |
| `std.interop` | Cross-language interoperability |
| `std.ux` | User-experience and diagnostics helpers |
| `std.stats` | Numerical, statistical and modelling toolkit |

## New Standard Libraries (2.31+)

### `std.sql` - SQL Query Builder

Build SQL queries programmatically:

```pea
import std.sql

// SELECT query
let query = std.sql.select("users", ["id", "name"], where="active = 1")
print query  // SELECT id, name FROM users WHERE active = 1

// INSERT query
let query = std.sql.insert("users", {"id": 1, "name": "Alice"})
print query  // INSERT INTO users (id, name) VALUES (1, 'Alice')

// UPDATE query
let query = std.sql.update("users", {"name": "Bob"}, "id = 1")
print query  // UPDATE users SET name = 'Bob' WHERE id = 1

// DELETE query
let query = std.sql.delete("users", "id = 1")
print query  // DELETE FROM users WHERE id = 1

// CREATE TABLE
let query = std.sql.create_table("users", {"id": "INT", "name": "TEXT"})
print query  // CREATE TABLE IF NOT EXISTS users (id INT, name TEXT)

// DROP TABLE
let query = std.sql.drop_table("users")
print query  // DROP TABLE IF EXISTS users
```

### `std.cache` - In-Memory Caching with TTL

```pea
import std.cache

// Set a value with 60-second TTL
std.cache.set("user:1", {"name": "Alice", "age": 30}, ttl=60)

// Get a value
let user = std.cache.get("key1", default="default_value")

// Check if key exists
if std.cache.has("key1") {
    print "Key exists!"
}

// Delete a key
std.cache.delete("key1")

// Clear all
std.cache.clear()

// Check size
let count = std.cache.size()

// List all keys
let keys = std.cache.keys()
```

### `std.uuid` - UUID Generation

```pea
import std.uuid

// Generate UUID v4
let id = std.uuid.v4()
print id  // e.g., "a1b2c3d4e5f678901234567890123456"

// UUID v1 (time-based)
let id = std.uuid.v1()

// UUID v3 (namespace-based)
let id = std.uuid.v3("6ba7b810-9dad-11d1-80b4-00c04fd430c8", "example.com")

// UUID v5 (namespace-based, SHA-1)
let id = std.uuid.v5("6ba7b810-9dad-11d1-80b4-00c04fd430c8", "example.com")

// Random hex string
let id = std.uuid.random()
```

### `std.cli` - Command-Line Argument Parsing

```pea
import std.cli

// Parse command-line arguments
let args = std.cli.parse()

// Check if a flag is present
if std.cli.has("verbose") {
    print "Verbose mode enabled"
}

// Get a flag value
let output = std.cli.get("output", "default.txt")
print "Output file: " + output

// Get positional arguments
let positional = std.cli.parse()["_positional"]
print "Positional args: " + str(positional)
```

### `std.config` - Configuration File Parsing

```pea
import std.config

// Parse INI file
let config = std.config.parse_ini("config.ini")
let db_host = std.config.get(config, "database.host", "localhost")
let db_port = std.config.get(config, "database.port", 5432)

// Parse JSON file
let config = std.config.parse_json("config.json")

// Parse TOML file
let config = std.config.parse_toml("pyproject.toml")

// Parse YAML file (requires PyYAML)
let config = std.config.parse_yaml("config.yaml")
```

### `std.template` - Template Engine

```pea
import std.template

// Simple variable substitution
let result = std.template.render("Hello {{name}}!", {"name": "World"})
print result  // Output: Hello World!

// Conditional blocks
let tmpl = "{% if logged_in %}Welcome back, {{name}}!{% else %}Please log in.{% endif %}"
let result = std.template.render(tmpl, {"logged_in": true, "name": "Alice"})
print result  // Output: Welcome back, Alice!

// Render from file
let result = std.template.render_file("template.html", {"name": "World"})
```

### `std.serialize` - Serialization

```pea
import std.serialize

// JSON serialization
let payload = std.serialize.json_dumps({"name": "Alice", "age": 30}, indent=2)
print payload

// JSON deserialization
let data = std.serialize.json_loads('{"name": "Alice", "age": 30}')
print data["name"]  // Output: Alice

// CSV serialization
let csv = std.serialize.csv_dumps([
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25}
])
print csv

// CSV deserialization
let rows = std.serialize.csv_loads("name,age\nAlice,30\nBob,25")
print rows[0]["name"]  // Output: Alice
```

### `std.graph` - Graph Data Structures and Algorithms

```pea
import std.graph

// Create an undirected graph
let g = std.graph.create(directed=false)

// Add edges
g.add_edge("A", "B")
g.add_edge("B", "C")
g.add_edge("A", "C")

// Check if node exists
if g.has_node("A") {
    print "Node A exists"
}

// Get neighbors
let neighbors = g.neighbors("A")
print "Neighbors of A: " + str(neighbors)  // Output: ['B', 'C']

// Breadth-first search
let order = g.bfs("A")
print "BFS order: " + str(order)  // Output: ['A', 'B', 'C']

// Depth-first search
let order = g.dfs("A")
print "DFS order: " + str(order)  // Output: ['A', 'B', 'C']

// Shortest path
let path = g.shortest_path("A", "C")
print "Shortest path: " + str(path)  // Output: ['A', 'C']
```

### `std.queue` - Queue and Priority Queue

```pea
import std.queue

// Regular queue (FIFO)
let q = std.queue.create()
q.enqueue("first")
q.enqueue("second")
print q.dequeue()  // Output: "first"
print q.size()     // Output: 1

// Priority queue (lower priority = higher priority)
let pq = std.queue.priority_create()
pq.push("low", 1)
pq.push("high", 10)
pq.push("mid", 5)
print pq.pop()     // Output: "high" (highest priority)
print pq.pop()     // Output: "mid"
print pq.pop()     // Output: "low"
```

### `std.env` - Environment Variables

```pea
import std.env

// Get environment variable
let home = std.env.get("HOME", "/default/path")
print "Home: " + home

// Set environment variable
std.env.set("MY_VAR", "hello")

// Check if exists
if std.env.has("PATH") {
    print "PATH is set"
}

// List all environment variables
let keys = std.env.keys()
print "Env keys: " + str(keys[:5])

// Unset environment variable
std.env.unset("MY_VAR")
```

---

# Creating Your Own Libraries

PeaLang makes it easy to create and share libraries. Follow these steps:

## 1. Create a Library Project

```bash
# Create a new library project
pea init --template library mylib

cd mylib
```

This generates:
```
mylib/
├── pea.toml              # Project manifest
├── src/
│   └── mylib.pea         # Your library source
├── tests/
│   └── test_mylib.pea    # Tests
├── README.md             # Documentation
└── LICENSE               # License file
```

## 2. Write Your Library Code

Edit `src/mylib.pea`:

```pea
// mylib - A useful utility library

export function add(a, b) {
    return a + b
}

export function greet(name) {
    return "Hello, " + name
}

export function version() {
    return "1.0.0"
}
```

## 3. Write Tests

Edit `tests/test_mylib.pea`:

```pea
import "../src/mylib.pea" as mylib

test "add function" {
    expect mylib.add(2, 3) == 5
    expect mylib.add(-1, 1) == 0
}

test "greet function" {
    expect mylib.greet("World") == "Hello, World"
}

test "version function" {
    expect mylib.version() == "1.0.0"
}
```

## 4. Test Your Library

```bash
pea test
```

## 5. Build Your Library

```bash
pea build --library
```

This creates `mylib-1.0.0.pelib` - a distributable package.

## 6. Publish Your Library

```bash
# Publish to a registry
pea publish ./mylib --registry http://registry.example.com --token <token>

# Or publish to multiple registries
pea publish ./mylib --registry https://registry.pealang.dev --token <token>
```

---

# Cross-Language Host SDKs

PeaLang provides host SDKs for integrating PeaLang into applications written in other languages:

| SDK | Language | Files |
|-----|----------|-------|
| Node.js | JavaScript/TypeScript | `src/index.ts`, `package.json` |
| Go | Go | `pealang/client.go`, `go.mod` |
| Python | Python | `pealang/client.py`, `pyproject.toml` |
| Browser | TypeScript | `src/browserClient.ts`, `src/browserLoader.ts` |
| Java | Java | `src/main/java/com/pealang/SdkClient.java`, `pom.xml` |
| C# | C# | `pealang/SdkClient.cs`, `pealang.csproj` |
| Rust | Rust | `src/main.rs`, `Cargo.toml` |
| Ruby | Ruby | `lib/pealang/client.rb`, `Gemfile` |
| PHP | PHP | `src/PeaClient.php`, `composer.json` |

Each SDK provides an HTTP client that connects to a PeaLang runtime service:

```typescript
// Node.js example
import { PeaClient } from 'pealang-client';

const client = new PeaClient('http://localhost:8080');
const result = await client.invoke('math_utils', 'add', [3, 7]);
console.log(result);  // 10
```

## Extension System

PeaLang supports extending the language with custom functions, types, and operators:

### Registering an Extension Function

```pea
// In a Python module (pe_extensions.py):
def my_custom_func(x):
    return x * 2

# Register with PeaLang
from pealang.extension_registry import ExtensionRegistry
reg = ExtensionRegistry()
reg.register_function('my_custom_func', my_custom_func, 1, 'Double a number')

# Use in PeaLang source:
# print my_custom_func(21)  // Output: 42
```

### Registering an Extension Type

```python
reg.register_type('MyType', lambda x: {'value': x}, {'double': lambda self: self['value'] * 2})
```

### Registering an Extension Operator

```python
reg.register_operator('++', lambda a, b: a + b + 1, 10, 'Custom increment operator')
```

### CLI Commands for Extensions

```bash
# List all extensions
pea ext list

# Load an extension module
pea ext load my_ext_module

# Get info about an extension
pea ext info my_custom_func
```

---

# Publishing to the Registry

The PeaLang registry is a self-hosted package server for sharing libraries.

## Running a Registry Server

```bash
pea registry serve --host 0.0.0.0 --port 8788 --storage ./registry-storage --name my-registry
```

## Publishing a Library

```bash
pea publish ./mylib --registry http://localhost:8788 --token <token>
```

## Registering a Publisher

```bash
pea registry register-publisher <token> <publisher-id>
```

## Consuming Published Libraries

```toml
[dependencies]
mylib = { registry = "http://registry.example.com", version = "1.0.0" }
```

---

# Best Practices

## Library Design

1. **Keep functions pure** - Functions should be deterministic and have no side effects
2. **Document everything** - Add comments and README documentation
3. **Use semantic versioning** - Follow semver for version numbers (MAJOR.MINOR.PATCH)
4. **Include tests** - Always include tests for your library functions
5. **Handle errors gracefully** - Use try/catch and provide meaningful error messages

## Publishing Best Practices

1. **Use semantic versioning** - Bump major version for breaking changes
2. **Document your API** - Include examples in your README
3. **Tag your releases** - Use Git tags for version releases
4. **Include a LICENSE** - Specify how others can use your library

## Extension Best Practices

1. **Document your extensions** - Explain what each extension does
2. **Provide migration guides** - Help users migrate from deprecated extensions
3. **Use clear names** - Use descriptive names for extensions
4. **Test thoroughly** - Test extensions with various inputs

---

# Getting Help

- Documentation: https://docs.pealang.dev
- Examples: https://github.com/pealang/examples
- Issues: https://github.com/pealang/pealang/issues
- Community: https://discord.gg/pealang

---

*PeaLang Documentation - Version 2.40.0*
