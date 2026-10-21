# PeaLang AI Development Handover v0.6.0

## Architecture
Lexer -> Parser -> typed AST -> optional tooling -> Interpreter. `stdlib.py` supplies automation/workflow capabilities. `ai.py` defines AI configuration, adapters and schema validation. `skills.py` manages portable JSON prompt skills.

## AI contract
`ai.configure(options)` stores provider/model/base URL/api-key environment-variable name/timeout. `ai.ask` normalises responses. `ai.validate` validates local dictionaries. `ai.extract` validates provider-produced JSON. v0.6 providers are `mock` and `openai-compatible`.

## Skills
JSON files require `name` and `prompt`. `skill.render` performs simple `{name}` replacement. Skills contain no provider credentials.

## Security
Never embed secrets. Remote prompts may leave the machine. Mock tests are preferred for CI. The runtime is not sandboxed.

## Required release documentation
Every release must include detailed README, cumulative changelog, full release notes, roadmap, additions/improvements, language basics, foundations, user guide, help files, feature/reference docs, test report, cumulative version history and updated handover.

## Next
v0.6.1 AI hardening, then v0.7 project/package model. Do not jump directly to autonomous agents without an explicit tool-permission contract.
