"""Phase 65: structured async concurrency in the bytecode VM and static layer."""

import asyncio

import pytest

from pealang import (
    AsyncVMRuntime,
    RuntimeOptions,
    SemanticAnalyzer,
    TypeChecker,
    TypeRef,
    compile_source_to_bytecode,
    erase_types,
    future_element_type,
    spawn_task,
)
from pealang.async_vm import CancellationToken
from pealang.help import help as pea_help


async def double(value):
    await asyncio.sleep(0.001)
    return value * 2


async def slow():
    await asyncio.sleep(0.05)
    return 1


async def pending():
    await asyncio.Event().wait()


def run(coro):
    return asyncio.run(coro)


def test_async_vm_gather_and_spawn_helpers():
    async def case():
        runtime = AsyncVMRuntime().register_async_function('api.double', double)
        source = (
            'async function gather_work(x) { return await concurrency.gather([api.double(x), api.double(x + 1)]) }\n'
            'async function spawn_work(x) { let t = concurrency.spawn(api.double(x)); return await concurrency.result(t) }\n'
            'export gather_work\nexport spawn_work'
        )
        module = await runtime.load_async(source)
        assert await module.call_async('gather_work', 3) == [6, 8]
        assert await module.call_async('spawn_work', 7) == 14

    run(case())


def test_async_vm_timeout_helper():
    async def case():
        runtime = (AsyncVMRuntime(RuntimeOptions(max_execution_ms=500))
              .register_async_function('api.pending', pending))
        module = await runtime.load_async(
            'async function work() { return await concurrency.timeout(0.05, api.pending()) }\nexport work'
        )
        with pytest.raises(asyncio.TimeoutError):
            await module.call_async('work')

    run(case())


def test_cancellation_token_propagates_to_a_structured_scope():
    async def case():
        token = CancellationToken()
        child = spawn_task(asyncio.sleep(0.01, result=1))
        await asyncio.sleep(0)
        token.cancel()
        assert token.cancelled
        assert token.scope.cancelled
        with pytest.raises(asyncio.CancelledError):
            token.scope.throw_if_cancelled()
        child.cancel()
        await asyncio.gather(child.task, return_exceptions=True)

    run(case())


def test_async_function_contracts_and_await_inference():
    source = 'async function load() -> Int { return 1 }\nlet x = await load()'
    analyzer = SemanticAnalyzer()
    result = analyzer.analyze(source)
    assert result.functions['load'].is_async
    assert analyzer.infer_expr('load()', {}, result) == TypeRef('Future', (TypeRef('Int'),))
    assert analyzer.infer_expr('await load()', {}, result) == TypeRef('Int')
    assert future_element_type(TypeRef('Future', (TypeRef('Int'),))) == TypeRef('Int')


def test_await_on_known_non_future_reports_a201():
    diagnostics = SemanticAnalyzer().analyze('let x: Int = 1\nlet y = await x').diagnostics
    assert any(d.code == 'A201' and 'not awaitable' in d.message for d in diagnostics)


def test_async_annotations_are_erased_before_compilation():
    source = 'async function f(x: Int) -> Int { return x }'
    assert TypeChecker().check(source).ok
    erased = erase_types(source)
    assert 'async function f(x)' in erased
    assert '->' not in erased
    compile_source_to_bytecode(source)


def test_help_exposes_async_concurrency_helpers():
    assert 'concurrency' in pea_help('async')
