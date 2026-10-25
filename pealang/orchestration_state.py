"""PeaLang v0.70 durable orchestration state, retries, idempotency, backfill, and scheduling."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable
import hashlib, json, random, sqlite3, time, uuid

class RunState(str, Enum):
    PENDING="pending"; RUNNING="running"; SUCCESS="success"; FAILED="failed"; SKIPPED="skipped"

@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1
    initial_delay: float = 0.0
    multiplier: float = 2.0
    max_delay: float = 60.0
    jitter: float = 0.0
    def delay(self, attempt:int)->float:
        base=min(self.max_delay,self.initial_delay*(self.multiplier**max(0,attempt-1)))
        return max(0.0,base + (random.uniform(-self.jitter,self.jitter) if self.jitter else 0.0))

@dataclass(frozen=True)
class Schedule:
    every_seconds: int
    start_at: datetime | None = None
    def occurrences(self,start:datetime,end:datetime)->list[datetime]:
        if self.every_seconds <= 0: raise ValueError("every_seconds must be positive")
        cur=self.start_at or start
        if cur < start:
            cur += timedelta(seconds=((start-cur).total_seconds()//self.every_seconds)*self.every_seconds)
            while cur < start: cur += timedelta(seconds=self.every_seconds)
        out=[]
        while cur <= end:
            out.append(cur); cur += timedelta(seconds=self.every_seconds)
        return out

class StateStore:
    def begin(self,*a,**k): raise NotImplementedError
    def finish(self,*a,**k): raise NotImplementedError
    def successful(self,*a,**k): raise NotImplementedError
    def attempts(self,*a,**k): raise NotImplementedError

class SQLiteStateStore(StateStore):
    def __init__(self,path:str|Path=":memory:"):
        self.path=str(path); self.db=sqlite3.connect(self.path)
        self.db.execute("""create table if not exists task_runs(
          dag_id text, task_id text, logical_date text, idempotency_key text,
          attempt integer, state text, started_at text, finished_at text,
          result_json text, error text, run_id text,
          primary key(dag_id,task_id,logical_date,attempt))""")
        self.db.execute("create unique index if not exists ux_task_key on task_runs(dag_id,task_id,idempotency_key) where state='success'")
        self.db.commit()
    def begin(self,dag_id,task_id,logical_date,key,attempt):
        rid=str(uuid.uuid4()); now=datetime.now(timezone.utc).isoformat()
        self.db.execute("insert into task_runs values(?,?,?,?,?,?,?,?,?,?,?)",(dag_id,task_id,logical_date,key,attempt,RunState.RUNNING.value,now,None,None,None,rid)); self.db.commit(); return rid
    def finish(self,run_id,state,result=None,error=None):
        payload=json.dumps(result,default=str) if result is not None else None
        self.db.execute("update task_runs set state=?,finished_at=?,result_json=?,error=? where run_id=?",(RunState(state).value,datetime.now(timezone.utc).isoformat(),payload,error,run_id)); self.db.commit()
    def successful(self,dag_id,task_id,key):
        row=self.db.execute("select result_json from task_runs where dag_id=? and task_id=? and idempotency_key=? and state='success' order by attempt desc limit 1",(dag_id,task_id,key)).fetchone()
        return (True,json.loads(row[0]) if row and row[0] else None) if row else (False,None)
    def attempts(self,dag_id,task_id,logical_date):
        return self.db.execute("select count(*) from task_runs where dag_id=? and task_id=? and logical_date=?",(dag_id,task_id,logical_date)).fetchone()[0]
    def history(self,dag_id=None):
        q="select dag_id,task_id,logical_date,idempotency_key,attempt,state,error,run_id from task_runs"; args=()
        if dag_id: q+=" where dag_id=?"; args=(dag_id,)
        return [dict(zip(("dag_id","task_id","logical_date","idempotency_key","attempt","state","error","run_id"),r)) for r in self.db.execute(q+" order by logical_date,task_id,attempt",args)]

def idempotency_key(dag_id:str,task_id:str,logical_date:str,inputs:dict[str,Any]|None=None)->str:
    raw=json.dumps([dag_id,task_id,logical_date,inputs or {}],sort_keys=True,default=str,separators=(",",":"))
    return hashlib.sha256(raw.encode()).hexdigest()

@dataclass
class OrchestrationResult:
    logical_date: str
    results: dict[str,Any]=field(default_factory=dict)
    states: dict[str,str]=field(default_factory=dict)
    attempts: dict[str,int]=field(default_factory=dict)

class DurableDAGRunner:
    def __init__(self,store:StateStore|None=None,sleep:Callable[[float],None]=time.sleep): self.store=store or SQLiteStateStore(); self.sleep=sleep
    def run(self,dag,inputs=None,logical_date=None,retry:RetryPolicy|None=None):
        dag.validate(); inputs=inputs or {}; retry=retry or RetryPolicy(); logical_date=logical_date or datetime.now(timezone.utc).isoformat(); out=OrchestrationResult(logical_date)
        for task_id in dag.topological_order():
            task=dag.tasks[task_id]; key=idempotency_key(dag.dag_id,task_id,logical_date,inputs)
            ok,old=self.store.successful(dag.dag_id,task_id,key)
            if ok: out.results[task_id]=old; out.states[task_id]=RunState.SKIPPED.value; out.attempts[task_id]=0; continue
            deps={x:out.results[x] for x in task.depends_on}; last=None
            for attempt in range(1,max(1,retry.max_attempts)+1):
                rid=self.store.begin(dag.dag_id,task_id,logical_date,key,attempt); out.attempts[task_id]=attempt
                try:
                    try: value=task.run(dependencies=deps,inputs=inputs)
                    except TypeError:
                        try: value=task.run(deps)
                        except TypeError: value=task.run()
                    self.store.finish(rid,RunState.SUCCESS,value); out.results[task_id]=value; out.states[task_id]=RunState.SUCCESS.value; last=None; break
                except Exception as exc:
                    last=exc; self.store.finish(rid,RunState.FAILED,error=str(exc)); out.states[task_id]=RunState.FAILED.value
                    if attempt < retry.max_attempts:
                        delay=retry.delay(attempt)
                        if delay: self.sleep(delay)
            if last is not None:
                from .orchestration import TaskExecutionError
                raise TaskExecutionError(task_id,last) from last
        return out
    def backfill(self,dag,start:datetime,end:datetime,schedule:Schedule,inputs_factory=None,retry=None):
        return [self.run(dag,(inputs_factory(dt) if inputs_factory else {}),dt.isoformat(),retry) for dt in schedule.occurrences(start,end)]

