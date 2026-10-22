# PeaLang Optional Type System

PeaLang 0.19 adds optional static annotations without breaking untyped programs.

## Variables

```pea
let score: Int = 4
let salary: Number = 100000
let manager: String? = null
let tags: List<String> = ["hr", "automation"]
```

## Functions

```pea
function add(a: Int, b: Int) -> Int {
    return a + b
}
```

## Records

```pea
type Employee = {
    name: String,
    rating: Int,
    salary: Number
}
```

## Union and generic types

```pea
let identifier: String | Int = "E1001"
let employees: List<Employee> = []
let index: Map<String, Employee> = {}
```

## Typecheck

```bash
pea typecheck app.pea
pea typecheck src tests
```

The command exits with code `0` when no type errors are found and `1` when errors exist. Type annotations are erased before execution, so typed and untyped code use the same runtime in this release.

## Current limits

Version 0.19 validates declarations, assignments, named record types, function signatures, nullable types, unions, and generic type syntax. Full expression-flow inference, return-path analysis, cross-module resolution, and record field conformance are planned refinements.
