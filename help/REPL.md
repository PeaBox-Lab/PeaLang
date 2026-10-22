# PeaLang REPL Help

Start the interactive shell:

```cmd
pea repl
```

At the `pea>` prompt, enter PeaLang code or one of these REPL commands:

| Command | Purpose |
|---|---|
| `help` or `:help` | General help |
| `help TOPIC` or `:help TOPIC` | Topic help |
| `? TOPIC` | Short help alias |
| `:topics` | List help topics |
| `:commands` | List CLI commands |
| `:examples` | Show copy-ready examples |
| `:vars` | List variables in the current session |
| `:clear` | Reset the session |
| `:version` | Show the current version |
| `exit` or `quit` | Return to Windows CMD, PowerShell, or the terminal |

Commands such as `python -m pytest -q`, `pip install`, and `dir` are operating-system commands. Run them after entering `exit`, not at the `pea>` prompt.
