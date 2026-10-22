# VM-backed Embedding

```python
from pealang import VMRuntime

runtime = VMRuntime(max_instructions=50_000)
module = runtime.load('''
function calculate(amount, rate) {
    return amount * rate
}
export calculate
''')

print(module.call("calculate", 100000, 0.15))
```

`VMRuntime` accepts host globals for approved callable functions. Use only explicitly selected functions and portable values. `VMModule.call` invokes exported compiled functions using VM frames.

The mature `PeaRuntime` capability model remains the recommended interface for security-sensitive embedding until capability enforcement is unified with `VMRuntime`.
