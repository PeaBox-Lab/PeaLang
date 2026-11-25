"""Phase 63: structural protocols, marker traits, and signature-aware conformance."""

from pealang import (
    SemanticAnalyzer,
    TypeChecker,
    analyze_project,
    check_record_protocol_conformance,
    execute,
    function_field_type,
    parse_protocols,
    parse_traits,
    parse_type,
    protocol_conforms,
)
from pealang.extension_registry import ExtensionRegistry
from pealang.extension_type_system import ExtensionTypeSystem


def protocol_codes(protocol, fields):
    return [d.code for d in check_record_protocol_conformance('Item', fields, protocol)]


def test_protocol_equals_syntax_and_nested_function_fields_parse():
    protocols = parse_protocols('protocol Printer = { function render(value: List<Int>) -> String }')
    protocol = protocols['Printer']
    assert protocol.methods[0][1][0][1] == parse_type('List<Int>')
    assert protocol.methods[0][2] == parse_type('String')


def test_marker_traits_are_real_static_contracts():
    traits = parse_traits('trait Printable\ntrait Named = {}')
    assert set(traits) == {'Printable', 'Named'}
    assert traits['Printable'].methods == ()
    assert protocol_conforms({}, traits['Printable'])


def test_structural_signature_diagnostics():
    protocol = parse_protocols('protocol Printer { function render(value: Int) -> String }')['Printer']
    assert protocol_codes(protocol, {}) == ['P201']
    assert protocol_codes(protocol, {'render': parse_type('Int')}) == ['P202']
    assert protocol_codes(protocol, {'render': parse_type('Function<Int>')}) == ['P203']
    assert protocol_codes(protocol, {'render': parse_type('Function<String, String>')}) == ['P204']
    assert protocol_codes(protocol, {'render': parse_type('Function<Int, Int>')}) == ['P205']
    assert protocol_codes(protocol, {
        'render': function_field_type((('value', parse_type('Int')),), parse_type('String'))
    }) == []


def test_bare_function_field_remains_legacy_wildcard():
    protocol = parse_protocols('protocol Printable { function to_string() -> String }')['Printable']
    assert protocol_conforms({'to_string': parse_type('Function')}, protocol)


def test_unrelated_record_is_not_scanned_against_protocol():
    source = 'protocol Printable { function to_string() -> String }\ntype User = {name: String}'
    result = SemanticAnalyzer().analyze(source)
    assert result.ok
    assert not [d for d in result.diagnostics if d.code.startswith('P2')]


def test_protocol_bound_uses_structural_signature():
    source = '''protocol Printable { function to_string() -> String }
type Good = {to_string: Function<String>}
function show<T: Printable>(value: T) -> String {
 return "ok"
}
let g: Good
print show(g)
'''
    result = SemanticAnalyzer().analyze(source)
    assert result.ok
    assert result.protocols['Printable'].methods[0][0] == 'to_string'


def test_multiple_protocol_bounds_are_checked():
    source = '''protocol A { function a() -> String }
protocol B { function b() -> String }
type Both = {a: Function<String>, b: Function<String>}
function check<T: A + B>(value: T) -> String {
 return "ok"
}
let x: Both
print check(x)
'''
    assert SemanticAnalyzer().analyze(source).ok


def test_project_analysis_exposes_protocols_and_traits(tmp_path):
    source = tmp_path / 'contracts.pea'
    source.write_text(
        'protocol Printable { function to_string() -> String }\n'
        'trait Serializable\n'
        'function show<T: Printable>(value: T) -> String {\n return "ok"\n}\n',
        encoding='utf-8',
    )
    result = analyze_project([source])
    assert 'contracts.Printable' in result['protocols']
    assert 'contracts.Serializable' in result['traits']


def test_extension_protocol_hook_uses_name_only_contract():
    registry = ExtensionRegistry()
    registry.register_type('Counter', lambda: 0, {'increment': lambda self: None})
    protocol = ExtensionTypeSystem(registry).get_extension_protocol('Counter')
    assert protocol is not None
    assert protocol.name == 'Counter'
    assert [method[0] for method in protocol.methods] == ['increment']
    assert protocol.method_names_only is True


def test_trait_declarations_are_erased_before_runtime():
    out = []
    execute('trait Marker\nfunction id(x: Int) -> Int { return x }\nprint id(3)', output=out.append)
    assert out == ['3']


def test_type_checker_parses_nested_function_record_fields():
    result = TypeChecker().check('type Handler = {call: Function<Int, String>}')
    assert result.ok
    assert result.records['Handler']['call'].args == (parse_type('Int'), parse_type('String'))
