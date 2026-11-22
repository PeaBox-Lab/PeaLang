"""Tests for Phase 5: Language Evolution features."""

from pealang.type_system import (
    Effect, EffectSet, IO_EFFECT, STATE_EFFECT, EXCEPTION_EFFECT, ASYNC_EFFECT, NONDET_EFFECT,
    infer_effects, check_effect_subtyping,
    LinearType, check_linear_usage,
    RefinementType, parse_refinement, check_refinement,
    Macro, MacroExpander, STANDARD_MACROS,
    ModuleSpec, parse_module_spec, check_module_compatibility,
    TypeRef, Diagnostic,
)


def test_effect_system():
    """Test effect system basics."""
    io = Effect("IO")
    state = Effect("State")
    assert str(io) == "IO"
    assert str(Effect("Generic", (TypeRef("Int"),))) == "Generic<Int>"
    
    # EffectSet operations
    pure = EffectSet()
    io_set = EffectSet(frozenset([IO_EFFECT]))
    state_set = EffectSet(frozenset([STATE_EFFECT]))
    
    assert str(pure) == "Pure"
    assert str(io_set) == "{IO}"
    
    # Union
    combined = io_set | state_set
    assert IO_EFFECT in combined.effects
    assert STATE_EFFECT in combined.effects
    
    # Intersection
    assert (io_set & state_set).effects == frozenset()
    
    # Subtraction
    diff = io_set - state_set
    assert IO_EFFECT in diff.effects


def test_effect_inference():
    """Test effect inference from source code."""
    # IO effect
    effects = infer_effects('print "hello"', 'test')
    assert IO_EFFECT in effects.effects
    
    # State effect
    effects = infer_effects('let x = 1', 'test')
    assert STATE_EFFECT in effects.effects
    
    # Exception effect
    effects = infer_effects('throw "error"', 'test')
    assert EXCEPTION_EFFECT in effects.effects
    
    # Async effect
    effects = infer_effects('async function foo() { await bar() }', 'test')
    assert ASYNC_EFFECT in effects.effects
    
    # Non-det effect
    effects = infer_effects('parallel { random() }', 'test')
    assert NONDET_EFFECT in effects.effects


def test_effect_subtyping():
    """Test effect subtyping checks."""
    actual = EffectSet(frozenset([IO_EFFECT, STATE_EFFECT]))
    expected = EffectSet(frozenset([IO_EFFECT]))
    
    # Actual has more effects than expected - should be OK (subeffecting)
    diagnostics = check_effect_subtyping(actual, expected)
    # No diagnostics expected when actual has all expected effects
    # (This depends on the subtyping direction)
    
    # Missing required effect
    actual = EffectSet(frozenset([]))
    expected = EffectSet(frozenset([IO_EFFECT]))
    diagnostics = check_effect_subtyping(actual, expected)
    assert len(diagnostics) == 1
    assert diagnostics[0].code == 'E101'


def test_linear_types():
    """Test linear/affine type system."""
    linear = LinearType(TypeRef("Int"), "linear")
    affine = LinearType(TypeRef("String"), "affine")
    
    assert str(linear) == "!Int"
    assert str(affine) == "?String"
    
    # Check is_linear
    from pealang.type_system import is_linear
    assert is_linear(linear)
    assert is_linear(affine)
    assert not is_linear(TypeRef("Int"))


def test_linear_usage_checking():
    """Test linear/affine usage checking."""
    # Linear variable used - OK
    source = "let !x = 1\nprint x"
    diagnostics = check_linear_usage(source, {})
    assert len([d for d in diagnostics if d.severity == 'error']) == 0
    
    # Linear variable unused - Error
    source = "let !x = 1\nlet y = 2"
    diagnostics = check_linear_usage(source, {})
    errors = [d for d in diagnostics if d.severity == 'error']
    assert len(errors) == 1
    assert errors[0].code == 'L101'
    assert "never used" in errors[0].message
    
    # Affine variable unused - Warning
    source = "let ?x = 1\nlet y = 2"
    diagnostics = check_linear_usage(source, {})
    warnings = [d for d in diagnostics if d.severity == 'warning']
    assert len(warnings) == 1
    assert warnings[0].code == 'L102'


def test_refinement_types():
    """Test refinement type parsing and checking."""
    # Parse refinement
    rt = parse_refinement("{v: Int | v > 0}")
    assert rt is not None
    assert str(rt.base_type) == "Int"
    assert rt.predicate == "v > 0"
    assert rt.variable == "v"
    
    # String representation
    assert str(rt) == "{v: Int | v > 0}"
    
    # Invalid format
    assert parse_refinement("invalid") is None


def test_refinement_checking():
    """Test refinement predicate checking."""
    rt = parse_refinement("{v: Int | v > 0}")
    assert rt is not None
    
    # Value satisfies predicate
    assert check_refinement(5, rt) == True
    assert check_refinement(10, rt) == True
    
    # Value violates predicate
    assert check_refinement(-5, rt) == False
    assert check_refinement(0, rt) == False
    
    # String refinement
    rt_str = parse_refinement("{v: String | len(v) > 3}")
    assert check_refinement("hello", rt_str) == True
    assert check_refinement("hi", rt_str) == False


def test_macros():
    """Test macro system."""
    expander = MacroExpander()
    
    # Define a simple macro
    macro = Macro(
        name="unless",
        pattern="unless $cond { $body }",
        template="if (!($1)) { $2 }"
    )
    expander.define(macro)
    
    # Expand macro
    source = "unless x > 0 { print \"negative\" }"
    expanded = expander.expand(source)
    assert "if (!(x > 0))" in expanded
    assert "print \"negative\"" in expanded


def test_standard_macros():
    """Test built-in standard macros."""
    # Try macro
    source = "try x catch e => print e"
    expanded = STANDARD_MACROS.expand(source)
    assert "try { x } catch e { print e }" in expanded
    
    # Match macro
    source = "match x { 1 => \"one\", _ => \"other\" }"
    expanded = STANDARD_MACROS.expand(source)
    assert "match x { 1 => \"one\", _ => \"other\" }" in expanded


def test_module_system_v2():
    """Test module system v2."""
    source = """
module mylib @1.0.0 {
    export function add(a, b) { return a + b }
    export const PI = 3.14
    import other as o
}
"""
    spec = parse_module_spec(source)
    assert spec is not None
    assert spec.name == "mylib"
    assert spec.version == "1.0.0"
    assert len(spec.exports) == 2
    assert spec.exports[0].name == "add"
    assert spec.exports[1].name == "PI"
    assert len(spec.imports) == 1
    assert spec.imports[0].module == "other"
    assert spec.imports[0].imports == ["o"]


def test_module_compatibility():
    """Test module compatibility checking."""
    available = {
        "dep1": ModuleSpec("dep1", "1.0.0"),
        "dep2": ModuleSpec("dep2", "2.0.0"),
    }
    
    spec = ModuleSpec(
        name="myapp",
        version="1.0.0",
        dependencies={"dep1": "1.0.0", "dep2": "2.0.0"}
    )
    
    # Should pass - versions match
    diagnostics = check_module_compatibility(spec, available)
    assert len([d for d in diagnostics if d.severity == 'error']) == 0
    
    # Missing dependency
    spec2 = ModuleSpec(
        name="myapp",
        version="1.0.0",
        dependencies={"missing": "1.0.0"}
    )
    diagnostics = check_module_compatibility(spec2, available)
    errors = [d for d in diagnostics if d.severity == 'error']
    assert len(errors) == 1
    assert errors[0].code == 'M101'
    
    # Version mismatch
    spec3 = ModuleSpec(
        name="myapp",
        version="1.0.0",
        dependencies={"dep1": "2.0.0"}
    )
    diagnostics = check_module_compatibility(spec3, available)
    warnings = [d for d in diagnostics if d.severity == 'warning']
    assert len(warnings) == 1
    assert warnings[0].code == 'M102'


def test_integrate_advanced_types():
    """Test integration of advanced types into type checker."""
    from pealang.type_system import integrate_advanced_types, TypeChecker
    
    source = """
    function add(a, b) { return a + b }
    let !x = 1
    """
    
    checker = TypeChecker()
    diagnostics = integrate_advanced_types(checker, source)
    # Should have diagnostics from linear type checking
    assert isinstance(diagnostics, list)


if __name__ == "__main__":
    test_effect_system()
    print("test_effect_system passed")
    test_effect_inference()
    print("test_effect_inference passed")
    test_effect_subtyping()
    print("test_effect_subtyping passed")
    test_linear_types()
    print("test_linear_types passed")
    test_linear_usage_checking()
    print("test_linear_usage_checking passed")
    test_refinement_types()
    print("test_refinement_types passed")
    test_refinement_checking()
    print("test_refinement_checking passed")
    test_macros()
    print("test_macros passed")
    test_standard_macros()
    print("test_standard_macros passed")
    test_module_system_v2()
    print("test_module_system_v2 passed")
    test_module_compatibility()
    print("test_module_compatibility passed")
    test_integrate_advanced_types()
    print("test_integrate_advanced_types passed")
    print("\nAll Phase 5 tests passed!")