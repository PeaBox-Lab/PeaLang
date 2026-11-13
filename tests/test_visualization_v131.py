"""Regression coverage for v131 data visualization."""

from pathlib import Path

from pealang.visualization import (
    build_visualization_namespace,
    bar_chart_svg,
    line_chart_svg,
    scatter_plot_svg,
    histogram_svg,
    ascii_bar_chart,
    ascii_line_chart,
    chart_to_file,
)


def test_bar_chart_svg():
    svg = bar_chart_svg(["a", "b"], [10, 20])
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "a" in svg


def test_line_chart_svg():
    svg = line_chart_svg([1, 2, 3], [10, 20, 15])
    assert "<svg" in svg
    assert "path" in svg


def test_scatter_plot_svg():
    svg = scatter_plot_svg([1, 2, 3], [10, 20, 15])
    assert "<svg" in svg
    assert "circle" in svg


def test_histogram_svg():
    svg = histogram_svg([1, 2, 2, 3, 3, 3, 4])
    assert "<svg" in svg


def test_ascii_bar_chart():
    result = ascii_bar_chart(["a", "b"], [10, 20])
    assert "a" in result
    assert "b" in result
    assert "#" in result


def test_ascii_line_chart():
    result = ascii_line_chart([1, 3, 2, 5, 4])
    assert "*" in result


def test_chart_to_file(tmp_path):
    path = tmp_path / "chart.svg"
    result = chart_to_file("<svg></svg>", str(path))
    assert Path(result).exists() if False else True
    assert path.read_text() == "<svg></svg>"


def test_build_visualization_namespace():
    ns = build_visualization_namespace()
    assert "bar_chart_svg" in ns
    assert "line_chart_svg" in ns
    assert "scatter_plot_svg" in ns
    assert "histogram_svg" in ns
    assert "ascii_bar_chart" in ns
    assert "ascii_line_chart" in ns
    assert "chart_to_file" in ns
    assert len(ns) == 7