"""Phase 61: structured error values shared by interpreter and VM."""

from pealang import (
    ERROR_VALUE_SCHEMA, VirtualMachine, build_error, compile_source_to_bytecode,
    error_value_from_exception, execute,
)


def run_interpreter(source):
    out = []
    execute(source, output=out.append, source_name="errors_v2.pea")
    return out


def run_vm(source):
    out = []
    vm = VirtualMachine(out.append)
    vm.run(compile_source_to_bytecode(source, "errors_v2.pea"))
    return out


def test_build_error_is_structured_and_stringifies_to_message():
    cause = build_error("ValueError", "bad value", "E_VALUE")
    err = build_error("TypeError", "bad type", "E_TYPE", cause)
    assert err["schema"] == ERROR_VALUE_SCHEMA
    assert err["kind"] == "TypeError"
    assert err["code"] == "E_TYPE"
    assert err["cause"]["code"] == "E_VALUE"
    assert str(err) == "bad type"


def test_exception_capture_exposes_code_and_cause():
    err = error_value_from_exception(PeaErrorWithCode())
    assert err["code"] == "E_HOST"
    assert err["cause"]["kind"] == "ValueError"


def PeaErrorWithCode():
    from pealang import PeaError
    return PeaError("host failure", code="E_HOST", cause=ValueError("root"))


def test_interpreter_typed_catch_reads_structured_fields():
    out = run_interpreter("""
try {
    throw error("TypeError", "bad type", "E_TYPE",
        error("ValueError", "bad value", "E_VALUE"))
} catch TypeError e {
    print e["schema"]
    print e["kind"]
    print e["code"]
    print e["cause"]["kind"]
    print e["cause"]["code"]
}
""")
    assert out == [ERROR_VALUE_SCHEMA, "TypeError", "E_TYPE", "ValueError", "E_VALUE"]


def test_vm_typed_catch_reads_structured_fields():
    out = run_vm(
        'try { throw error("TypeError", "bad type", "E_TYPE") } '
        'catch TypeError e { print e["kind"]; print e["code"] }'
    )
    assert out == ["TypeError", "E_TYPE"]


def test_vm_plain_throw_still_prints_message():
    out = run_vm('try { throw "boom" } catch e { print e }')
    assert out == ["boom"]


def test_vm_catches_builtin_division_error():
    out = run_vm('try { let x = 1 / 0 } catch ZeroDivisionError e { print e["kind"] }')
    assert out == ["ZeroDivisionError"]
