

"""PeaLang 0.84 structured concurrency and resilience primitives."""
from __future__ import annotations
import asyncio, hashlib, json, random, time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Mapping

class CancellationReason(str,Enum):
 MANUAL='manual'; TIMEOUT='timeout'; SHUTDOWN='shutdown'; PARENT='parent'
class CancellationToken:
 def __init__(self,parent=None):self._event=asyncio.Event();self.reason=None;self.parent=parent
 @property
 def cancelled(self):return self._event.is_set() or bool(self.parent and self.parent.cancelled)
 def cancel(self,reason=CancellationReason.MANUAL):self.reason=reason;self._event.set()
 def child(self):return CancellationToken(self)
 def raise_if_cancelled(self):
  if self.cancelled:raise asyncio.CancelledError((self.reason or (self.parent and self.parent.reason) or CancellationReason.PARENT).value)
 async def wait(self):
  if self.cancelled:return
  if not self.parent:await self._event.wait();return
  tasks=[asyncio.create_task(self._event.wait()),asyncio.create_task(self.parent.wait())]
  done,pending=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
  for task in pending:task.cancel()

@dataclass(frozen=True)
class Deadline:
 expires_at:float
 @classmethod
 def after(cls,seconds,clock=time.monotonic):return cls(clock()+max(0,float(seconds)))
 def remaining(self,clock=time.monotonic):return max(0.0,self.expires_at-clock())
 @property
 def expired(self):return self.remaining()<=0

async def run_with_deadline(awaitable,deadline,token=None):
 if token:token.raise_if_cancelled()
 try:return await asyncio.wait_for(awaitable,timeout=deadline.remaining())
 except asyncio.TimeoutError:
  if token:token.cancel(CancellationReason.TIMEOUT)
  raise

@dataclass(frozen=True)
class TaskOutcome:
 name:str;status:str;value:Any=None;error:str|None=None
class StructuredTaskGroup:
 """Fail-fast parent-owned tasks; sibling failure cancels the group."""
 def __init__(self,token=None):self.token=token or CancellationToken();self._tasks={}
 def create_task(self,name,awaitable):
  if name in self._tasks:raise ValueError(f'duplicate task: {name}')
  self.token.raise_if_cancelled();task=asyncio.create_task(awaitable,name=name);self._tasks[name]=task;return task
 async def wait(self):
  if not self._tasks:return ()
  done,pending=await asyncio.wait(self._tasks.values(),return_when=asyncio.FIRST_EXCEPTION)
  failed=any(not t.cancelled() and t.exception() is not None for t in done)
  if failed:
   self.token.cancel(CancellationReason.PARENT)
   for task in pending:task.cancel()
  await asyncio.gather(*pending,return_exceptions=True)
  out=[]
  for name,task in self._tasks.items():
   if task.cancelled():out.append(TaskOutcome(name,'cancelled'))
   elif task.exception():out.append(TaskOutcome(name,'failed',error=f'{task.exception().__class__.__name__}: {task.exception()}'))
   else:out.append(TaskOutcome(name,'completed',task.result()))
  return tuple(out)
 async def cancel(self,reason=CancellationReason.MANUAL):
  self.token.cancel(reason)
  for task in self._tasks.values():task.cancel()
  await asyncio.gather(*self._tasks.values(),return_exceptions=True)

@dataclass(frozen=True)
class RetryPolicyV2:
 max_attempts:int=3;initial_delay:float=.05;max_delay:float=2.0;multiplier:float=2.0;jitter:float=.1
 def __post_init__(self):
  if self.max_attempts<1:raise ValueError('max_attempts must be positive')
class RetrySafetyError(RuntimeError):pass
async def retry_async(operation,policy=RetryPolicyV2(),*,idempotent=False,idempotency_key=None,retryable=(TimeoutError,ConnectionError),sleep=asyncio.sleep,rng=random.random):
 if policy.max_attempts>1 and not (idempotent or idempotency_key):raise RetrySafetyError('retries require idempotent=True or an idempotency_key')
 delay=policy.initial_delay
 for attempt in range(1,policy.max_attempts+1):
  try:return await operation()
  except retryable:
   if attempt==policy.max_attempts:raise
   jitter=delay*policy.jitter*(rng()*2-1);await sleep(max(0,delay+jitter));delay=min(policy.max_delay,delay*policy.multiplier)

class IdempotencyStore:
 def __init__(self):self._records={}
 @staticmethod
 def _fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest()
 async def execute(self,key,payload,operation):
  fingerprint=self._fingerprint(payload)
  if key in self._records:
   old,result=self._records[key]
   if old!=fingerprint:raise RetrySafetyError('idempotency key reused with different payload')
   return result
  result=await operation();self._records[key]=(fingerprint,result);return result

class LifecycleState(str,Enum):RUNNING='running';DRAINING='draining';STOPPED='stopped'
@dataclass(frozen=True)
class DrainReport:
 completed:int;cancelled:int;remaining:int;elapsed_ms:float
class GracefulShutdown:
 def __init__(self):self.state=LifecycleState.RUNNING;self._tasks=set()
 def track(self,task):
  if self.state is not LifecycleState.RUNNING:raise RuntimeError('service is not accepting work')
  self._tasks.add(task);task.add_done_callback(self._tasks.discard);return task
 def create_task(self,awaitable):return self.track(asyncio.create_task(awaitable))
 async def drain(self,timeout=30.0):
  self.state=LifecycleState.DRAINING;started=time.monotonic();initial=len(self._tasks)
  if self._tasks:
   done,pending=await asyncio.wait(tuple(self._tasks),timeout=max(0,timeout))
  else:done,pending=set(),set()
  for task in pending:task.cancel()
  if pending:await asyncio.gather(*pending,return_exceptions=True)
  self.state=LifecycleState.STOPPED
  return DrainReport(len(done),len(pending),0,(time.monotonic()-started)*1000)

@dataclass(frozen=True)
class ResilienceGateBudget:
 max_cancel_seconds:float=1.0;max_drain_seconds:float=30.0;require_retry_safety:bool=True
class ResilienceGate:
 def evaluate(self,*,cancel_seconds,drain_seconds,retry_safety_passed,orphan_tasks=0):
  checks={'cancellation':cancel_seconds<=1.0,'drain':drain_seconds<=30.0,'retry_safety':bool(retry_safety_passed),'no_orphans':orphan_tasks==0}
  return {'gate':'PASS' if all(checks.values()) else 'FAIL','checks':checks}


