# PeaLang Language Reference v0.2.0

## Lexical structure
Comments begin with `#` or `//`. Statements are separated by a newline or semicolon. Blocks use braces.

## Values
Numbers, strings, booleans (`true`, `false`), `null`, lists, dictionaries, user functions, and host built-ins.

## Variables
```pea
let score = 10
const limit = 100
score += 5
```

## Strings and interpolation
```pea
let name = "Rajesh"
print "Hello {name}, total {2 + 3}"
```
Use `{{` and `}}` for literal braces.

## Operators
Arithmetic: `+ - * / %`; comparison: `== != < <= > >=`; logic: `and or not`.

## Control flow
```pea
if score >= 50 { print "pass" } else { print "retry" }
while score < 50 { score += 1 }
for item in range(1, 5) {
    if item == 2 { continue }
    if item == 4 { break }
    print item
}
```

## Functions
```pea
function square(x) { return x * x }
print square(9)
```

## Collections
```pea
let person = {"name": "Rajesh"}
print person.name
person.name = "Pea"
let scores = [10, 20]
scores[1] += 5
```

## Imports
```pea
import "math.pea"
print twice(10)
```
Imports are relative to the running file, execute once, and currently share the global environment.

## Built-ins
`range`, `len`, `str`, `number`, `int`, `type`, `upper`, `lower`, `split`, `join`, `append`, `keys`, `values`, `json`, `read`, `write`, `exists`, `sqrt`, `round`, and `sleep`.

## Automation namespaces added in v0.3.0
The global namespaces `file`, `path`, `json`, `csv`, `env`, `datetime`, `regex`, `http`, and `process` expose automation functions through property calls. See `docs/STANDARD_LIBRARY.md` for signatures and return contracts.
