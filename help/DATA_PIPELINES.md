# Data pipelines help

Load with `analysis.read_csv_file`, `analysis.read_json_file`, or `analysis.read_jsonl_file`; clean with `analysis.dropna`, `analysis.fillna`, and `analysis.clean_missing`; transform with `analysis.add_column`, `analysis.cast`, `analysis.normalize`; aggregate with `analysis.group_by` or `analysis.sql`; and write results with `analysis.write_csv_file`, `analysis.write_json_file`, or `analysis.write_jsonl_file`. `analysis.sql` runs SQLite SQL over in-memory records, including `GROUP BY` and window functions. Runnable examples live in `examples/use_cases/`.
