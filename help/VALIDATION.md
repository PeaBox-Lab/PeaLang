# Data validation and schema enforcement (v132)

PeaLang provides dependency-free tools for defining schemas, validating records,
and generating data-quality reports.

## Key functions

- `analysis.build_schema(fields)` — build a schema from field dicts
- `analysis.validate_record(record, schema)` — validate a single record
- `analysis.validate_records(records, schema)` — validate a list
- `analysis.check_type(value, dtype)` — type check
- `analysis.data_quality_report(records)` — quality summary
- `analysis.missing_summary(records)` — missing values per column
- `analysis.duplicate_rows(records)` — duplicate row indices
- `analysis.infer_schema(records)` — infer schema from data