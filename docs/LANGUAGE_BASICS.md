# PeaLang Language Basics

## 1. Programs and statements
PeaLang files end in `.pea`. A program is a sequence of statements separated by newlines or semicolons. Blocks use braces.

```pea
print "Hello"
print 2 + 3
```

## 2. Comments
```pea
# Whole-line comment
// Alternative comment
```

## 3. Values
PeaLang has numbers, strings, booleans, `null`, lists, dictionaries, functions and built-in functions.

```pea
let count = 5
let price = 19.95
let name = "PeaLang"
let active = true
let missing = null
let skills = ["automation", "AI"]
let person = {"name": "Rajesh", "city": "Gurgaon"}
```

## 4. Variables and constants
Use `let` for a value that can change and `const` for a binding that cannot be reassigned.

```pea
let total = 10
total += 5
const tax_rate = 18
```

Assignment operators are `=`, `+=`, `-=`, `*=`, and `/=`.

## 5. Operators
Arithmetic: `+ - * / %`. Comparison: `== != < <= > >=`. Logic: `and or not`.

```pea
let eligible = score >= 70 and active
```

## 6. Conditions
```pea
if score >= 70 {
    print "pass"
} else {
    print "review"
}
```

## 7. Loops
```pea
for number in range(1, 6) {
    if number == 2 { continue }
    if number == 5 { break }
    print number
}

let attempts = 0
while attempts < 3 {
    attempts += 1
}
```

## 8. Functions
```pea
function add(a, b) {
    return a + b
}
print add(2, 5)
```
Functions capture surrounding variables, enabling lexical closures. Functions can call themselves recursively.

## 9. Collections
```pea
let names = ["Asha", "Vikram"]
names[1] = "Rajesh"

let employee = {"name": "Rajesh", "city": "Gurgaon"}
employee.city = "Delhi"
print employee["name"]
```
Use dot access for fixed dictionary keys and bracket access for indexes or dynamic keys.

## 10. String interpolation
```pea
let name = "Rajesh"
print "Hello {name}. Two plus three is {2 + 3}."
print "Literal braces: {{example}}"
```

## 11. Imports
```pea
import "helpers.pea"
print twice(10)
```
Imports are local files, resolved relative to the active program, executed once, and currently share global scope.

## 12. Errors
Errors generally use `source:line:column: message`. Run `pea check file.pea` before execution to find syntax errors, undefined names, duplicates and unused variables.

## 13. Automation foundations
```pea
let config = json.read("config.json")
let people = csv.read("employees.csv")
let output = path.join("output", "people.json")
json.write(output, people)
```
Use `env.require("API_KEY")` for externally supplied credentials. Use `http.get` only with trusted endpoints. `process.run` requires explicit opt-in.

## 14. Recommended learning sequence
1. Values and `print`
2. `let`, `const`, and operators
3. Conditions and loops
4. Functions
5. Lists and dictionaries
6. Interpolation and imports
7. File/JSON/CSV automation
8. Formatter, checker and tests
