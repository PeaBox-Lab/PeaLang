# Profiling, Coverage and Observability

PeaLang 0.30 adds production-hardening instrumentation around the bytecode VM.

## Profile

```bash
pea profile app.pea
```

The report includes elapsed time, executed instruction count, opcode counts, per-function instruction activity, and executed source lines.

## Benchmark

```bash
pea benchmark app.pea
```

The default CLI benchmark performs 20 VM runs and reports minimum, median, mean, and maximum elapsed milliseconds.

## Python API

```python
profiler = Profiler().start()
coverage = Coverage()
instrumentation = Instrumentation(profiler, coverage)
vm = VirtualMachine(instrumentation=instrumentation)
vm.run(module)
profiler.stop()
```

`Observer` is deliberately transport neutral. Hosts can translate `TraceEvent` objects to OpenTelemetry spans/events without making OpenTelemetry a core PeaLang dependency.
