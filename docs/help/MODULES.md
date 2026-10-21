# Modules Help
Use `export name` inside a module and `import "path.pea" as alias` in the caller. Access exports as `alias.name`. If a property is missing, confirm the module actually exported it. `export` at the top-level entry program is rejected; it is intended for imported module execution.
