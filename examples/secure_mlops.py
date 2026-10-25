


from pealang.mlops_secure import MonitoringStore,AlertRule,evaluate_alerts
store=MonitoringStore("monitoring.json")
event=store.record("demo","drift",0.23)
print(evaluate_alerts("demo",[event],[AlertRule("drift",0.2,severity="critical",rollback=True)]))



