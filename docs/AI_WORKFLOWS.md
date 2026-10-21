# AI Workflows Guide v0.6.0

## Configure
`ai.configure(options)` stores provider, model, base URL, credential environment-variable name and timeout. `ai.info()` returns non-secret configuration.

## Providers
### mock
Local deterministic provider for tests and examples. `ai.ask(prompt)` returns the prompt as `text`.

### openai-compatible
Posts JSON to `{base_url}/chat/completions` with `model` and a single user message. If `api_key_env` is configured, its environment value is sent as a Bearer token. Responses must expose `choices[0].message.content`.

## Ask
`ai.ask(prompt, options?)` returns a dictionary containing `text`, `provider`, `model`, `usage`, and `raw`.

## Structured output
`ai.validate(data, schema)` validates dictionaries without making an AI call. `ai.extract(input, schema, options?)` asks a non-mock provider for JSON and validates the result. The mock provider accepts dictionary input and projects schema keys for deterministic tests.

## Schema types
`string`, `number`, `boolean`, `list`, `dictionary`, `any`.

## Failure model
Missing credentials, unknown providers, request failures, malformed provider responses and schema mismatches produce `PeaError`. v0.6 does not add try/catch or automatic retries to `ai.ask`.

## Privacy
Anything sent to a configured remote endpoint leaves the PeaLang process. Do not submit confidential content unless the selected endpoint and organisational controls permit it.
