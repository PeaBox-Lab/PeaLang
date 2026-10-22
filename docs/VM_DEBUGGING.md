# VM Debugging

The 0.21 VM exposes resumable execution state.

```python
from pealang import compile_source_to_bytecode, VirtualMachine

module = compile_source_to_bytecode(source, "rules.pea")
vm = VirtualMachine(output=print)
vm.module = module
vm.add_breakpoint(4, "rules.pea")
event = vm.run(module)
print(event)
print(vm.stack_trace())
vm.continue_run()
```

A breakpoint event contains `reason`, `source`, `line`, and `frame`. Stack records include frame ID, function name, source, current line, and locals. `step()` advances one VM instruction. This API is the foundation for VM-backed DAP integration, but the existing DAP adapter remains interpreter-backed in 0.21.
