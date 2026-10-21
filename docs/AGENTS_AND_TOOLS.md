# Agents and Tools Guide v0.8.0

## Philosophy
v0.8 establishes explicit capabilities before autonomous behaviour. Agents are dictionaries containing a name, instruction, allowed tool names and optional model. Tools are registered callables with metadata.

## Register a PeaLang function as a tool
```pea
function lookup(id) { return "employee:" + str(id) }
tool.register("lookup", lookup, "Lookup an employee", "safe")
```

## Define an agent
```pea
let analyst = agent.define("analyst", "Analyse the supplied data.", ["lookup"])
```

## Run inference
`agent.run(analyst, input)` delegates text generation to the current `ai` provider and returns `agent`, `text`, `provider`, `model`, and the configured tool-name list.

## Explicit tool execution
`agent.tool(analyst, "lookup", [42])` checks the agent allowlist and then invokes the tool. A registered-but-unlisted tool is denied.

## Metadata
`tool.describe(name)` returns name, description and permission label. The permission label is metadata in v0.8; enforcement is by explicit tool-name allowlist.

## What is not yet implemented
No autonomous tool selection, model function-calling protocol, agent loop, planner, memory store, delegation, background execution, approval UI, sandbox or remote tool protocol exists in v0.8.
