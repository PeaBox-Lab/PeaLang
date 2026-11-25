"""Phase 66: shared module resolution, caching, and static module graphs."""

import asyncio
import json

import pytest

from pealang import (
    AsyncVMRuntime,
    Interpreter,
    ModuleResolver,
    VirtualMachine,
    analyze_project,
    compile_source_to_bytecode,
    module_candidates,
)
from pealang.help import help as pea_help
from pealang.parser import parse_source
from pealang.vm import VMError


def write_project(tmp_path, dependencies=None):
    (tmp_path / 'pea.json').write_text(json.dumps({
        'project': {'name': 'demo', 'version': '1.0.0', 'entry': 'main.pea'},
        'dependencies': dependencies or {},
    }), encoding='utf-8')
    package = tmp_path / 'modules' / 'api'
    package.mkdir(parents=True)
    (package / 'client.pea').write_text('let value = 7\nexport value', encoding='utf-8')
    main = tmp_path / 'main.pea'
    main.write_text('import "api.client" as client\nprint client.value', encoding='utf-8')
    return main


def test_module_candidates_include_dotted_paths():
    assert module_candidates('api.client') == [
        'api.client', 'api/client', 'api/client/__init__.pea'
    ]
    assert module_candidates('./local.pea') == ['./local.pea']


def test_vm_resolves_dotted_project_modules(tmp_path):
    main = write_project(tmp_path)
    out = []
    vm = VirtualMachine(out.append, module_resolver=ModuleResolver(tmp_path))
    vm.run(compile_source_to_bytecode(main.read_text(encoding='utf-8'), str(main)))
    assert out == [7]
    assert len(vm.module_cache) == 1


def test_vm_infers_project_resolver_from_source_path(tmp_path):
    main = write_project(tmp_path)
    out = []
    VirtualMachine(out.append).run(
        compile_source_to_bytecode(main.read_text(encoding='utf-8'), str(main))
    )
    assert out == [7]


def test_interpreter_import_cache_and_async_vm_parity(tmp_path):
    write_project(tmp_path)
    source = (
        'import "api.client" as a\n'
        'import "api.client" as b\n'
        'print a.value + b.value'
    )
    out = []
    interpreter = Interpreter(out.append, base_dir=tmp_path, project_root=tmp_path)
    interpreter.run(parse_source(source, str(tmp_path / 'main.pea')))
    assert out == ['14']
    assert len(interpreter.module_resolver.cache) == 1

    async def case():
        runtime = AsyncVMRuntime(project_root=tmp_path)
        module = await runtime.load_async(
            'import "api.client" as client\n'
            'async function read() { return client.value }\n'
            'export read',
            str(tmp_path / 'async.pea'),
        )
        assert await module.call_async('read') == 7

    asyncio.run(case())


def test_vm_rejects_circular_imports(tmp_path):
    (tmp_path / 'pea.json').write_text(json.dumps({
        'project': {'name': 'demo', 'version': '1.0.0', 'entry': 'main.pea'},
        'dependencies': {},
    }), encoding='utf-8')
    modules = tmp_path / 'modules'
    modules.mkdir()
    (modules / 'a.pea').write_text('import "b" as b\nexport value', encoding='utf-8')
    (modules / 'b.pea').write_text('import "a" as a\nexport value', encoding='utf-8')
    source = 'import "a" as a\nprint a.value'
    vm = VirtualMachine(lambda _: None, module_resolver=ModuleResolver(tmp_path))
    with pytest.raises(VMError, match='Circular module import'):
        vm.run(compile_source_to_bytecode(source, str(tmp_path / 'main.pea')))


def test_static_module_graph_reports_unresolved_and_cycles(tmp_path):
    missing = tmp_path / 'missing.pea'
    missing.write_text('import "nowhere.pea" as nowhere\nexport value', encoding='utf-8')
    a = tmp_path / 'a.pea'
    b = tmp_path / 'b.pea'
    a.write_text('import "b.pea" as b\nexport value', encoding='utf-8')
    b.write_text('import "a.pea" as a\nexport value', encoding='utf-8')
    result = analyze_project([missing, a, b])
    codes = [d.code for _, d in result['diagnostics']]
    assert 'M201' in codes
    assert 'M203' in codes
    assert result['modules']['cycles']


def test_help_describes_module_graph():
    text = pea_help('modules')
    assert 'project/dependency module' in text
    assert 'M203' in text
