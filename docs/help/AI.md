# AI Help
- Check `ai.info()` for provider/model/base URL configuration; it never returns the credential value.
- Missing `api_key_env` values fail before the request.
- `openai-compatible` expects a chat-completions endpoint under the configured base URL.
- Use the mock provider for offline tests.
- Schema errors identify the missing or incorrectly typed field.
