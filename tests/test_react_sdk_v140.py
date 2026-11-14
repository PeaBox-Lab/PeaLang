"""Regression coverage for v1.4.0 React SDK."""

from pealang.react_sdk import (
    build_react_sdk_namespace,
    generate_react_hooks,
    generate_data_grid_adapter,
    generate_chart_adapter,
    REACT_HOOKS,
)


def test_generate_react_hooks():
    src = generate_react_hooks()
    assert "usePeaRuntime" in src
    assert "usePeaScript" in src
    assert "usePeaDataFrame" in src
    assert "usePeaQuery" in src
    assert "usePeaValidation" in src
    assert "useState" in src
    assert "useEffect" in src


def test_generate_data_grid_adapter():
    src = generate_data_grid_adapter()
    assert "peaFrameToGridRows" in src
    assert "peaFrameToColumnDefs" in src
    assert "peaFilterRows" in src
    assert "peaSortRows" in src


def test_generate_chart_adapter():
    src = generate_chart_adapter()
    assert "peaToVegaLite" in src
    assert "peaToChartJs" in src
    assert "vega-lite" in src


def test_react_hooks_dict():
    assert "usePeaScript" in REACT_HOOKS
    assert "usePeaDataFrame" in REACT_HOOKS
    assert len(REACT_HOOKS) == 4


def test_build_react_sdk_namespace():
    ns = build_react_sdk_namespace()
    assert "generate_react_hooks" in ns
    assert "generate_data_grid_adapter" in ns
    assert "generate_chart_adapter" in ns
    assert "REACT_HOOKS" in ns
    assert len(ns) == 4
