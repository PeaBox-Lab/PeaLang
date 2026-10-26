



# PeaLang v0.69 DAG Orchestration

v0.69 begins the orchestration and governance phase with dependency-safe directed acyclic graphs.

## Capabilities
- Programmatic DAG and task definitions.
- Decorator-based task registration.
- Duplicate-task, missing-dependency, self-dependency, and cycle validation.
- Deterministic topological ordering.
- Parallelizable execution-layer planning.
- Local dependency-result propagation.
- Declarative DAG construction from dictionaries and a callable registry.
- Machine-readable graph descriptions for future schedulers and visual tools.

## Example
```python
from pealang.orchestration import DAG
pipeline = DAG("employee-pipeline")

@pipeline.task("extract")
def extract():
    return [{"id": 1}]

@pipeline.task("transform", depends_on=("extract",))
def transform(dependencies):
    return dependencies["extract"]

print(pipeline.describe())
results = pipeline.run()
```

v0.70 can build persistent task state, retries, backfills, idempotency, and scheduling on this validated DAG model.




