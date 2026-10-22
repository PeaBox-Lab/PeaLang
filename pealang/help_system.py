from __future__ import annotations

TOPICS = {
'getting-started': '''Getting started
  pea repl                       Start interactive mode
  pea run FILE.pea               Run a PeaLang file
  pea check FILE_OR_FOLDER       Validate source
  pea fmt FILE_OR_FOLDER         Format source

First program:
  let name = "Rajesh"
  print "Hello {name}"
''',
'repl': '''REPL commands
  :help [topic]     Show help or a topic
  help [topic]      Friendly alias for :help
  ? [topic]         Short alias for :help
  :topics           List help topics
  :commands         List REPL commands
  :examples         Show copy-ready examples
  :vars             List current variables
  :clear            Reset REPL state
  :version          Show PeaLang version
  exit or quit      Leave the REPL

Windows commands such as python, pip, dir, and pytest must be run after
leaving the REPL with exit.
''',
'syntax': '''Language syntax
  let x = 10
  const app = "PeaLang"
  print x
  if x > 5 { print "large" }
  for item in [1, 2, 3] { print item }
  function add(a, b) { return a + b }
''',
'variables': '''Variables
  let score = 10       Mutable variable
  const name = "Pea"   Constant
  score = score + 1    Assignment
Use :vars in the REPL to list current values.
''',
'functions': '''Functions
  function greet(name) {
    return "Hello {name}"
  }
  print greet("Rajesh")
Functions use lexical scope and may have default parameters.
''',
'collections': '''Collections
  let items = [1, 2, 3]
  let person = {"name": "Rajesh", "city": "Gurugram"}
  append(items, 4)
  print len(items)
  print keys(person)
''',
'files': '''Files and paths
  let text = file.read("notes.txt")
  file.write("copy.txt", text)
  print path.exists("copy.txt")
Run process operations only with --allow-process and trusted programs.
''',
'errors': '''Errors
  try {
    throw "Something failed"
  } catch error {
    print error
  } finally {
    print "done"
  }
''',
'debugging': '''Debugging
  pea debug FILE.pea --break=LINE
  pea dap
DAP supports conditions, hit counts, log points, exception stops, frames,
scopes, variables, evaluate, and lifecycle events.
''',
'commands': '''CLI commands
  pea --version
  pea help [topic]
  pea repl
  pea run FILE.pea
  pea FILE.pea
  pea fmt PATH [--check]
  pea check PATH
  pea test [PATH]
  pea docs FILE.pea [-o OUTPUT.md]
  pea debug FILE.pea --break=LINE
  pea dap
  pea init NAME
  pea project
  pea add NAME SOURCE
  pea remove NAME
  pea start
''',
}
ALIASES={'start':'getting-started','basics':'syntax','variable':'variables','function':'functions','list':'collections','dict':'collections','file':'files','error':'errors','debug':'debugging','cli':'commands'}

EXAMPLES='''Examples

Hello:
  let name = "Rajesh"
  print "Hello {name}"

Calculation:
  let x = 10
  let y = 20
  print x + y

Function:
  function add(a, b) {
    return a + b
  }
  print add(10, 20)

Loop:
  for item in ["HR", "Automation", "AI"] {
    print item
  }
'''

def topic_names(): return sorted(TOPICS)

def render_help(topic=None):
    if not topic:
        return '''PeaLang Help

Usage:
  pea help [topic]                Help from Windows CMD or PowerShell
  :help [topic]                   Help inside the PeaLang REPL
  help [topic]                    Friendly REPL alias

Popular topics:
  getting-started  repl  syntax  variables  functions
  collections      files errors  debugging  commands

Use `pea help topics` or `:topics` to list every topic.
'''
    key=ALIASES.get(topic.strip().lower(),topic.strip().lower())
    if key in ('topics','topic'):
        return 'Help topics\n  ' + '\n  '.join(topic_names()) + '\n'
    if key in ('examples','example'):
        return EXAMPLES
    if key in TOPICS: return TOPICS[key]
    matches=[name for name in TOPICS if key in name]
    hint=f" Did you mean: {', '.join(matches)}?" if matches else ''
    return f"Unknown help topic '{topic}'.{hint}\nUse `pea help topics` to list available topics.\n"
