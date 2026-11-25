"""Phase 68: deterministic resource scopes and `using` bindings."""

import pytest

from pealang import (
    Interpreter,
    ResourceScope,
    ResourceScopeError,
    ResourceScopeManager,
    VirtualMachine,
    check_resource_scopes,
    compile_source_to_bytecode,
    derive_limits,
    dispose,
    scope_summary,
)
from pealang.help import help as pea_help
from pealang.parser import parse_source
from pealang.resource_limits import ResourceLimits
from pealang.type_system import analyze_project


class Resource:
    def __init__(self, name, log):
        self.name = name
        self.log = log

    def close(self):
        self.log.append('close ' + self.name)


class Disposable:
    def __init__(self, log):
        self.log = log

    def dispose(self):
        self.log.append('dispose')


def test_scope_manager_nests_and_cleans_up_in_lifo_order():
    manager = ResourceScopeManager()
    log = []
    with manager.enter('outer') as outer:
        outer.defer(lambda: log.append('outer-cleanup'), 'outer-cleanup')
        assert manager.current() is outer
        with manager.enter('inner') as inner:
            inner.register(Resource('r', log))
            assert manager.current() is inner
    assert log == ['close r', 'outer-cleanup']
    assert manager.snapshot()['active'] == []
    assert manager.snapshot()['history'] == ['inner', 'outer']


def test_child_scopes_derive_bounded_limits_and_reject_closed_use():
    parent = ResourceScope('parent', limits=ResourceLimits(max_instructions=50))
    child = parent.child('child', limits=ResourceLimits(max_instructions=10))
    assert child.budget.limits.max_instructions == 10
    assert child.budget.limits.max_output_bytes == parent.budget.limits.max_output_bytes
    derived = derive_limits(parent.budget.limits, max_instructions=7)
    assert derived.max_instructions == 7
    child.close()
    with pytest.raises(ResourceScopeError) as exc:
        child.defer(lambda: None)
    assert exc.value.code == 'RS201'
    assert 'RS201' in str(exc.value)


def test_dispose_helper_supports_close_and_dispose_without_methods():
    log = []
    assert dispose(Resource('r', log)) is True
    assert dispose(Disposable(log)) is True
    assert dispose(42) is False
    assert log == ['close r', 'dispose']


def test_interpreter_using_cleans_up_on_normal_exit():
    log = []
    out = []
    interp = Interpreter(out.append)
    interp.global_env.define('res', Resource('a', log), True)
    interp.run(parse_source('using r = res {\n print "inside"\n}\nprint "done"'))
    assert out == ['inside', 'done']
    assert log == ['close a']
    assert interp.scope_manager.current() is None


def test_vm_using_cleans_up_on_normal_exit():
    log = []
    out = []
    vm = VirtualMachine(out.append)
    vm.run(compile_source_to_bytecode('using r = res {\n print "inside"\n}\nprint "done"'),
           {'res': Resource('b', log)})
    assert out == ['inside', 'done']
    assert log == ['close b']
    assert vm.scope_manager.snapshot()['history'] == ['r']


def test_both_runtimes_clean_up_on_exceptions():
    src = 'using r = res {\n throw error("UserError", "boom")\n}'
    interp_log = []
    interp = Interpreter(print)
    interp.global_env.define('res', Resource('interp', interp_log), True)
    with pytest.raises(Exception):
        interp.run(parse_source(src))
    assert interp_log == ['close interp']
    assert interp.scope_manager.current() is None

    vm_log = []
    vm = VirtualMachine(print)
    with pytest.raises(Exception):
        vm.run(compile_source_to_bytecode(src), {'res': Resource('vm', vm_log)})
    assert vm_log == ['close vm']
    assert vm.scope_manager.current() is None


def test_nested_using_scopes_close_in_reverse_order():
    log = []
    src = ('using a = outer {\n using b = inner {\n print "nested"\n }\n print "outer"\n}')
    interp = Interpreter(lambda _: None)
    interp.global_env.define('outer', Resource('outer', log), True)
    interp.global_env.define('inner', Resource('inner', log), True)
    interp.run(parse_source(src))
    assert log == ['close inner', 'close outer']

    log.clear()
    vm = VirtualMachine(lambda _: None)
    vm.run(compile_source_to_bytecode(src),
           {'outer': Resource('outer', log), 'inner': Resource('inner', log)})
    assert log == ['close inner', 'close outer']


def test_scopes_namespace_reports_active_scope():
    src = 'using r = res {\n print scopes.current()["name"]\n}'
    interp_out = []
    interp = Interpreter(interp_out.append)
    interp.global_env.define('res', Resource('x', []), True)
    interp.run(parse_source(src))
    assert 'r' in interp_out[0]

    vm_out = []
    vm = VirtualMachine(vm_out.append)
    # The VM lacks generic indexing of dict constants in all paths; use snapshot instead.
    vm.run(compile_source_to_bytecode('using r = res {\n print scopes.snapshot()["active"][0]\n}'),
           {'res': Resource('y', [])})
    assert 'r' in str(vm_out[0])


def test_static_scope_diagnostics_and_project_integration(tmp_path):
    result = check_resource_scopes('using r = x {\n using s = y {}\n}\nusing r = z {\n r = 3\n}')
    codes = [issue.code for issue in result['diagnostics']]
    assert 'R201' in codes
    assert 'R202' in codes
    assert [item['name'] for item in result['bindings']] == ['r', 's', 'r']

    path = tmp_path / 'scopes.pea'
    path.write_text('using r = x {\n r = 3\n}\n', encoding='utf-8')
    analysis = analyze_project([str(path)])
    assert str(path) in analysis['scopes']
    assert any(code == 'R202' for _, diag in analysis['diagnostics'] for code in [diag.code])


def test_async_vm_using_releases_resources():
    import asyncio
    from pealang import AsyncVMRuntime

    log = []

    async def case():
        runtime = AsyncVMRuntime(output=lambda _: None)
        runtime.register_async_function('res.make', lambda: Resource('async', log))
        await runtime.load_async('using r = res.make() {\n print "inside"\n}')
        assert log == ['close async']

    asyncio.run(case())


def test_help_describes_resource_scopes():
    text = pea_help('scopes')
    assert 'using name = resource' in text
    assert 'R201' in text
    assert 'R202' in text
    assert 'scope_summary' in scope_summary(ResourceScope('s')).keys() or 'name' in scope_summary(ResourceScope('s'))
