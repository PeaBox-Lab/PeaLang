# PeaLang Bytecode Compiler and VM

PeaLang 0.20 introduces a portable stack bytecode layer alongside the existing tree-walking interpreter.

## Compile

```bash
pea compile app.pea
pea compile app.pea -o build/app.peac
```

A `.peac` file is UTF-8 JSON with a `PEAC` format marker, format version, constant pool, top-level code object, function code objects, instructions, line mappings, and source name. The format is inspectable in 0.20 while the instruction set remains preview.

## Run on the VM

```bash
pea vm app.pea
pea vm app.peac
pea app.peac
```

Set an instruction budget:

```bash
pea vm app.peac --max-instructions 50000
```

## Disassemble

```bash
pea dis app.peac
```

Example output:

```text
code <module>():
  0000 L1    CONST            0
  0001 L1    PRINT
  0002 L1    HALT
```

## Supported compiler subset

- literals and variables
- arithmetic and comparisons
- lists and dictionaries
- indexed and dotted access
- `if`/`else`
- `while` and `for`
- named functions, calls, and returns
- exports
- built-in host-callable functions
- source line metadata

The original interpreter remains the compatibility runtime for advanced features not yet compiled, including imports, exception constructs, workflow primitives, parallel blocks, AI declarations, and some assignment forms.
