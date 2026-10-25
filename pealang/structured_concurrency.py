
"""Structured concurrency primitives with cancellation propagation."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass
class CancellationScope:
 def __init__(self,parent=None):self.parent=parent;self.cancelled=False;self.children=[]
 def child(self):c=CancellationScope(self);self.children.append(c);return c
 def cancel(self):
  self.cancelled=True
  for child in list(self.children):child.cancel()
 def throw_if_cancelled(self):
  if self.cancelled or (self.parent and self.parent.cancelled):raise asyncio.CancelledError('PeaLang task cancelled')
@dataclass
class PeaTask:
 task:asyncio.Task
 scope:CancellationScope
 def cancel(self):self.scope.cancel();self.task.cancel()
 async def result(self):return await self.task
class TaskGroup:
 def __init__(self,scope=None):self.scope=scope or CancellationScope();self.tasks=[]
 async def __aenter__(self):return self
 async def __aexit__(self,typ,value,tb):
  if typ:
   self.scope.cancel()
   for item in self.tasks:item.cancel()
  results=await asyncio.gather(*(x.task for x in self.tasks),return_exceptions=True)
  if typ:return False
  for result in results:
   if isinstance(result,BaseException):
    self.scope.cancel();raise result
  return False
 def spawn(self,awaitable):
  child=self.scope.child()
  async def runner():child.throw_if_cancelled();return await awaitable
  item=PeaTask(asyncio.create_task(runner()),child);self.tasks.append(item);return item
async def gather_structured(*awaitables):
 async with TaskGroup() as group:tasks=[group.spawn(x) for x in awaitables]
 return [await x.result() for x in tasks]

