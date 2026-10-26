



"""PeaLang v0.69 DAG definitions, validation, planning, and local execution."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from collections import defaultdict, deque

class DAGError(RuntimeError): pass
class DuplicateTaskError(DAGError): pass
class MissingDependencyError(DAGError): pass
class CycleError(DAGError): pass
class TaskExecutionError(DAGError):
    def __init__(self, task_id, cause):
        super().__init__(f"Task {task_id!r} failed: {cause}")
        self.task_id=task_id; self.cause=cause

@dataclass
class Task:
    task_id: str
    run: Callable[..., Any]
    depends_on: tuple[str,...]=()
    metadata: dict[str,Any]=field(default_factory=dict)

@dataclass
class DAGValidation:
    valid: bool
    errors: list[str]=field(default_factory=list)
    warnings: list[str]=field(default_factory=list)
    order: list[str]=field(default_factory=list)

class DAG:
    def __init__(self, dag_id:str, description:str=""):
        self.dag_id=dag_id; self.description=description; self.tasks:dict[str,Task]={}
    def add(self,task:Task):
        if task.task_id in self.tasks: raise DuplicateTaskError(task.task_id)
        if task.task_id in task.depends_on: raise CycleError(f"Task {task.task_id!r} depends on itself")
        self.tasks[task.task_id]=task; return self
    def task(self,task_id,depends_on=(),metadata=None):
        def decorate(fn):
            self.add(Task(task_id,fn,tuple(depends_on),metadata or {})); return fn
        return decorate
    def validate(self,strict=True):
        errors=[]; warnings=[]
        for task in self.tasks.values():
            missing=[x for x in task.depends_on if x not in self.tasks]
            if missing: errors.append(f"Task {task.task_id!r} has missing dependencies: {', '.join(missing)}")
            if not task.depends_on: warnings.append(f"Task {task.task_id!r} is a root task")
        order=[]
        if not errors:
            try: order=self.topological_order()
            except CycleError as exc: errors.append(str(exc))
        result=DAGValidation(not errors,errors,warnings,order)
        if strict and errors:
            if any("missing dependencies" in e for e in errors): raise MissingDependencyError("; ".join(errors))
            raise CycleError("; ".join(errors))
        return result
    def topological_order(self):
        indegree={k:0 for k in self.tasks}; children=defaultdict(list)
        for task in self.tasks.values():
            for dep in task.depends_on:
                if dep not in self.tasks: raise MissingDependencyError(f"Unknown dependency {dep!r}")
                indegree[task.task_id]+=1; children[dep].append(task.task_id)
        ready=deque(sorted(k for k,v in indegree.items() if v==0)); order=[]
        while ready:
            current=ready.popleft(); order.append(current)
            for child in sorted(children[current]):
                indegree[child]-=1
                if indegree[child]==0: ready.append(child)
        if len(order)!=len(self.tasks):
            blocked=sorted(k for k,v in indegree.items() if v>0)
            raise CycleError("Dependency cycle detected involving: "+", ".join(blocked))
        return order
    def layers(self):
        self.validate(); remaining=set(self.tasks); done=set(); layers=[]
        while remaining:
            layer=sorted(t for t in remaining if set(self.tasks[t].depends_on)<=done)
            if not layer: raise CycleError("Unable to produce execution layers")
            layers.append(layer); done.update(layer); remaining.difference_update(layer)
        return layers
    def describe(self):
        validation=self.validate(strict=False)
        return {"dag_id":self.dag_id,"description":self.description,"valid":validation.valid,
                "order":validation.order,"layers":self.layers() if validation.valid else [],
                "tasks":{k:{"depends_on":list(v.depends_on),"metadata":v.metadata} for k,v in self.tasks.items()},
                "errors":validation.errors,"warnings":validation.warnings}
    def run(self,inputs=None):
        self.validate(); results={}; inputs=inputs or {}
        for task_id in self.topological_order():
            task=self.tasks[task_id]
            dependencies={name:results[name] for name in task.depends_on}
            try: results[task_id]=task.run(dependencies=dependencies,inputs=inputs)
            except TypeError:
                try: results[task_id]=task.run(dependencies)
                except TypeError:
                    try: results[task_id]=task.run()
                    except Exception as exc: raise TaskExecutionError(task_id,exc) from exc
            except Exception as exc: raise TaskExecutionError(task_id,exc) from exc
        return results

def dag_from_dict(spec,registry):
    graph=DAG(spec["dag_id"],spec.get("description",""))
    for item in spec.get("tasks",[]):
        fn_name=item.get("callable",item["task_id"])
        if fn_name not in registry: raise DAGError(f"Callable {fn_name!r} is not registered")
        graph.add(Task(item["task_id"],registry[fn_name],tuple(item.get("depends_on",())),item.get("metadata",{})))
    return graph




