
"""PeaLang v0.73 ONNX, tensor interchange, and governed query planning."""
from __future__ import annotations
from dataclasses import dataclass,field,asdict
from typing import Any,Callable
import json,re
from .data import DataFrame

class ModelInteropError(RuntimeError): pass

@dataclass(frozen=True)
class TensorSpec:
    name:str
    shape:tuple[int|None,...]
    dtype:str="float32"

class TensorBridge:
    @staticmethod
    def from_dataframe(frame:DataFrame,columns):
        rows=frame.to_dicts(); return [[float(r.get(c,0) or 0) for c in columns] for r in rows]
    @staticmethod
    def to_dataframe(tensor,columns=None):
        values=tensor.detach().cpu().tolist() if hasattr(tensor,"detach") else tensor.tolist() if hasattr(tensor,"tolist") else list(tensor)
        if values and not isinstance(values[0],(list,tuple)): values=[[x] for x in values]
        columns=list(columns or [f"f{i}" for i in range(len(values[0]) if values else 0)])
        return DataFrame([{c:row[i] for i,c in enumerate(columns)} for row in values])
    @staticmethod
    def to_torch(frame,columns,dtype=None):
        try: import torch
        except ImportError as exc: raise ModelInteropError("PyTorch support requires torch") from exc
        return torch.tensor(TensorBridge.from_dataframe(frame,columns),dtype=dtype or torch.float32)

@dataclass
class ONNXModel:
    path:str
    providers:list[str]|None=None
    _session:Any=field(default=None,repr=False)
    def load(self):
        if self._session is not None:return self
        try: import onnxruntime as ort
        except ImportError as exc: raise ModelInteropError("ONNX Runtime support requires onnxruntime") from exc
        self._session=ort.InferenceSession(self.path,providers=self.providers or ort.get_available_providers()); return self
    def inputs(self):
        self.load(); return [TensorSpec(x.name,tuple(x.shape),x.type) for x in self._session.get_inputs()]
    def predict(self,inputs):
        self.load(); return dict(zip([x.name for x in self._session.get_outputs()],self._session.run(None,inputs)))
    def predict_frame(self,frame:DataFrame,features,input_name=None,output_columns=None):
        try: import numpy as np
        except ImportError as exc: raise ModelInteropError("ONNX DataFrame inference requires numpy") from exc
        self.load(); name=input_name or self._session.get_inputs()[0].name
        outputs=self._session.run(None,{name:np.asarray(TensorBridge.from_dataframe(frame,features),dtype=np.float32)})
        values=outputs[0]; cols=output_columns or [f"prediction_{i}" for i in range(values.shape[1] if len(values.shape)>1 else 1)]
        return TensorBridge.to_dataframe(values,cols)

@dataclass(frozen=True)
class QueryPolicy:
    allowed_datasets:tuple[str,...]=()
    allowed_operations:tuple[str,...]=("select","filter","group","aggregate","sort","limit")
    maximum_limit:int=1000
    require_approval_for:tuple[str,...]=("export","delete","update","join_sensitive")

@dataclass
class QueryPlan:
    dataset:str
    operations:list[dict[str,Any]]
    original_request:str
    approved:bool=False
    diagnostics:list[str]=field(default_factory=list)
    def to_dict(self):return asdict(self)

class GovernedQueryPlanner:
    """Rule-first planner. An optional model callback can propose a plan, but policy validation is authoritative."""
    def __init__(self,policy:QueryPolicy,model:Callable[[str],dict]|None=None): self.policy=policy;self.model=model
    def propose(self,request,dataset=None):
        if self.model: raw=self.model(request)
        else:
            limit_match=re.search(r"\b(?:top|limit)\s+(\d+)\b",request,re.I); limit=min(int(limit_match.group(1)),self.policy.maximum_limit) if limit_match else min(100,self.policy.maximum_limit)
            raw={"dataset":dataset or (self.policy.allowed_datasets[0] if len(self.policy.allowed_datasets)==1 else ""),"operations":[{"operation":"select","columns":["*"]},{"operation":"limit","count":limit}]}
        plan=QueryPlan(raw.get("dataset",dataset or ""),list(raw.get("operations",[])),request)
        return self.validate(plan)
    def validate(self,plan:QueryPlan):
        errors=[]
        if self.policy.allowed_datasets and plan.dataset not in self.policy.allowed_datasets: errors.append("dataset is not allowed")
        for op in plan.operations:
            name=op.get("operation","")
            if name not in self.policy.allowed_operations: errors.append(f"operation is not allowed: {name}")
            if name=="limit" and int(op.get("count",0))>self.policy.maximum_limit: errors.append("limit exceeds policy")
            if name in self.policy.require_approval_for: plan.approved=False; errors.append(f"approval required: {name}")
        plan.diagnostics=errors; return plan
    def approve(self,plan,actor,reason):
        if not actor or not reason: raise ValueError("actor and reason are required")
        plan.approved=True; plan.diagnostics=[d for d in plan.diagnostics if not d.startswith("approval required")]; return plan

