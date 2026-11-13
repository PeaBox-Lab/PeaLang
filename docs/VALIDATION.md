# Data validation and schema enforcement (v132)

PeaLang provides dependency-free tools for defining schemas, validating records,
and generating data-quality reports.

## Schema definition

Build a schema from a list of field dicts:

```python
schema = analysis.build_schema([
    {"name": "age", "dtype": "int", "required": True, "min_value": 0, "max_value": 120},
    {"name": "name", "dtype": "string", "required": True},
])
```

## Validation

- `validate_record(record, schema)` — validate a single record
- `validate_records(records, schema)` — validate a list of records
- `check_type(value, dtype)` — check if a value matches a type

## Data quality

- `data_quality_report(records)` — comprehensive quality summary
- `missing_summary(records)` — missing value counts per column
- `duplicate_rows(records)` — indices of duplicate rows
- `infer_schema(records)` — infer a schema from data

## Supported types

`any`, `string`/`str`, `int`/`integer`, `float`/`number`, `bool`/`boolean`, `list`, `dict`, `null`