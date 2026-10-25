

import asyncio,pytest
from pealang.concurrency_resilience import *
def test_parent_cancellation_propagates():
 async def case():
  parent=CancellationToken();child=parent.child();parent.cancel(CancellationReason.SHUTDOWN);assert child.cancelled
  with pytest.raises(asyncio.CancelledError):child.raise_if_cancelled()
 asyncio.run(case())
def test_deadline_cancels_token():
 async def case():
  token=CancellationToken()
  with pytest.raises(asyncio.TimeoutError):await run_with_deadline(asyncio.sleep(.05),Deadline.after(.001),token)
  assert token.cancelled and token.reason is CancellationReason.TIMEOUT
 asyncio.run(case())
def test_structured_group_fail_fast():
 async def fail():raise ValueError('bad')
 async def slow():await asyncio.sleep(1)
 async def case():
  group=StructuredTaskGroup();group.create_task('fail',fail());group.create_task('slow',slow());out=await group.wait();assert {x.status for x in out}=={'failed','cancelled'} and group.token.cancelled
 asyncio.run(case())
def test_retry_requires_safety_and_succeeds():
 async def case():
  with pytest.raises(RetrySafetyError):await retry_async(lambda:asyncio.sleep(0),RetryPolicyV2(max_attempts=2))
  calls=[]
  async def op():
   calls.append(1)
   if len(calls)<3:raise TimeoutError()
   return 42
  assert await retry_async(op,RetryPolicyV2(3,0,0,1,0),idempotent=True)==42
 asyncio.run(case())
def test_idempotency_payload_guard():
 async def case():
  store=IdempotencyStore();calls=[]
  async def op():calls.append(1);return 'ok'
  assert await store.execute('k',{'a':1},op)=='ok' and await store.execute('k',{'a':1},op)=='ok' and len(calls)==1
  with pytest.raises(RetrySafetyError):await store.execute('k',{'a':2},op)
 asyncio.run(case())
def test_graceful_drain_and_gate():
 async def case():
  shutdown=GracefulShutdown();shutdown.create_task(asyncio.sleep(.001));report=await shutdown.drain(.1);assert report.completed==1 and shutdown.state is LifecycleState.STOPPED
  with pytest.raises(RuntimeError):shutdown.create_task(asyncio.sleep(0))
  assert ResilienceGate().evaluate(cancel_seconds=.1,drain_seconds=.2,retry_safety_passed=True)['gate']=='PASS'
 asyncio.run(case())


