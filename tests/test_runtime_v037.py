
import asyncio,pytest
from pealang import ResourceLimits,ResourceBudget,ResourceLimitExceeded,estimated_size,CancellationScope,TaskGroup,gather_structured
from pealang.embedding import RuntimeOptions
def test_all_limits_declared():
 x=ResourceLimits();assert x.max_memory_bytes and x.max_stack_depth and x.max_collection_items and x.max_output_bytes and x.max_http_requests and x.max_file_read_bytes
def test_instruction_limit():
 b=ResourceBudget(ResourceLimits(max_instructions=2));b.instruction(2)
 with pytest.raises(ResourceLimitExceeded):b.instruction()
def test_memory_limit():
 b=ResourceBudget(ResourceLimits(max_memory_bytes=5))
 with pytest.raises(ResourceLimitExceeded):b.memory(6)
def test_collection_limit():
 b=ResourceBudget(ResourceLimits(max_collection_items=2))
 with pytest.raises(ResourceLimitExceeded):b.collection(3)
def test_output_limit_utf8():
 b=ResourceBudget(ResourceLimits(max_output_bytes=3))
 with pytest.raises(ResourceLimitExceeded):b.output('pea!')
def test_http_limit():
 b=ResourceBudget(ResourceLimits(max_http_requests=1));b.http_request()
 with pytest.raises(ResourceLimitExceeded):b.http_request()
def test_file_read_limit():
 b=ResourceBudget(ResourceLimits(max_file_read_bytes=2))
 with pytest.raises(ResourceLimitExceeded):b.file_read(3)
def test_stack_and_recursion():
 b=ResourceBudget(ResourceLimits(max_recursion_depth=1,max_stack_depth=1));b.set_recursion(1);b.set_stack(1)
 with pytest.raises(ResourceLimitExceeded):b.set_recursion(2)
def test_estimated_size_recursive_safe():
 x=[];x.append(x);assert estimated_size(x)>0
def test_runtime_options_retains_limits():assert RuntimeOptions().max_http_requests==32 and RuntimeOptions().max_file_read_bytes==8*1024*1024
def test_cancellation_propagates():
 p=CancellationScope();c=p.child();p.cancel();assert c.cancelled
 with pytest.raises(asyncio.CancelledError):c.throw_if_cancelled()
def test_structured_gather():
 async def f(x):await asyncio.sleep(0);return x*2
 assert asyncio.run(gather_structured(f(2),f(3)))==[4,6]
def test_taskgroup_result():
 async def run():
  async with TaskGroup() as g:t=g.spawn(asyncio.sleep(0,result=7))
  return await t.result()
 assert asyncio.run(run())==7
