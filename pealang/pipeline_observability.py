
"""Pipeline metrics, SLA evaluation, alerts, and audit reporting for PeaLang v0.71."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Callable
import json, statistics

@dataclass(frozen=True)
class SLAPolicy:
    max_duration_seconds: float | None = None
    minimum_success_rate: float = 1.0
    maximum_failed_tasks: int = 0

@dataclass
class RunMetric:
    dag_id:str; run_id:str; started_at:str; finished_at:str; duration_seconds:float; state:str; task_count:int; failed_tasks:int=0; metadata:dict[str,Any]|None=None

@dataclass(frozen=True)
class Alert:
    severity:str; code:str; message:str; dag_id:str; run_id:str

class MetricsRegistry:
    def __init__(self): self.runs=[]
    def record(self,metric:RunMetric): self.runs.append(metric); return metric
    def summary(self,dag_id=None):
        rows=[r for r in self.runs if dag_id is None or r.dag_id==dag_id]
        if not rows: return {"runs":0,"success_rate":0.0,"average_duration_seconds":0.0,"p95_duration_seconds":0.0}
        durations=sorted(r.duration_seconds for r in rows); idx=max(0,min(len(durations)-1,int((len(durations)-1)*.95)))
        return {"runs":len(rows),"success_rate":sum(r.state=="success" for r in rows)/len(rows),"average_duration_seconds":statistics.fmean(durations),"p95_duration_seconds":durations[idx],"failed_tasks":sum(r.failed_tasks for r in rows)}

class SLAEvaluator:
    def evaluate(self,metric:RunMetric,policy:SLAPolicy):
        alerts=[]
        if policy.max_duration_seconds is not None and metric.duration_seconds>policy.max_duration_seconds: alerts.append(Alert("critical","SLA_DURATION",f"Duration {metric.duration_seconds:.2f}s exceeded {policy.max_duration_seconds:.2f}s",metric.dag_id,metric.run_id))
        if metric.failed_tasks>policy.maximum_failed_tasks: alerts.append(Alert("critical","SLA_TASK_FAILURES",f"Failed tasks {metric.failed_tasks} exceeded {policy.maximum_failed_tasks}",metric.dag_id,metric.run_id))
        if metric.state!="success" and policy.minimum_success_rate>=1.0: alerts.append(Alert("critical","SLA_RUN_STATE",f"Run ended in {metric.state}",metric.dag_id,metric.run_id))
        return alerts

class AlertRouter:
    def __init__(self): self.handlers=[]
    def add(self,handler:Callable[[Alert],None]): self.handlers.append(handler); return self
    def dispatch(self,alerts):
        for alert in alerts:
            for handler in self.handlers: handler(alert)
        return len(alerts)

class AuditReport:
    @staticmethod
    def build(metric:RunMetric,alerts=None,lineage=None):
        return {"schema":"pealang.audit.v1","generated_at":datetime.now(timezone.utc).isoformat(),"run":asdict(metric),"alerts":[asdict(a) for a in (alerts or [])],"lineage":lineage.to_dict() if lineage else None}
    @staticmethod
    def write(path,report):
        with open(path,"w",encoding="utf-8") as fh: json.dump(report,fh,indent=2,default=str)

