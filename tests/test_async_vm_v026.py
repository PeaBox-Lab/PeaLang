import asyncio,pytest
from pealang import AsyncVMRuntime,RuntimeOptions
async def double(x):await asyncio.sleep(.001);return x*2
def run(coro):return asyncio.run(coro)
def test_await_host():
 async def case():
  r=AsyncVMRuntime().register_async_function('api.double',double);m=await r.load_async('async function work(x){return await api.double(x)}\nexport work');assert await m.call_async('work',4)==8
 run(case())
def test_permission():
 async def case():
  r=AsyncVMRuntime().register_async_function('api.double',double,'api.use');m=await r.load_async('async function work(x){return await api.double(x)}\nexport work')
  with pytest.raises(Exception):await m.call_async('work',4)
 run(case())
def test_permission_allowed():
 async def case():
  r=AsyncVMRuntime(RuntimeOptions(permissions=frozenset({'api.use'}))).register_async_function('api.double',double,'api.use');m=await r.load_async('async function work(x){return await api.double(x)}\nexport work');assert await m.call_async('work',3)==6
 run(case())
def test_timeout():
 async def case():
  async def slow():await asyncio.sleep(.1);return 1
  r=AsyncVMRuntime(RuntimeOptions(max_execution_ms=5)).register_async_function('api.slow',slow);m=await r.load_async('async function work(){return await api.slow()}\nexport work')
  with pytest.raises(asyncio.TimeoutError):await m.call_async('work')
 run(case())
def test_async_syntax_compiles():
 from pealang import compile_source_to_bytecode,disassemble
 assert 'AWAIT' in disassemble(compile_source_to_bytecode('async function f(){return await api.get()}'))

