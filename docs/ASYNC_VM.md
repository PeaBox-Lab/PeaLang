# Native Async VM

PeaLang 0.26 adds `async function`, `await`, the `AWAIT` bytecode operation, cooperative VM suspension, Python awaitable host integration, cancellation tokens, and execution deadlines.

```pea
async function load_employee(id) {
    return await hr.get(id)
}
export load_employee
```

```python
runtime = AsyncVMRuntime(RuntimeOptions(
    permissions=frozenset({"hr.get"}),
    max_execution_ms=500,
))
runtime.register_async_function("hr.get", get_employee, "hr.get")
module = await runtime.load_async(source, "rules.pea")
employee = await module.call_async("load_employee", "E1001")
```

The VM suspends at `AWAIT`, returns control to the Python event loop, awaits the host operation, pushes its result back onto the operand stack, and resumes the preserved instruction pointer and call frames.

Use `CancellationToken.cancel()` for cooperative cancellation. Deadlines are enforced with `asyncio.wait_for`.
