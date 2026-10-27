from pealang.lineage import DatasetRef,ColumnRef,LineageGraph
from pealang.pipeline_observability import RunMetric,SLAPolicy,SLAEvaluator,MetricsRegistry,AuditReport
from pealang.dashboard import Dashboard,dashboard_from_dict,render_react

def test_dataset_and_column_lineage():
    raw=DatasetRef("employees_raw","hr"); clean=DatasetRef("employees_clean","hr")
    salary=ColumnRef(raw,"salary","decimal"); total=ColumnRef(clean,"total_compensation","decimal")
    g=LineageGraph(); g.add_column(salary); g.add_column(total); g.connect(salary,total,"derive","salary + bonus")
    assert g.downstream(salary.id)==[total.id]; assert g.upstream(total.id)==[salary.id]; assert g.validate()["valid"]

def test_sla_metrics_and_audit():
    m=RunMetric("daily_hr","r1","a","b",125.0,"failed",5,1)
    alerts=SLAEvaluator().evaluate(m,SLAPolicy(max_duration_seconds=60))
    assert {a.code for a in alerts}=={"SLA_DURATION","SLA_TASK_FAILURES","SLA_RUN_STATE"}
    reg=MetricsRegistry(); reg.record(m); assert reg.summary("daily_hr")["runs"]==1
    assert AuditReport.build(m,alerts)["schema"]=="pealang.audit.v1"

def test_dashboard_dsl_and_react_renderer():
    d=Dashboard("Operations").add("metric","Success rate",source="summary",value="success_rate").add("table","Runs",source="runs")
    code=render_react(d,"OperationsDashboard")
    assert "function OperationsDashboard" in code and "pea-dashboard" in code
    loaded=dashboard_from_dict(d.to_dict()); assert len(loaded.components)==2
