"""Native PeaLang test runner with describe/test/expect/before_each/after_each syntax."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
import re
import time
import json
from typing import Callable, Optional
from .runtime import execute, PeaError


@dataclass
class NativeTestResult:
    name: str
    file: str
    passed: bool
    elapsed_ms: float
    error: str | None = None
    line: int = 0
    describe: str = ""


@dataclass
class DescribeBlock:
    name: str
    tests: list[tuple[str, str, int]]  # (name, body, line)
    before_each: str = ""
    after_each: str = ""
    nested: list["DescribeBlock"] = field(default_factory=list)


TEST_RE = re.compile(r'test\s+"([^"]+)"\s*\{')
DESCRIBE_RE = re.compile(r'describe\s+"([^"]+)"\s*\{')
BEFORE_EACH_RE = re.compile(r'before_each\s*\{')
AFTER_EACH_RE = re.compile(r'after_each\s*\{')
EXPECT_RE = re.compile(r'expect\s+(.*?)\s+to(?:_not)?\s+(\w+)\s*(\(.*?\))?', re.IGNORECASE)


def _find_block(source: str, start: int) -> tuple[str, int]:
    """Find matching brace block starting at position (start should be at '{')."""
    # If start is not at '{', find the first '{'
    while start < len(source) and source[start] != '{':
        start += 1
    if start >= len(source):
        raise SyntaxError(f"No opening brace found at or after {start}")
    
    depth = 0
    for i in range(start, len(source)):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                return source[start+1:i], i + 1  # Return content inside braces
    raise SyntaxError(f"Unclosed block starting at {start}")


def _parse_describe(source: str, start: int = 0, parent_name: str = "") -> tuple[list[DescribeBlock], str]:
    """Parse describe/test/before_each/after_each blocks from source."""
    blocks: list[DescribeBlock] = []
    setup_lines: list[str] = []
    i = start
    
    while i < len(source):
        # Skip whitespace
        if source[i].isspace():
            i += 1
            continue
            
        # Check for describe
        m = DESCRIBE_RE.match(source, i)
        if m:
            name = m.group(1)
            body, end = _find_block(source, m.end() - 1)  # Start at the '{'
            nested, nested_setup = _parse_describe(body, 0, parent_name + name + " > ")
            blocks.append(DescribeBlock(
                name=parent_name + name,
                tests=[],
                before_each="",
                after_each="",
                nested=nested
            ))
            setup_lines.append(nested_setup)
            i = end
            continue
            
        # Check for before_each
        m = BEFORE_EACH_RE.match(source, i)
        if m:
            body, end = _find_block(source, m.end() - 1)
            if blocks:
                blocks[-1].before_each = body
            else:
                setup_lines.append("# before_each (top-level)\n" + body)
            i = end
            continue
            
        # Check for after_each
        m = AFTER_EACH_RE.match(source, i)
        if m:
            body, end = _find_block(source, m.end() - 1)
            if blocks:
                blocks[-1].after_each = body
            else:
                setup_lines.append("# after_each (top-level)\n" + body)
            i = end
            continue
            
        # Check for test
        m = TEST_RE.match(source, i)
        if m:
            name = m.group(1)
            line = source[:i].count('\n') + 1
            body, end = _find_block(source, m.end() - 1)
            if blocks:
                blocks[-1].tests.append((name, body, line))
            else:
                # Top-level test
                blocks.append(DescribeBlock(
                    name=parent_name.rstrip(" > ") or "global",
                    tests=[(name, body, line)],
                    before_each="",
                    after_each="",
                    nested=[]
                ))
            i = end
            continue
            
        # Regular code - add to setup
        line_end = source.find('\n', i)
        if line_end == -1:
            line_end = len(source)
        setup_lines.append(source[i:line_end])
        i = line_end + 1 if line_end < len(source) else len(source)
    
    setup = "\n".join(setup_lines)
    return blocks, setup


def _lower_expect(body: str) -> str:
    """Convert expect assertions to assert statements with rich matchers."""
    lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith('expect '):
            # Parse: expect actual to_be expected  OR  expect actual not_to_be expected
            m = re.match(r'expect\s+(.+?)\s+(not_)?to_(\w+)\s*(?:\((.*)\))?', stripped)
            if m:
                actual, not_flag, matcher, expected = m.groups()
                not_prefix = "not " if not_flag else ""
                
                # Generate assertion based on matcher
                matchers = {
                    "equal": f"assert {not_prefix}({actual} == {expected}), f'Expected {actual} {not_prefix}to equal {expected}'",
                    "not_equal": f"assert {not_prefix}({actual} != {expected}), f'Expected {actual} {not_prefix}to not equal {expected}'",
                    "be_true": f"assert {not_prefix}({actual} is True), f'Expected {actual} {not_prefix}to be true'",
                    "be_false": f"assert {not_prefix}({actual} is False), f'Expected {actual} {not_prefix}to be false'",
                    "be_none": f"assert {not_prefix}({actual} is None), f'Expected {actual} {not_prefix}to be None'",
                    "be_truthy": f"assert {not_prefix}bool({actual}), f'Expected {actual} {not_prefix}to be truthy'",
                    "be_falsy": f"assert {not_prefix}(not {actual}), f'Expected {actual} {not_prefix}to be falsy'",
                    "contain": f"assert {not_prefix}({expected} in {actual}), f'Expected {actual} {not_prefix}to contain {expected}'",
                    "have_length": f"assert {not_prefix}(len({actual}) == {expected}), f'Expected {actual} {not_prefix}to have length {expected}'",
                    "throw": f"try: {actual}\nexcept Exception as e: pass\nelse: assert False, f'Expected {actual} {not_prefix}to throw'",
                    "match": f"assert {not_prefix}(re.search({expected}, str({actual})) is not None), f'Expected {actual} {not_prefix}to match {expected}'",
                }
                if matcher in matchers:
                    lines.append(matchers[matcher])
                else:
                    lines.append(f"# Unknown matcher: {matcher}")
            else:
                # Simple expect actual == expected OR expect actual != expected OR expect actual
                m2 = re.match(r'expect\s+(.+?)\s+(not_)?(?:to)?\s*(==|!=)\s*(.+)', stripped)
                if m2:
                    actual, not_flag, op, expected = m2.groups()
                    not_prefix = "not " if not_flag else ""
                    if op == '==':
                        lines.append(f"assert {not_prefix}{actual} == {expected}")
                    else:
                        lines.append(f"assert {not_prefix}{actual} != {expected}")
                else:
                    # Bare expect truthy
                    m3 = re.match(r'expect\s+(.+)', stripped)
                    if m3:
                        actual = m3.group(1)
                        lines.append(f"assert {actual}")
                    else:
                        lines.append(line)
        elif stripped:
            lines.append(line)
    return "\n".join(lines)


def split_tests(source: str) -> tuple[str, list[tuple[str, str, int, str]]]:
    """Extract test blocks, return (setup_code, [(test_name, body, line, describe_name)])"""
    blocks, setup = _parse_describe(source)
    
    tests = []
    for block in blocks:
        for name, body, line in block.tests:
            tests.append((name, _lower_expect(body), line, block.name))
        for nested in block.nested:
            for n, b, l in nested.tests:
                tests.append((n, _lower_expect(b), l, nested.name))
    
    return setup, tests


def run_source_tests(source: str, file: str = '<memory>', filter_text: Optional[str] = None) -> list[NativeTestResult]:
    """Run tests from a source string."""
    setup, tests = split_tests(source)
    results = []
    
    for name, body, line, describe_name in tests:
        if filter_text and filter_text.lower() not in name.lower():
            continue
            
        # Find the describe block for before/after
        block = None
        for b in _parse_describe(source)[0]:
            if b.name == describe_name:
                block = b
                break
            for n in b.nested:
                if n.name == describe_name:
                    block = n
                    break
        
        started = time.perf_counter()
        try:
            # Build test code with before/after
            test_code = setup
            if block and block.before_each:
                test_code += "\n" + block.before_each
            test_code += "\n" + _lower_expect(body)
            if block and block.after_each:
                test_code += "\n" + block.after_each
                
            execute(test_code, source_name=file)
            results.append(NativeTestResult(
                name=name, file=file, passed=True,
                elapsed_ms=(time.perf_counter() - started) * 1000,
                line=line, describe=describe_name
            ))
        except Exception as exc:
            results.append(NativeTestResult(
                name=name, file=file, passed=False,
                elapsed_ms=(time.perf_counter() - started) * 1000,
                error=str(exc), line=line, describe=describe_name
            ))
    return results


def run_paths(paths: list[str | Path], filter_text: Optional[str] = None) -> list[NativeTestResult]:
    """Run tests from multiple file paths."""
    results = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for f in p.rglob("*.pea"):
                results.extend(run_source_tests(f.read_text(encoding="utf-8"), str(f), filter_text))
        else:
            results.extend(run_source_tests(p.read_text(encoding="utf-8"), str(p), filter_text))
    return results


def coverage_summary(paths: list[Path], results: list[NativeTestResult]) -> dict:
    """Generate coverage summary."""
    total_lines = executable = 0
    for raw in paths:
        p = Path(raw)
        files = [p] if p.is_file() else list(p.rglob("*.pea"))
        for f in files:
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.lstrip().startswith(('#', 'test ', 'describe ', 'before_each', 'after_each')):
                    total_lines += 1
    executable = total_lines
    passed = sum(x.passed for x in results)
    return {
        'files': len(paths),
        'executable_lines': executable,
        'tests': len(results),
        'passed': passed,
        'failed': len(results) - passed,
        'mode': 'test-aware baseline; VM line coverage remains experimental'
    }


def to_junit_xml(results: list[NativeTestResult], testsuite_name: str = "PeaLang") -> str:
    """Generate JUnit XML output."""
    from xml.etree import ElementTree as ET
    
    testsuite = ET.Element("testsuite", name=testsuite_name, tests=str(len(results)),
                           failures=str(sum(1 for r in results if not r.passed)),
                           time=str(sum(r.elapsed_ms for r in results) / 1000))
    
    for r in results:
        testcase = ET.SubElement(testsuite, "testcase", name=r.name,
                                 classname=r.describe, time=str(r.elapsed_ms / 1000))
        if not r.passed:
            ET.SubElement(testcase, "failure", message=r.error or "Test failed").text = r.error
    
    return ET.tostring(testsuite, encoding="unicode")


# --- Matcher functions exposed to PeaLang ---

def expect(actual: any) -> "ExpectWrapper":
    """Create an expectation wrapper for fluent assertions."""
    return ExpectWrapper(actual)


class ExpectWrapper:
    def __init__(self, actual: any):
        self.actual = actual
        self.negated = False
    
    def not_(self) -> "ExpectWrapper":
        self.negated = True
        return self
    
    def to_equal(self, expected: any, msg: str = "") -> None:
        ok = self.actual == expected
        if self.negated: ok = not ok
        if not ok: raise AssertionError(msg or f"Expected {self.actual} {'not ' if self.negated else ''}to equal {expected}")
    
    def to_not_equal(self, expected: any, msg: str = "") -> None:
        self.to_equal(expected, msg)
    
    def to_be_true(self, msg: str = "") -> None:
        ok = self.actual is True
        if self.negated: ok = not ok
        if not ok: raise AssertionError(msg or f"Expected {self.actual} {'not ' if self.negated else ''}to be True")
    
    def to_be_false(self, msg: str = "") -> None:
        ok = self.actual is False
        if self.negated: ok = not ok
        if not ok: raise AssertionError(msg or f"Expected {self.actual} {'not ' if self.negated else ''}to be False")
    
    def to_be_none(self, msg: str = "") -> None:
        ok = self.actual is None
        if self.negated: ok = not ok
        if not ok: raise AssertionError(msg or f"Expected {self.actual} {'not ' if self.negated else ''}to be None")
    
    def to_contain(self, item: any, msg: str = "") -> None:
        ok = item in self.actual
        if self.negated: ok = not ok
        if not ok: raise AssertionError(msg or f"Expected {self.actual} {'not ' if self.negated else ''}to contain {item}")
    
    def to_have_length(self, length: int, msg: str = "") -> None:
        ok = len(self.actual) == length
        if self.negated: ok = not ok
        if not ok: raise AssertionError(msg or f"Expected {self.actual} {'not ' if self.negated else ''}to have length {length}")
    
    def to_match(self, pattern: str, msg: str = "") -> None:
        import re
        ok = re.search(pattern, str(self.actual)) is not None
        if self.negated: ok = not ok
        if not ok: raise AssertionError(msg or f"Expected {self.actual} {'not ' if self.negated else ''}to match {pattern}")
    
    def to_throw(self, msg: str = "") -> None:
        try:
            if callable(self.actual):
                self.actual()
            ok = False
        except Exception:
            ok = True
        if self.negated: ok = not ok
        if not ok: raise AssertionError(msg or f"Expected function {'not ' if self.negated else ''}to throw")


def build_native_testing_namespace() -> dict[str, any]:
    return {
        "run_source_tests": run_source_tests,
        "run_paths": run_paths,
        "coverage_summary": coverage_summary,
        "to_junit_xml": to_junit_xml,
        "expect": expect,
        "DescribeBlock": DescribeBlock,
        "NativeTestResult": NativeTestResult,
    }