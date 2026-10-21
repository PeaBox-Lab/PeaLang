# Portable Skills Guide
A v0.6 PeaLang skill is a JSON file with at least `name` and `prompt`. `description` is recommended.

## Load
`skill.load("skills/summarise.json")` loads and registers the skill for the current interpreter.

## Inspect
`skill.list()` returns loaded names. `skill.get(name)` returns the skill dictionary.

## Render
`skill.render(name, values)` replaces `{key}` placeholders with values. Rendering is deliberately simple in v0.6; it has no conditionals, loops or escaping language.

## Use with AI
Render the prompt first, then pass it to `ai.ask`. Keep provider configuration and credentials outside skills so the same skill stays portable.
