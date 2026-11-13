"""Calendar feature extraction for dates and datetimes.

Tables usually store timestamps as strings, but models need numbers. This
module parses common textual date formats and expands them into calendar
features such as year, month, weekday, quarter, seasonality encodings and an
epoch day trend. It is pure Python and dependency-free.

The same helpers back the ``date`` pipeline step in :mod:`pealang.pipeline`, so
date expansion can be composed with imputation, encoding and scaling.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from typing import Any, Iterable

DEFAULT_PARTS = (
    "year", "month", "day", "weekday", "quarter", "is_weekend",
)

PART_NAMES = (
    "year",
    "month",
    "day",
    "weekday",
    "quarter",
    "day_of_year",
    "week",
    "is_weekend",
    "is_month_start",
    "is_month_end",
    "epoch_day",
    "month_sin",
    "month_cos",
    "weekday_sin",
    "weekday_cos",
)

_EPOCH = date(1970, 1, 1)
_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d")


def normalize_parts(parts: Any) -> list[str]:
    if parts is None:
        items = list(DEFAULT_PARTS)
    elif isinstance(parts, str):
        items = [parts]
    else:
        items = [str(part) for part in parts]
    resolved: list[str] = []
    for item in items:
        name = item.strip().lower()
        if not name:
            raise ValueError("date parts must not be blank")
        if name not in PART_NAMES:
            raise ValueError(
                "unknown date part: " + repr(item) +
                " (expected " + ", ".join(PART_NAMES) + ")"
            )
        if name not in resolved:
            resolved.append(name)
    if not resolved:
        raise ValueError("date parts must not be empty")
    return resolved


def parse_date(value: Any) -> date:
    """Parse a date, datetime or common date string into a ``date``."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, bool) or not isinstance(value, str):
        raise ValueError("cannot parse date: " + repr(value))
    text = value.strip()
    if not text:
        raise ValueError("cannot parse date: " + repr(value))
    head = text.split("T")[0].split(" ")[0]
    for pattern in _FORMATS:
        try:
            return datetime.strptime(head, pattern).date()
        except ValueError:
            continue
    raise ValueError(
        "cannot parse date: " + repr(value) +
        " (expected YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD or YYYYMMDD)"
    )


def is_date(value: Any) -> bool:
    """Return whether a value parses as a date."""
    try:
        parse_date(value)
    except ValueError:
        return False
    return True


def date_parts(value: Any, parts: Any = None) -> dict[str, Any]:
    """Return the requested calendar features for one date value.

    ``weekday`` is Monday ``0`` through Sunday ``6``. ``week`` is the ISO week
    and ``epoch_day`` counts days since 1970-01-01. ``month_sin``/``month_cos``
    and ``weekday_sin``/``weekday_cos`` are cyclic encodings that keep December
    next to January and Sunday next to Monday.
    """
    day_value = parse_date(value)
    resolved = normalize_parts(parts)
    month = day_value.month
    day_of_month = day_value.day
    weekday = day_value.weekday()
    out: dict[str, Any] = {}
    for part in resolved:
        if part == "year":
            out[part] = day_value.year
        elif part == "month":
            out[part] = month
        elif part == "day":
            out[part] = day_of_month
        elif part == "weekday":
            out[part] = weekday
        elif part == "quarter":
            out[part] = (month - 1) // 3 + 1
        elif part == "day_of_year":
            out[part] = day_value.timetuple().tm_yday
        elif part == "week":
            out[part] = day_value.isocalendar()[1]
        elif part == "is_weekend":
            out[part] = 1 if weekday >= 5 else 0
        elif part == "is_month_start":
            out[part] = 1 if day_of_month == 1 else 0
        elif part == "is_month_end":
            following = day_value + timedelta(days=1)
            out[part] = 1 if following.month != month else 0
        elif part == "epoch_day":
            out[part] = (day_value - _EPOCH).days
        elif part == "month_sin":
            out[part] = math.sin(2.0 * math.pi * (month - 1) / 12.0)
        elif part == "month_cos":
            out[part] = math.cos(2.0 * math.pi * (month - 1) / 12.0)
        elif part == "weekday_sin":
            out[part] = math.sin(2.0 * math.pi * weekday / 7.0)
        elif part == "weekday_cos":
            out[part] = math.cos(2.0 * math.pi * weekday / 7.0)
    return out


def calendar_features(values: Iterable[Any], parts: Any = None,
                      prefix: Any = None) -> dict[str, Any]:
    """Expand a sequence of dates into a numeric feature matrix.

    Returns ``{features, names, parts, n}``. ``names`` are the part names, or
    ``prefix + "_" + part`` when a prefix is given.

    ```pea
    let matrix = stats.calendar_features(dates, ["year", "month", "weekday"])
    print matrix["names"]
    print matrix["features"]
    ```
    """
    if isinstance(values, str):
        raise ValueError("values must be an iterable of dates")
    if values is None:
        raise ValueError("values are required")
    items = list(values)
    if not items:
        raise ValueError("values are required")
    resolved = normalize_parts(parts)
    label = ""
    if prefix is not None:
        label = str(prefix).strip()
        if not label:
            raise ValueError("prefix must not be empty")
        label += "_"
    features: list[list[Any]] = []
    for index, value in enumerate(items):
        try:
            record = date_parts(value, resolved)
        except ValueError as error:
            raise ValueError(
                "cannot parse date at row " + str(index) + ": "
                + repr(value)
            ) from None
        features.append([record[part] for part in resolved])
    return {
        "features": features,
        "names": [label + part for part in resolved],
        "parts": resolved,
        "n": len(features),
    }


def build_dates_namespace() -> dict[str, Any]:
    return {
        "is_date": is_date,
        "date_parts": date_parts,
        "calendar_features": calendar_features,
    }
