# Tools Help
Register a callable with `tool.register`. User-defined PeaLang functions are supported. `tool.list` returns names and `tool.describe` returns metadata. Tool names must be explicitly allowed by an agent before `agent.tool` can invoke them. Registered tools execute in-process and are not sandboxed.
