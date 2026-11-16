"""Built-in help for PeaLang: callable inside programs and the REPL.

`help("topic")` returns a short reference for the given topic.
`help()` returns an overview listing all known topics.
"""

from __future__ import annotations

_HELP = {
    "overview": (
        "PeaLang help\n"
        "usage:\n"
        "  help()              list all topics\n"
        "  help(\"match\")       detailed help for a topic\n"
        "available topics:\n"
        "  variables, functions, control_flow, match, exceptions, async, types, "
        "list, dict, strings, stats, web, ai, modules, cli"
    ),
    "variables": (
        "Variables & bindings\n"
        "  let x = 5          declare (immutable by convention)\n"
        "  const PI = 3.14    declare a constant\n"
        "  let [a,b] = pair   destructure a list/tuple\n"
        "  let {name} = user  destructure a dict\n"
    ),
    "functions": (
        "Functions\n"
        "  function add(a, b) { return a + b }\n"
        "  function greet(name='world') { ... }\n"
        "  let inc = function(x) { return x + 1 }\n"
        "  function f(...) { ... }            defaults must follow required args\n"
        "  return expr               return a value\n"
    ),
    "control_flow": (
        "Control flow\n"
        "  if cond { ... } else if cond { ... } else { ... }\n"
        "  while cond { ... }\n"
        "  for x in collection { ... }   iterates lists/strings/dicts\n"
        "  for i, x in enumerate(collection) { ... }\n"
        "  break / continue\n"
    ),
    "match": (
        "Pattern matching (statement and expression)\n"
        "  match x {\n"
        "    1 => \"one\",\n"
        "    [a, b] => a + b,\n"
        "    {\"key\": v} => v,\n"
        "    _ => \"other\"\n"
        "  }\n"
        "  wildcard: _ , literal, list, and dict patterns supported\n"
    ),
    "exceptions": (
        "Exceptions\n"
        "  throw expr                 raise a value (string, dict, number...)\n"
        "  try { ... } catch e { ... } finally { ... }\n"
        "  assert cond, \"message\"    assert with a custom message\n"
        "  Runtime errors print a stack trace when raised inside functions\n"
    ),
    "async": (
        "Async & parallel\n"
        "  async function f() { ... }\n"
        "  let x = await f()\n"
        "  PARALLEL { expr1, expr2, expr3 }\n"
    ),
    "types": (
        "Types (optional static layer)\n"
        "  let x: Int = 5\n"
        "  let y: String? = null\n"
        "  let r: Result = ...\n"
        "  type Point = {x: Int, y: Int}\n"
        "  type Result = Ok value | Err message\n"
        "  trait MyTrait   (marker interface)\n"
        "  erase_types strips annotations before runtime\n"
    ),
    "list": (
        "Lists\n"
        "  let xs = [1, 2, 3]\n"
        "  xs[0], xs[1:], xs[-1]\n"
        "  [x * 2 for x in xs if x > 1]         list comprehension\n"
        "  {k: v for [k,v] in items}             dict comprehension\n"
        "  len(xs), sum(xs), sorted(xs), reversed(xs)\n"
        "  map(f, xs), filter(f, xs), all(xs), any(xs)\n"
    ),
    "dict": (
        "Dicts\n"
        "  let d = {\"a\": 1, \"b\": 2}\n"
        "  d[\"a\"], d.get(\"a\", default), d.has(\"a\")\n"
        "  keys(d), values(d), items(d)\n"
        "  merge(d1, d2), deep_merge(d1, d2)\n"
        "  get_path(d, \"a.b.c\", default)\n"
    ),
    "strings": (
        "Strings\n"
        "  \"hello\" + \" world\"                    concat\n"
        "  \"{x}\" inside double-quoted strings       interpolation syntax\n"
        "  upper(s), lower(s), trim(s)\n"
        "  split(s, sep), strip_prefix, strip_suffix\n"
        "  replace(s, a, b), repeat(s, n)\n"
        "  contains(s, sub), starts_with(s, p), ends_with(s, p)\n"
        "  pad_start(s, width, fill), pad_end(s, width, fill)\n"
        "  snake_case(s), kebab_case(s), slugify(s)\n"
    ),
    "stats": (
        "Statistics & numerics (std.stats)\n"
        "  Imported as: let stats = std.stats  (or registered by default)\n"
        "  Provided by the pealang.numerics module\n"
        "  mean, median, stddev, corr  (see std.stats for full list)\n"
    ),
    "web": (
        "Web (std.web)\n"
        "  let app = web.app()\n"
        "  app.enable_cors(\"*\")\n"
        "  app.get(\"/path\", handlerFn)\n"
        "  app.post(\"/path\", handlerFn)\n"
        "  app.serve(\"127.0.0.1\", 8080)\n"
        "  web.health()  web.json(x)  web.text(s)  web.envelope(data, meta)\n"
        "  web.created(x)  web.not_found(msg)  app.dispatch(method, path)\n"
    ),
    "ai": (
        "AI (std.ai)\n"
        "  set_ai_key(\"openai\", \"sk-...\")\n"
        "  get_ai_status()\n"
        "  list_ai_providers()\n"
        "  run_ai_query(\"openai\", \"gpt-4\", \"prompt\")\n"
        "  CloudModel / LocalModel / AIConfig (see pea_ai module)\n"
    ),
    "modules": (
        "Modules\n"
        "  import \"./file.pea\"              import a file\n"
        "  import \"./file.pea\" as alias      import with alias\n"
        "  export name                       re-export from a module\n"
        "  Modules export their top-level bindings\n"
    ),
    "cli": (
        "CLI\n"
        "  pea run FILE.pea        run a script\n"
        "  pea eval -e EXPR        evaluate an expression\n"
        "  pea repl                interactive REPL\n"
        "  pea serve FILE.pea      serve as an HTTP app\n"
        "  pea scaffold fastapi ./dir   generate a service skeleton\n"
        "  pea doctor              environment diagnostics\n"
        "  pea info                version + available namespaces\n"
        "  pea --help              command list\n"
    ),
}

def help(topic: str | None = None) -> str:
    """Return reference information for *topic*, or an overview if omitted."""
    if topic is None:
        return _HELP["overview"]
    key = topic.lower()
    for name, text in _HELP.items():
        if name == key or name.startswith(key):
            return text
    # fall back to substring only for longer queries
    if len(key) >= 3:
        for name, text in _HELP.items():
            if key in name:
                return text
    return f"Unknown topic '{topic}'. Available topics: {', '.join(sorted(_HELP))}"
