

"""Stable Python embedding API for PeaLang."""
from __future__ import annotations
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
import time
from typing import Any, Callable, Mapping
from .errors import PeaError
from .interpreter import Interpreter, UserFunction
from .parser import parse_source
from .resource_limits import ResourceBudget,ResourceLimits,ResourceLimitExceeded,estimated_size

class PeaRuntimeError(PeaError): pass
class PeaPermissionError(PeaRuntimeError): pass
class PeaResourceLimitError(PeaRuntimeError): pass

@dataclass(frozen=True)
class RuntimeOptions:
    permissions: frozenset[str] = frozenset()
    max_execution_ms: int = 1000
    max_instructions: int = 100_000
    max_call_depth: int = 100
    max_memory_bytes: int = 16 * 1024 * 1024
    max_stack_depth: int = 1024
    max_collection_items: int = 100_000
    max_output_bytes: int = 1024 * 1024
    max_http_requests: int = 32
    max_file_read_bytes: int = 8 * 1024 * 1024
    allow_process: bool = False

    @classmethod
    def safe_defaults(cls): return cls()

@dataclass(frozen=True)
class ExecutionResult:
    value: Any
    instructions: int
    elapsed_ms: float

@dataclass
class HostFunction:
    name: str
    function: Callable[..., Any]
    permission: str | None = None


def to_pea(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)): return value
    if is_dataclass(value): return {k: to_pea(v) for k,v in asdict(value).items()}
    if hasattr(value, 'model_dump'): return to_pea(value.model_dump())
    if isinstance(value, Mapping): return {str(k): to_pea(v) for k,v in value.items()}
    if isinstance(value, (list, tuple, set)): return [to_pea(v) for v in value]
    raise TypeError(f'Unsupported host value: {type(value).__name__}')


def from_pea(value: Any, target_type: type | None = None) -> Any:
    if target_type is None: return value
    if hasattr(target_type, 'model_validate'): return target_type.model_validate(value)
    if is_dataclass(target_type): return target_type(**value)
    return target_type(value)

class PeaModule:
    def __init__(self, runtime: 'PeaRuntime', interpreter: Interpreter, exports: dict[str, Any], source_name: str):
        self.runtime, self.interpreter, self.exports, self.source_name = runtime, interpreter, exports, source_name

    def get_export(self, name: str) -> Any:
        if name not in self.exports: raise PeaRuntimeError(f"Module does not export '{name}'")
        value=self.exports[name]
        return '<function>' if isinstance(value,UserFunction) else value

    def call(self, name: str, *args: Any) -> Any:
        if name not in self.exports: raise PeaRuntimeError(f"Module does not export function '{name}'")
        fn=self.exports[name]
        if not isinstance(fn,UserFunction) and not callable(fn): raise PeaRuntimeError(f"Export '{name}' is not callable")
        prepared=[to_pea(x) for x in args]
        started=time.perf_counter();self.runtime._start_budget(self.interpreter)
        try:
            value=self.interpreter.invoke_user_function(fn,prepared) if isinstance(fn,UserFunction) else fn(*prepared)
            return value
        finally:self.runtime._finish_budget(started)

    def call_typed(self, name: str, *args: Any, output_type: type):
        return from_pea(self.call(name,*args),output_type)

class PeaRuntime:
    """Embed PeaLang without exposing arbitrary Python reflection or imports."""
    def __init__(self, options: RuntimeOptions | None = None, output: Callable[[Any],None] | None = None):
        self.options=options or RuntimeOptions.safe_defaults();self.output=output or (lambda value: None)
        self.host_functions: dict[str,HostFunction]={};self.last_result:ExecutionResult|None=None
        self._instructions=0;self._deadline=0.0

    def register_function(self, name: str, function: Callable[...,Any], permission: str|None=None):
        if not name or not callable(function): raise ValueError('A name and callable are required')
        self.host_functions[name]=HostFunction(name,function,permission);return self

    def register_module(self, name: str, functions: Mapping[str,Callable[...,Any]], permission_prefix: str|None=None):
        for child,fn in functions.items():
            permission=f'{permission_prefix}.{child}' if permission_prefix else None
            self.register_function(f'{name}.{child}',fn,permission)
        return self

    def _host_namespace(self):
        root={}
        for full,item in self.host_functions.items():
            parts=full.split('.');node=root
            for part in parts[:-1]:node=node.setdefault(part,{})
            def wrapper(*args,_item=item):
                if _item.permission and _item.permission not in self.options.permissions:
                    raise PeaPermissionError(f"Permission '{_item.permission}' is required for '{_item.name}'")
                return to_pea(_item.function(*args))
            node[parts[-1]]=wrapper
        return root

    def _new_interpreter(self,source_name='<embedded>'):
        base=Path(source_name).parent if source_name not in ('<embedded>','<input>') else Path('.')
        vm=Interpreter(output=self.output,base_dir=base,allow_process=self.options.allow_process,debug_hook=self._budget_hook,permissions=self.options.permissions)
        for name,value in self._host_namespace().items():vm.global_env.define(name,value,True)
        return vm

    def _start_budget(self,vm):
        self._instructions=0;self._deadline=time.perf_counter()+(self.options.max_execution_ms/1000)
        self._resource_budget=ResourceBudget(ResourceLimits(self.options.max_execution_ms,self.options.max_instructions,self.options.max_memory_bytes,self.options.max_call_depth,self.options.max_stack_depth,self.options.max_collection_items,self.options.max_output_bytes,self.options.max_http_requests,self.options.max_file_read_bytes))
        vm.debug_hook=self._budget_hook

    def _budget_hook(self,vm,node):
        self._instructions+=1
        try:
            self._resource_budget.instruction();self._resource_budget.set_recursion(len(vm.call_stack));self._resource_budget.set_stack(len(getattr(vm,'call_stack',[])));self._resource_budget.deadline()
        except ResourceLimitExceeded as exc:raise PeaResourceLimitError(str(exc)) from exc
        if self._instructions>self.options.max_instructions:raise PeaResourceLimitError('Instruction limit exceeded')
        if len(vm.call_stack)>self.options.max_call_depth:raise PeaResourceLimitError('Call-depth limit exceeded')
        if time.perf_counter()>self._deadline:raise PeaResourceLimitError('Execution timeout exceeded')

    def _finish_budget(self,started):
        self.last_result=ExecutionResult(None,self._instructions,(time.perf_counter()-started)*1000)

    def load(self, source: str, source_name='<embedded>') -> PeaModule:
        vm=self._new_interpreter(source_name);program=parse_source(source,source_name)
        vm.module_exports=set();started=time.perf_counter();self._start_budget(vm)
        try:
            vm.run(program,source_name)
            names=vm.module_exports or {k for k in vm.global_env.values if k not in vm.global_env.const}
            exports={n:vm.global_env.values[n] for n in names if n in vm.global_env.values}
            return PeaModule(self,vm,exports,source_name)
        finally:self._finish_budget(started)

    def load_file(self,path:str|Path)->PeaModule:
        path=Path(path).resolve();return self.load(path.read_text(encoding='utf-8'),str(path))

    def eval(self, source: str, source_name='<embedded>') -> ExecutionResult:
        vm=self._new_interpreter(source_name);started=time.perf_counter();self._start_budget(vm)
        try:
            value=vm.run(parse_source(source,source_name),source_name)
            result=ExecutionResult(value,self._instructions,(time.perf_counter()-started)*1000);self.last_result=result;return result
        finally:
            if self.last_result is None:self._finish_budget(started)


