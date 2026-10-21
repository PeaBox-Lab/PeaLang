# Getting Started
1. Install Python 3.9 or later.
2. From the project root run `python -m pip install -e .`.
3. Run `pea examples/hello.pea`.
4. Open the REPL with `pea`.
5. Run checks with `python -m unittest discover -s tests -v`.

Create `welcome.pea`:
```pea
let name = "PeaLang"
print "Welcome to {name}!"
```
Run it with `pea welcome.pea`.

## Project quick start (v0.7)
Run `pea init my-app`, enter the directory, then `pea start`. Use `modules/` for reusable project code and `pea add name path` for local dependencies.
