# Workflows and Concurrency Guide

## Structured workflows
Use `workflow.step` when you want named intermediate results and `workflow.result` to aggregate them.

```pea
let source = workflow.step("source", json.read("input.json"))
let count = workflow.step("count", len(source.value))
let run = workflow.result("daily-report", [source, count])
assert run.ok
```

## Parallel work
Use a parallel expression for independent expressions:
```pea
let responses = parallel {
    http.get("https://example.com/a")
    http.get("https://example.com/b")
}
```
Keep operations independent. The v0.5 runtime caps a block at eight worker threads and returns values in source order.

## Tasks
`task.sleep(seconds)` pauses synchronously. `task.retry(callable, attempts?, delay?)` is a low-level helper for host/user callable values. Because PeaLang currently lacks anonymous functions, retry is most useful with a zero-argument function already defined by the program.

## Failure handling
A failed parallel expression raises an error when its future result is collected. v0.5 has no cancellation syntax, timeout syntax on `parallel`, or language-level try/catch.
