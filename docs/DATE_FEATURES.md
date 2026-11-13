# Date Features

Dates usually arrive as strings, but estimators need numbers. PeaLang parses
common textual date formats and expands them into calendar features: year,
month, weekday, quarter, seasonality encodings, month boundaries and an epoch
day trend. Everything is pure Python and dependency-free, and the same helpers
back a `date` pipeline step.

Exposed through:

- `stats.*` — global namespace, always available.
- `std.stats.*` — stable standard-library module.
- `analysis.*` — record-friendly column expansion.
- the `date` step in `stats.fit_pipeline`.

## Parsing

Accepted values are:

- `YYYY-MM-DD`, `YYYY/MM/DD`, `YYYY.MM.DD`
- `YYYYMMDD`
- any of the above followed by `T` or a space and a time, for example
  `2024-03-09T12:30:00`
- Python `date` and `datetime` values from interop

Surrounding whitespace is trimmed. The time component and any timezone
information are ignored; only the calendar date is used.

```pea
print stats.is_date("2024-02-29")
print stats.date_parts("2024-03-09", ["weekday", "epoch_day"])
```

`stats.is_date(value)` returns a boolean. `stats.date_parts(value, parts)`
returns a record of the requested parts. Use it for one-off values; use the
matrix helpers for columns.

Invalid values raise `ValueError` with the original text. `2023-02-29` and
`2024-13-01` do not parse.

## Parts

| Part | Value |
|---|---|
| `year` | four-digit year |
| `month` | `1` to `12` |
| `day` | `1` to `31` |
| `weekday` | `0` Monday to `6` Sunday |
| `quarter` | `1` to `4` |
| `day_of_year` | `1` to `366` |
| `week` | ISO week, `1` to `53` |
| `is_weekend` | `1` on Saturday/Sunday, else `0` |
| `is_month_start` | `1` on the first day of a month |
| `is_month_end` | `1` on the last day of a month |
| `epoch_day` | days since `1970-01-01`, may be negative |
| `month_sin` | `sin(2*pi*(month-1)/12)` |
| `month_cos` | `cos(2*pi*(month-1)/12)` |
| `weekday_sin` | `sin(2*pi*weekday/7)` |
| `weekday_cos` | `cos(2*pi*weekday/7)` |

The default parts are `year`, `month`, `day`, `weekday`, `quarter` and
`is_weekend`. Parts are returned in the order requested, and duplicates are
removed.

The cyclic parts keep December next to January and Sunday next to Monday, which
helps linear models. Trees often fit raw `month` and `weekday` more directly.

## Numeric matrices

```pea
let matrix = stats.calendar_features(
    ["2024-01-05", "2024-02-10"],
    ["year", "month", "weekday"]
)
print matrix["names"]     // ["year", "month", "weekday"]
print matrix["features"]  // [[2024, 1, 4], [2024, 2, 5]]
print matrix["n"]
```

`stats.calendar_features(values, parts, prefix)` returns
`{features, names, parts, n}`. A prefix renames the output columns to
`prefix_part`. A single string, an empty sequence and unknown parts raise
`ValueError`; an unparseable value reports its row index.

## Adding columns to records

```pea
let rows = [{"when": "2024-01-05", "sales": 10.0}]
let expanded = analysis.date_features(
    rows, "when", ["month", "weekday"], null, false
)
print expanded[0]["when_month"]
print expanded[0]["when_weekday"]
```

`analysis.date_features(data, column, parts, prefix, drop_original)` returns
new records with `<column>_<part>` columns, or `<prefix>_<part>` when a prefix
is given. `drop_original = true` removes the source column. Other columns are
preserved.

Missing and unparseable dates raise with the row index, so impute or filter
them first. The helper does not guess.

## Pipeline step

```pea
let steps = [
    {"op": "impute", "method": "auto"},
    {"op": "date", "parts": ["year", "month", "weekday", "epoch_day"]},
    {"op": "encode", "method": "onehot"},
    {"op": "scale", "method": "standard"}
]
let fitted = stats.fit_pipeline(steps, features, ["when", "region", "spend"])
print fitted["names"]
print fitted["steps"][1]["columns"]
```

A `date` step detects columns whose observed values all parse as dates and
replaces each with one column per part, named `column=part`. Other columns pass
through untouched. `parts` defaults to the standard set.

- `{"op": "date", "required": false}` leaves the data unchanged when no date
  column is present. This is what `analysis.model_pipeline` uses by default.
- An explicit `{"op": "date"}` is required by default and raises when it finds
  no date columns, which catches misspelled or mistyped columns.
- Missing values in a detected date column raise; add an `impute` step first.
  `auto` imputation fills date strings with the most common date.
- Order matters: impute, then date, then encode, then scale.

The fitted transformer stores the chosen parts per column, so
`stats.transform_pipeline` expands new rows the same way and
`stats.save_model` persists the step. See
[`docs/FEATURE_PIPELINES.md`](FEATURE_PIPELINES.md) and
[`docs/MODEL_PERSISTENCE.md`](MODEL_PERSISTENCE.md).

## Model wrapper

`analysis.model_pipeline` now runs impute, date, encode and scale when
`steps = null`. Dates are expanded automatically with the default parts, and
datasets without dates are unaffected.

```pea
let model = analysis.model_pipeline(
    rows, "sales", ["when", "region"], null, "forest", "regression",
    {"n_estimators": 50, "max_depth": 6}
)
print model["output_features"]
print model["importance"][0]["feature"]
print analysis.predict_pipeline(model, [{"when": "2025-01-15", "region": "north"}])
```

## Choosing parts

- Add `epoch_day` for a numeric trend. `year` alone gives a step per year and
  is constant for single-year data, where scaling turns it into a zero column.
- Add `month_sin`, `month_cos`, `weekday_sin` and `weekday_cos` for linear or
  distance-based models that need smooth seasonality.
- Use `week`, `day_of_year` or `is_month_start`/`is_month_end` for calendar
  effects that raw month/day do not capture.
- Keep the part list small. Each date column becomes one column per part, and
  wide date expansions can dominate a model.

## Runnable example

- [`examples/use_cases/22_date_features.pea`](../examples/use_cases/22_date_features.pea)

```bash
pea run examples/use_cases/22_date_features.pea
```

The example builds two years of daily sales from date strings, shows the
single-value, matrix and record-column helpers, fits a default pipeline model
(month is the top feature), fits a second model with `epoch_day`, and scores a
future date and a row with a missing date.

## Assumptions and limitations

- Only the date component is used. There are no hour, minute, second or
  time-of-day features yet, and no timezone conversion.
- Automatic date detection is a heuristic. An eight-digit string that happens
  to be a valid date is treated as one; use explicit `steps` without a date
  step to keep such columns numeric or categorical.
- Fiscal calendars, holidays, business-day counts and locale-specific day
  names are not included.
- A detected date column must be complete. Mode imputation keeps a date-typed
  column but fills it with an arbitrary observed date, which may mislead a
  model; consider adding an `is_missing` indicator before imputing.
- Leap years and month lengths are handled by the standard library. Years must
  be four digits and within `0001` to `9999`.
