"""Phase 64: explicit iterators, VM parity, and iterable static contracts."""

import pytest

from pealang import (
    CompileError,
    Interpreter,
    PeaIterator,
    SemanticAnalyzer,
    TypeChecker,
    TypeRef,
    VirtualMachine,
    VMError,
    close_iterator,
    compile_source,
    compile_source_to_bytecode,
    execute,
    has_next,
    iterable_element_type,
    iterator_next,
    make_iterator,
    peek,
    to_pea,
)
from pealang.help import help as pea_help


def vm_output(source, globals=None):
    out = []
    VirtualMachine(out.append).run(compile_source_to_bytecode(source), globals)
    return out


def test_iterator_api_lookahead_default_and_close():
    it = make_iterator([1, 2])
    assert isinstance(it, PeaIterator)
    assert has_next(it) is True
    assert peek(it) == 1
    assert iterator_next(it) == 1
    assert iterator_next(it, 'done') == 2
    assert iterator_next(it, 'done') == 'done'
    close_iterator(it)
    assert has_next(it) is False


def test_exhaustion_without_default_is_typed_value_error():
    it = make_iterator([])
    with pytest.raises(ValueError, match='Iterator exhausted'):
        iterator_next(it)


def test_interpreter_iterator_builtins_and_preserved_lookahead():
    out = []
    execute(
        'let it = iter([1,2])\n'
        'print next(it)\n'
        'print has_next(it)\n'
        'for x in it { print x }',
        output=out.append,
    )
    assert out == ['1', 'true', '2']


def test_vm_iterator_builtins_match_interpreter_sequence():
    source = 'let it = iter([1,2])\nprint next(it)\nprint has_next(it)\nfor x in it { print x }'
    assert vm_output(source) == [1, True, 2]


def test_peek_builtin_is_non_consuming_in_both_runtimes():
    source = 'let it = iter([7,8])\nprint peek(it)\nprint next(it)\nprint peek(it)'
    out = []
    execute(source, output=out.append)
    assert out == ['7', '7', '8']
    assert vm_output(source) == [7, 7, 8]


def test_vm_exception_unwind_closes_active_iterators():
    vm = VirtualMachine(lambda value: None)
    with pytest.raises(VMError):
        vm.run(compile_source_to_bytecode('for x in [1,2] { throw "boom" }'))
    assert vm.stack == []


def test_simple_for_parity_between_interpreter_and_vm():
    source = 'for x in [1,2,3] { print x }'
    out = []
    execute(source, output=out.append)
    assert out == ['1', '2', '3']
    assert [str(value) for value in vm_output(source)] == out


def test_host_iterator_object_works_in_both_runtimes():
    class Counter:
        def __init__(self):
            self.n = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self.n >= 2:
                raise StopIteration
            self.n += 1
            return self.n

    source = 'for x in host { print x }'
    out = []
    interp = Interpreter(output=out.append)
    interp.global_env.define('host', Counter(), True)
    interp.run(compile_source(source))
    assert out == ['1', '2']
    assert [str(value) for value in vm_output(source, {'host': Counter()})] == out


def test_break_leaves_no_vm_stack_value():
    vm = VirtualMachine(lambda value: None)
    vm.run(compile_source_to_bytecode('for x in [1,2] { print x\nbreak }'))
    assert vm.stack == []


def test_destructuring_for_is_a_clear_compile_error():
    with pytest.raises(CompileError, match='Destructuring for'):
        compile_source_to_bytecode('for [a,b] in [[1,2]] { print a }')


def test_iterable_element_type_helper():
    assert iterable_element_type(TypeRef('List', (TypeRef('Int'),))) == TypeRef('Int')
    assert iterable_element_type(TypeRef('Map', (TypeRef('String'), TypeRef('Int')))) == TypeRef('String')
    assert iterable_element_type(TypeRef('Int')) is None


def test_iterable_static_annotations_and_iteration_diagnostic():
    assert TypeChecker().check(
        'let xs: Iterable<Int> = [1,2]\nlet it: Iterator<Int> = iter(xs)'
    ).ok
    diagnostics = SemanticAnalyzer().analyze('let x: Int = 1\nfor v in x { print v }').diagnostics
    assert any(d.code == 'I201' for d in diagnostics)


def test_embedding_accepts_pea_iterators():
    it = make_iterator([1, 2])
    assert to_pea(it) is it


def test_help_exposes_iterators_topic():
    assert 'iter' in pea_help('iterators')
