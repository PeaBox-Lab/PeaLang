"""Phase 67: bounded, hygiene-aware macro expansion."""

import pytest

from pealang import (
    MacroExpansionError,
    SafeMacro,
    SafeMacroExpander,
    STANDARD_SAFE_MACROS,
    VirtualMachine,
    compile_source_with_macros,
    expand_source_macros,
    validate_macro,
)
from pealang.help import help as pea_help


def test_standard_safe_macros_expand_without_changing_pipeline():
    result = STANDARD_SAFE_MACROS.expand('try x catch e => print e')
    assert result.ok
    assert 'try { x } catch e { print e }' in result.source
    assert 'try_expr' in result.applied
    assert expand_source_macros('try x catch e => print e') == 'try { x } catch e { print e }'


def test_hygiene_marker_avoids_capture():
    expander = SafeMacroExpander()
    expander.define(SafeMacro(
        name='safe_add',
        pattern='safe_add $left $right',
        template='let @tmp = $left\n@tmp + $right',
    ))
    result = expander.expand('safe_add tmp 2')
    assert result.ok
    assert 'let __tmp_1 = tmp' in result.source
    assert '__tmp_1 + 2' in result.source
    assert 'let tmp = tmp' not in result.source


def test_macro_definitions_are_validated():
    unknown = validate_macro(SafeMacro('unknown', 'use $x', 'use $y'))
    assert any(issue.code == 'MG102' for issue in unknown)
    unbalanced = validate_macro(SafeMacro('unbalanced', 'unless $x { $body', 'if ($x) { $body }'))
    assert any(issue.code == 'MG101' for issue in unbalanced)
    bad_name = validate_macro(SafeMacro('not-valid', 'call $x', '$x'))
    assert any(issue.code == 'MG001' for issue in bad_name)


def test_non_convergent_expansion_is_bounded():
    expander = SafeMacroExpander()
    expander.define(SafeMacro('loop', 'loop $value', 'loop $value more'))
    result = expander.expand('loop x')
    assert not result.ok
    assert any(issue.code == 'MG203' for issue in result.issues)


def test_strict_expansion_raises_on_invalid_definition():
    expander = SafeMacroExpander()
    expander.define(SafeMacro('bad', 'show $x', 'show $missing'))
    with pytest.raises(MacroExpansionError, match='MG102'):
        expand_source_macros('show 1', expander)


def test_compile_source_with_macros_runs_in_vm():
    expander = SafeMacroExpander()
    expander.define(SafeMacro(
        name='twice',
        pattern='print double $value',
        template='print $value + $value',
    ))
    source = 'print double 3'
    out = []
    VirtualMachine(out.append).run(compile_source_with_macros(source, '<macro>', expander))
    assert out == [6]


def test_help_describes_safe_metaprogramming():
    text = pea_help('macros')
    assert '$name' in text
    assert '@name' in text
    assert 'MG101-MG203' in text
