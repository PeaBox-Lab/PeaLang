# SQL and DataFrame interop (v135)

PeaLang provides enhanced SQL-over-records and DataFrame-like operations.

## Key functions

- `analysis.sql_query(records, query)` — SQL over records
- `analysis.sql_value(records, query)` — scalar result
- `analysis.dataframe_from_records(records)` — create DataFrame
- `analysis.dataframe_select(df, columns)` — select columns
- `analysis.dataframe_filter(df, condition)` — filter rows
- `analysis.dataframe_sort(df, column, ascending)` — sort
- `analysis.dataframe_groupby(df, group_col, agg_col, agg)` — group/aggregate
- `analysis.dataframe_head(df, n)` / `dataframe_tail(df, n)` — slice
- `analysis.dataframe_describe(df)` — describe
- `analysis.window_function(records, column, func, partition_by, order_by)` — window function