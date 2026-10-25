


from pealang.data import DataFrame
df=DataFrame([{"date":"2026-01-01","sales":10},{"date":"2026-01-02","sales":15}])
print(df.resample("date","month","sales","sum").to_dicts())
print(df.pct_change("sales").to_dicts())



