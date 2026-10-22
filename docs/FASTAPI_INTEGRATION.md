# FastAPI Integration

Install the example dependencies separately:

```bash
python -m pip install fastapi uvicorn pydantic
```

Run the bundled example from `examples/embedding`:

```bash
uvicorn fastapi_app:app --reload
```

The FastAPI endpoint validates the request with Pydantic, converts the model into a PeaLang dictionary, invokes an exported rule, and returns the result. Production services should load scripts at startup, use explicit capability permissions, set execution budgets, and translate `PeaError` into controlled HTTP error responses.
