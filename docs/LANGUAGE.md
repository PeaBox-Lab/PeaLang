# PeaLang Language Reference

## Comments
`# comment` and `// comment` are supported.

## Values
Numbers, strings, booleans (`true`, `false`), `null`, lists, and dictionaries.

## Variables
```text
let score = 10
const limit = 100
score += 5
```

## Operators
Arithmetic: `+ - * / %`. Comparison: `== != < <= > >=`. Logic: `and or not`.

## Control flow
```text
if score >= 50 { print "pass" } else { print "retry" }
while score < 50 { score += 1 }
for item in range(1, 5) { print item }
```

## Functions
```text
function square(x) { return x * x }
print square(9)
```

## Collections
```text
let names = ["A", "B"]
let person = {"name": "Rajesh", "city": "Gurgaon"}
print names[0]
print person["city"]
```

## Files
```text
write("output.txt", "Hello")
print read("output.txt")
```
