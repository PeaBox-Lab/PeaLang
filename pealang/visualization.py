"""Dependency-free data visualization helpers for PeaLang.

Generates SVG charts and ASCII plots from tabular data without any external
plotting library.  Output can be embedded in reports, notebooks or saved to
files.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Iterable, Sequence


def _nums(values: Iterable[Any]) -> list[float]:
    out = []
    for v in values or []:
        if v is None or isinstance(v, bool):
            continue
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            continue
    return out


def _min_max(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 1.0
    return min(values), max(values)


def bar_chart_svg(labels: Sequence[Any], values: Sequence[Any], title: str = "",
                  width: int = 400, height: int = 300,
                  color: str = "#4C78A8") -> str:
    """Generate an SVG bar chart."""
    vals = _nums(values)
    if not vals:
        return "<svg></svg>"
    lo, hi = 0.0, max(vals) if vals else 1.0
    if hi == 0:
        hi = 1.0
    n = len(vals)
    bar_w = (width - 60) / n
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    if title:
        parts.append(f'<text x="{width//2}" y="20" text-anchor="middle" font-size="14" font-weight="bold">{title}</text>')
    for i, (label, val) in enumerate(zip(labels, vals)):
        x = 40 + i * bar_w
        bar_h = (val / hi) * (height - 60)
        y = height - 40 - bar_h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w*0.8:.1f}" height="{bar_h:.1f}" fill="{color}"/>')
        parts.append(f'<text x="{x + bar_w*0.4:.1f}" y="{height - 25}" text-anchor="middle" font-size="10">{label}</text>')
        parts.append(f'<text x="{x + bar_w*0.4:.1f}" y="{y - 5:.1f}" text-anchor="middle" font-size="9">{val:.1f}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def line_chart_svg(x: Sequence[Any], y: Sequence[Any], title: str = "",
                   width: int = 400, height: int = 300,
                   color: str = "#4C78A8") -> str:
    """Generate an SVG line chart."""
    xs = _nums(x)
    ys = _nums(y)
    if not xs or not ys:
        return "<svg></svg>"
    n = min(len(xs), len(ys))
    xs, ys = xs[:n], ys[:n]
    xlo, xhi = _min_max(xs)
    ylo, yhi = _min_max(ys)
    if xhi == xlo:
        xhi = xlo + 1
    if yhi == ylo:
        yhi = ylo + 1
    pts = []
    for xi, yi in zip(xs, ys):
        px = 40 + (xi - xlo) / (xhi - xlo) * (width - 80)
        py = height - 40 - (yi - ylo) / (yhi - ylo) * (height - 80)
        pts.append((px, py))
    path = "M " + " L ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    if title:
        parts.append(f'<text x="{width//2}" y="20" text-anchor="middle" font-size="14" font-weight="bold">{title}</text>')
    parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2"/>')
    for px, py in pts:
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="{color}"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def scatter_plot_svg(x: Sequence[Any], y: Sequence[Any], title: str = "",
                    width: int = 400, height: int = 300,
                    color: str = "#4C78A8") -> str:
    """Generate an SVG scatter plot."""
    xs = _nums(x)
    ys = _nums(y)
    if not xs or not ys:
        return "<svg></svg>"
    n = min(len(xs), len(ys))
    xs, ys = xs[:n], ys[:n]
    xlo, xhi = _min_max(xs)
    ylo, yhi = _min_max(ys)
    if xhi == xlo:
        xhi = xlo + 1
    if yhi == ylo:
        yhi = ylo + 1
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    if title:
        parts.append(f'<text x="{width//2}" y="20" text-anchor="middle" font-size="14" font-weight="bold">{title}</text>')
    for xi, yi in zip(xs, ys):
        px = 40 + (xi - xlo) / (xhi - xlo) * (width - 80)
        py = height - 40 - (yi - ylo) / (yhi - ylo) * (height - 80)
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{color}" opacity="0.7"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def histogram_svg(values: Sequence[Any], title: str = "", bins: int = 10,
                 width: int = 400, height: int = 300,
                 color: str = "#4C78A8") -> str:
    """Generate an SVG histogram."""
    vals = _nums(values)
    if not vals:
        return "<svg></svg>"
    lo, hi = _min_max(vals)
    if hi == lo:
        hi = lo + 1
    bin_width = (hi - lo) / bins
    counts = [0] * bins
    for v in vals:
        idx = min(int((v - lo) / bin_width), bins - 1)
        counts[idx] += 1
    labels = [f"{lo + i * bin_width:.1f}" for i in range(bins)]
    return bar_chart_svg(labels, counts, width=width, height=height, title=title, color=color)


def ascii_bar_chart(labels: Sequence[Any], values: Sequence[Any], *,
                    width: int = 40) -> str:
    """Generate an ASCII bar chart for terminal output."""
    vals = _nums(values)
    if not vals:
        return ""
    hi = max(vals) if vals else 1.0
    if hi == 0:
        hi = 1.0
    lines = []
    for label, val in zip(labels, vals):
        bar_len = int((val / hi) * width)
        bar = "#" * bar_len
        lines.append(f"{str(label):>12} | {bar} {val:.1f}")
    return "\n".join(lines)


def ascii_line_chart(values: Sequence[Any], *, width: int = 60, height: int = 15) -> str:
    """Generate an ASCII line chart for terminal output."""
    vals = _nums(values)
    if not vals:
        return ""
    lo, hi = _min_max(vals)
    if hi == lo:
        hi = lo + 1
    # Normalize to height
    rows = [[" "] * width for _ in range(height)]
    for i, v in enumerate(vals):
        if i >= width:
            break
        y = int((v - lo) / (hi - lo) * (height - 1))
        y = height - 1 - y
        rows[y][i] = "*"
    return "\n".join("".join(r) for r in rows)


def chart_to_file(svg: str, path: str) -> str:
    """Write an SVG chart to a file."""
    pp = Path(path)
    pp.parent.mkdir(parents=True, exist_ok=True)
    pp.write_text(svg, encoding="utf-8")
    return str(pp)


def build_visualization_namespace() -> dict[str, Any]:
    return {
        "bar_chart_svg": bar_chart_svg,
        "line_chart_svg": line_chart_svg,
        "scatter_plot_svg": scatter_plot_svg,
        "histogram_svg": histogram_svg,
        "ascii_bar_chart": ascii_bar_chart,
        "ascii_line_chart": ascii_line_chart,
        "chart_to_file": chart_to_file,
    }
