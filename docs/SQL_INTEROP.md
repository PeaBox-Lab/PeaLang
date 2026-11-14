# SQL and DataFrame interop (v135)

PeaLang provides enhanced SQL-over-records and DataFrame-like operations.

## SQL queries

- `analysis.sql_query(records, query)` — execute SQL over records
- `analysis.sql_value(records, query)` — return a single scalar value

## DataFrame operations

- `analysis.dataframe_from_records(records)` — create DataFrame-like dict
- `analysis.dataframe_select(df, columns)` — select columns
- `analysis.dataframe_filter(df, condition)` — filter rows
- `analysis.dataframe_sort(df, column, ascending)` — sort
- `analysis.dataframe_groupby(df, group_col, agg_col, agg)` — group and aggregate
- `analysis.dataframe_head(df, n)` / `dataframe_tail(df, n)` — slice
- `analysis.dataframe_describe(df)` — describe numeric columns
- `analysis.dataframe_to_records(df)` — convert back to records

## Window functions

- `analysis.window_function(records, column, func, partition_by, order_by)` — apply window function (row_number, rank, dense_rank, sum, avg)