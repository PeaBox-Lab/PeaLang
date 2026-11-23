# PeaLang Extension Development Guide

# Table of Contents

1. [Overview](#overview)
2. [Extension Types](#extension-types)
3. [Creating Extension Functions](#creating-extension-functions)
4. [Creating Extension Types](#creating-extension-types)
5. [Creating Extension Operators](#creating-extension-operators)
6. [Creating Extension Namespaces](#creating-extension-namespaces)
7. [Loading Extensions](#loading-extensions)
8. [Extension Manifest Declaration](#extension-manifest-declaration)
9. [CLI Commands](#cli-commands)
10. [Best Practices](#best-practices)
11. [Examples](#examples)

---

# Overview

PeaLang's extension system allows you to extend the language with custom functions, types, operators, and namespaces. Extensions can be written in Python and registered at runtime, making it easy to add domain-specific functionality without modifying the PeaLang core.

## Extension Types

| Extension Type | Description |
|---------------|-------------|
| **Functions** | Callable from PeaLang source code |
| **Types** | Custom types with methods, usable in type annotations |
| **Operators** | Custom infix operators (e.g., `++`, `~~`) |
| **Namespaces** | Named groups of symbols (e.g., `std.myextension`) |

---

# Creating Extension Functions

Extension functions are Python functions registered with the extension registry. They can be called from PeaLang source code.

## Basic Example

```python
# my_extensions.py
def greet(name: str) -> str:
    """Greets a person by name."""
    return f"Hello, {name}!"

def add(a, b):
    """Adds two numbers."""
    return a + b

# Register with PeaLang
from pealang.extension_registry import ExtensionRegistry

reg = ExtensionRegistry()
reg.register_function('greet', greet, 1, 'Greets a person by name')
reg.register_function('add', add, 2, 'Adds two numbers')
```

## Using in PeaLang Source

```pea
import std.io

print ext.greet("World")    // Output: Hello, World!
print ext.add(3, 4)         // Output: 7
```

## Function Registration Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Function name (as called from PeaLang) |
| `func` | callable | The Python function |
| `arg_count` | int or None | Number of arguments (None = variadic) |
| `doc` | str | Documentation string |

---

# Creating Extension Types

Extension types allow you to define custom types with methods that can be used from PeaLang source.

## Basic Example

```python
# my_types.py
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def distance(self, other):
        return ((self.x - other.x)**2 + (self.y - other.y)**2) ** 0.5
    
    def __str__(self):
        return f"Point({self.x}, {self.y})"

# Register with PeaLang
from pealang.extension_registry import ExtensionRegistry

reg = ExtensionRegistry()
reg.register_type('Point', Point, {
    'distance': lambda self, other: self.distance(other),
    '__str__': lambda self: str(self),
}, doc='A 2D point with x and y coordinates')
```

## Using in PeaLang Source

```pea
import std.io

let p1 = Point(3, 4)
let p2 = Point(6, 8)

print p1.distance(p2)    // Output: 5.0
print p1                 // Output: Point(3, 4)
```

## Type Registration Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Type name |
| `constructor` | callable | Constructor function |
| `methods` | dict | Method name -> callable mapping |
| `doc` | str | Documentation string |

---

# Creating Extension Operators

Extension operators allow you to define custom infix operators for use in PeaLang expressions.

## Basic Example

```python
# my_ops.py
def vector_add(a, b):
    """Add two vectors element-wise."""
    return [a[i] + b[i] for i in range(len(a))]

def vector_sub(a, b):
    """Subtract two vectors element-wise."""
    return [a[i] - b[i] for i in range(len(a))]

# Register with PeaLang
from pealang.extension_registry import ExtensionRegistry

reg = ExtensionRegistry()
reg.register_operator('⊕', vector_add, 10, 'Vector addition')
reg.register_operator('⊖', vector_sub, 10, 'Vector subtraction')
```

## Using in PeaLang Source

```pea
let a = [1, 2, 3]
let b = [4, 5, 6]

let c = a ⊕ b    // [5, 7, 9]
let d = a ⊖ b    // [-3, -3, -3]

print c  // Output: [5, 7, 9]
print d  // Output: [-3, -3, -3]
```

## Operator Registration Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | str | Operator symbol (e.g., `++`, `~~`) |
| `func` | callable | Binary function (a, b) -> result |
| `precedence` | int | Operator precedence (higher = binds tighter) |
| `doc` | str | Documentation string |

---

# Creating Extension Namespaces

Namespaces group related symbols under a common prefix, similar to Python modules or JavaScript namespaces.

## Basic Example

```python
# my_ns.py
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

# Register with PeaLang
from pealang.extension_registry import ExtensionRegistry

reg = ExtensionRegistry()
reg.register_namespace('math.ext', {
    'add': add,
    'subtract': subtract,
})
```

## Using in PeaLang Source

```pea
import std.io

print math.ext.add(3, 4)      // Output: 7
print math.ext.subtract(10, 3) // Output: 7
```

---

# Loading Extensions

Extensions can be loaded in several ways:

## 1. Programmatically (Python)

```python
from pealang.extension_registry import ExtensionRegistry
from pealang.interpreter import Interpreter

reg = ExtensionRegistry()
reg.register_function('my_func', my_func, 1, 'My custom function')

interp = Interpreter()
interp.extension_registry = reg
interp.extension_type_system = ExtensionTypeSystem(reg)
```

## 2. From pea.toml Manifest

Add an `[extensions]` section to your `pea.toml`:

```toml
[extensions]
functions = ["my_custom_func", "another_func"]
types = ["MyType", "AnotherType"]
operators = ["++", "~~"]
namespaces = ["std.myext", "std.utils"]
```

The interpreter will automatically load these when the project is loaded.

## 3. Via CLI

```bash
# List all extensions
pea ext list

# Load a module
pea ext load my_extension_module

# Get info about an extension
pea ext info my_custom_func
```

---

# CLI Commands Reference

## `pea ext list`

Lists all registered extensions:

```bash
pea ext list
```

Output:
```
Extension functions:
  my_custom_func
  another_func

Extension types:
  MyType
  AnotherType

Extension operators:
  ++
  ~~

Extension namespaces:
  std.myext
  std.utils
```

## `pea ext load <module>`

Loads a Python module as extensions:

```bash
pea ext load my_ext_module
```

## `pea ext info <name>`

Shows details about a specific extension:

```bash
pea ext info my_custom_func
# Function: my_custom_func
#   Arg count: 1
#   Doc: My custom function

pea ext info MyType
# Type: MyType
#   Methods: method1, method2
#   Doc: A custom type

pea ext info ++
# Operator: ++
#   Precedence: 10
#   Doc: Custom increment operator

pea ext info std.myext
# Namespace: std.myext
#   Symbols: func1, func2
```

---

# Best Practices

## Extension Function Best Practices

1. **Use descriptive names** - Function names should clearly indicate what they do
2. **Handle errors gracefully** - Use try/except and raise meaningful errors
3. **Validate inputs** - Check input types and ranges
4. **Document your functions** - Add docstrings and descriptions
5. **Keep functions pure** - Functions should be deterministic when possible

## Extension Type Best Practices

1. **Implement `__str__`** - Provide a string representation
2. **Implement `__eq__`** - Allow comparison of instances
3. **Document methods** - Document what each method does
4. **Validate inputs** - Check input types in constructors and methods

## Extension Operator Best Practices

1. **Use intuitive symbols** - Choose symbols that intuitively represent the operation
2. **Choose appropriate precedence** - Higher precedence = binds tighter
3. **Document behavior** - Clearly document what the operator does
4. **Avoid conflicts** - Don't override existing operators unless necessary

## Extension Namespace Best Practices

1. **Use descriptive names** - Use names that clearly indicate the namespace's purpose
2. **Group related functions** - Group related functions in the same namespace
3. **Document the namespace** - Explain what the namespace provides
4. **Use hierarchical names** - Use dots to separate hierarchy levels (e.g., `math.ext`)

---

# Examples

## Complete Example: Math Utilities Extension

```python
# my_math_ext.py
import math

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

def sqrt(x):
    if x < 0:
        raise ValueError("Cannot compute square root of negative number")
    return math.sqrt(x)

def power(base, exponent):
    return base ** exponent

# Register with PeaLang
from pealang.extension_registry import ExtensionRegistry

reg = ExtensionRegistry()
reg.register_function('add', add, 2, 'Add two numbers')
reg.register_function('subtract', subtract, 2, 'Subtract two numbers')
reg.register_function('multiply', multiply, 2, 'Multiply two numbers')
reg.register_function('divide', divide, 2, 'Divide two numbers')
reg.register_function('sqrt', sqrt, 1, 'Square root')
reg.register_function('power', power, 2, 'Raise base to exponent')

# Register types
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def magnitude(self):
        return (self.x**2 + self.y**2) ** 0.5
    
    def add(self, other):
        return Vector(self.x + other.x, self.y + other.y)
    
    def __str__(self):
        return f"Vector({self.x}, {self.y})"

reg.register_type('Vector', Vector, {
    'magnitude': lambda self: self.magnitude(),
    'add': lambda self, other: self.add(other),
    '__str__': lambda self: str(self),
}, doc='A 2D vector with x and y components')

# Register operators
reg.register_operator('⊕', lambda a, b: Vector(a.x + b.x, a.y + b.y), 10, 'Vector addition')
reg.register_operator('⊖', lambda a, b: Vector(a.x - b.x, a.y - b.y), 10, 'Vector subtraction')

# Register namespace
reg.register_namespace('math.ext', {
    'add': add,
    'subtract': subtract,
    'multiply': multiply,
    'divide': divide,
})

# Use in pea.toml:
# [extensions]
# functions = ["add", "subtract", "multiply", "divide", "sqrt", "power"]
# types = ["Vector"]
# operators = ["⊕", "⊖"]
# namespaces = ["math.ext"]
```

## Using the Extension in PeaLang

```pea
import std.math.ext

let v1 = Vector(3, 4)
let v2 = Vector(1, 2)

let sum = v1 ⊕ v2
print sum  // Output: Vector(4, 6)

let diff = v1 ⊖ v2
print diff  // Output: Vector(2, 2)

print math.ext.add(5, 3)  // Output: 8
print math.sqrt(16)       // Output: 4.0
print math.power(2, 10)   // Output: 1024
```

---

# Best Practices

## Extension Development

1. **Start simple** - Start with simple functions and add complexity gradually
2. **Test thoroughly** - Test extensions with various inputs
3. **Document everything** - Document functions, types, operators, and namespaces
4. **Use versioning** - Version your extensions and document breaking changes
5. **Handle errors gracefully** - Use try/except and raise meaningful errors

## Extension Distribution

1. **Package as Python packages** - Distribute extensions as Python packages
2. **Include requirements.txt** - List dependencies
3. **Include examples** - Include example usage in documentation
4. **Test on multiple platforms** - Test on different Python versions and platforms

## Extension Security

1. **Validate inputs** - Check input types and ranges
2. **Sanitize inputs** - Sanitize user inputs to prevent injection attacks
3. **Limit resource usage** - Limit memory and CPU usage
4. **Audit code** - Review extension code for security issues

---

# Troubleshooting

## Common Issues

### "Extension not found"
- Check the extension name spelling
- Verify the extension was loaded correctly
- Check if the module was loaded with `pea ext load`

### "Function not callable"
- Check if the function was registered correctly
- Verify the function signature matches the expected signature

### "Type not found"
- Check if the type was registered correctly
- Verify the type name spelling

## Debugging Extensions

```python
from pealang.extension_registry import ExtensionRegistry

reg = ExtensionRegistry()
print(reg.list_all())
# {'functions': [...], 'types': [...], 'operators': [...], 'namespaces': [...]}
```

---

# Getting Help

- Documentation: https://docs.pealang.dev
- Examples: https://github.com/pealang/examples
- Issues: https://github.com/pealang/pealang/issues
- Community: https://discord.gg/pealang

---

*PeaLang Extension Development Guide - Version 2.40.0*
