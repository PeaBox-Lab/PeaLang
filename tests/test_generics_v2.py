"""Phase 62: static generics v2 contracts, inference, bounds, and compatibility."""

from pealang import (
    SemanticAnalyzer, TypeChecker, analyze_project, compatible_generic, execute,
    parse_generic_functions, parse_type,
)


def codes(source):
    return [d.code for d in SemanticAnalyzer().analyze(source).diagnostics]


def test_generic_bounds_parse_without_changing_type_parameter_names():
    g = parse_generic_functions('function show<T: Printable>(value: T) -> String { return "ok" }')['show']
    assert g.type_params == ('T',)
    assert g.bounds['T'] == ('Printable',)


def test_type_parameters_are_in_scope_but_unknown_types_still_fail():
    assert TypeChecker().check('function id<T>(x: T) -> T { return x }').ok
    diagnostics = TypeChecker().check('function id<T>(x: Missing) -> T { return x }').diagnostics
    assert any(d.code == 'T101' and 'Missing' in d.message for d in diagnostics)


def test_semantic_analyzer_preserves_generic_contracts():
    r = SemanticAnalyzer().analyze('function id<T>(x: T) -> T { return x }')
    assert r.generics['id'].type_params == ('T',)
    assert r.functions['id'].params[0][1].name == 'T'


def test_generic_call_infers_from_variables():
    source = 'function id<T>(x: T) -> T {\n return x\n}\nlet n: Int = 1\nprint id(n)'
    assert SemanticAnalyzer().analyze(source).ok


def test_conflicting_generic_inference_is_diagnosed():
    source = 'function pair<T>(a: T, b: T) -> T { return a }\nprint pair(1, "x")'
    assert 'G202' in codes(source)


def test_protocol_bound_violation_is_diagnosed():
    source = '''protocol Printable { function to_string() -> String }
type Broken = {other: Int}
function show<T: Printable>(value: T) -> String { return "ok" }
let b: Broken = {"other": 1}
print show(b)
'''
    assert 'G203' in codes(source)


def test_generic_compatibility_checks_arguments_recursively():
    assert compatible_generic(parse_type('List<Int>'), parse_type('List<String>')) is False
    assert compatible_generic(parse_type('List<T>'), parse_type('List<Int>'), {'T'}) is True
    assert compatible_generic(parse_type('Int?'), parse_type('Int')) is True
    assert compatible_generic(parse_type('Int'), parse_type('Int?')) is False


def test_project_analysis_exposes_generic_contracts(tmp_path):
    source = tmp_path / 'g.pea'
    source.write_text('function id<T>(x: T) -> T { return x }', encoding='utf-8')
    assert 'g.id' in analyze_project([source])['generics']


def test_generic_runtime_erasure_still_executes():
    out = []
    execute('function id<T>(x: T) -> T { return x }\nprint id(3)', output=out.append)
    assert out == ['3']
