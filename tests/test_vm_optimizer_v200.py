"""Regression coverage for v2.0.0 VM optimizer and package hub."""

import json
import tempfile
import os
from pathlib import Path

from pealang.vm_optimizer import (
    build_vm_optimizer_namespace,
    OptimizationHints,
    constant_fold,
    loop_unroll_hint,
    encode_bytecode_v2,
    decode_bytecode_v2,
    inspect_bytecode_v2,
    benchmark_vm,
    benchmark_compare,
    PackageIndex,
)


def test_constant_fold():
    assert constant_fold("2 + 3") == "5"
    assert constant_fold("10 * 4") == "40"
    assert constant_fold("x + 1") == "x + 1"  # not foldable


def test_loop_unroll_hint():
    result = loop_unroll_hint(4)
    assert result["should_unroll"] is True
    assert result["iterations"] == 4


def test_loop_unroll_hint_large():
    result = loop_unroll_hint(20)
    assert result["should_unroll"] is False


def test_encode_decode_bytecode_v2():
    instructions = [{"op": "LOAD", "arg": 1}, {"op": "ADD"}, {"op": "STORE", "arg": 0}]
    data = encode_bytecode_v2(instructions)
    assert data.startswith(b"PEACv2")
    decoded = decode_bytecode_v2(data)
    assert decoded["version"] == 2
    assert decoded["instructions"] == instructions


def test_inspect_bytecode_v2():
    instructions = [{"op": "LOAD", "arg": 1}]
    data = encode_bytecode_v2(instructions)
    info = inspect_bytecode_v2(data)
    assert info["version"] == 2
    assert info["instruction_count"] == 1
    assert info["size_bytes"] == len(data)


def test_bytecode_checksum():
    instructions = [{"op": "LOAD", "arg": 1}]
    data = encode_bytecode_v2(instructions)
    # Tamper with data
    tampered = data[:-5] + b"XXXXX"
    try:
        decode_bytecode_v2(tampered)
        assert False, "Should have raised"
    except ValueError:
        pass


def test_optimization_hints():
    hints = OptimizationHints()
    assert hints.constant_folding is True
    d = hints.to_dict()
    assert "constant_folding" in d
    hints.apply({"constant_folding": False})
    assert hints.constant_folding is False


def test_benchmark_vm():
    result = benchmark_vm("let x = 1 + 2", iterations=5)
    assert "min_ms" in result
    assert "mean_ms" in result
    assert result["iterations"] == 5


def test_benchmark_compare():
    result = benchmark_compare("let x = 1", iterations=3)
    assert "baseline" in result
    assert "optimized_estimate" in result
    assert result["optimized_estimate"]["speedup"] == 1.25


def test_package_index():
    with tempfile.TemporaryDirectory() as d:
        idx = PackageIndex(os.path.join(d, "index"))
        idx.publish("mypkg", "1.0.0", {"author": "test"})
        idx.publish("mypkg", "1.1.0")
        result = idx.resolve("mypkg")
        assert result["version"] == "1.1.0"
        result2 = idx.resolve("mypkg", "1.0.0")
        assert result2["version"] == "1.0.0"
        assert idx.search("mypkg") != []
        assert idx.list_packages() != []
        scan = idx.security_scan("mypkg")
        assert scan["passed"] is True
        assert idx.remove("mypkg") is True
        assert idx.resolve("mypkg") is None


def test_build_vm_optimizer_namespace():
    ns = build_vm_optimizer_namespace()
    assert "OptimizationHints" in ns
    assert "constant_fold" in ns
    assert "encode_bytecode_v2" in ns
    assert "PackageIndex" in ns
    assert len(ns) == 10
