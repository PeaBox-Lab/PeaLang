


from pealang.dashboard import DashboardFilter,DashboardState,DataBinding,apply_dashboard_filters
from pealang.browser_repl import BrowserREPL,DatasetInspector
from pealang.jupyter import RichDisplay,PeaKernel,kernelspec
from pealang.data import DataFrame

def test_dashboard_filters_and_state():
    rows=[{"country":"IN","cost":10},{"country":"US","cost":20},{"country":"IN","cost":30}]
    fs=[DashboardFilter("country","country","select","IN"),DashboardFilter("cost","cost","range",(5,25))]
    assert apply_dashboard_filters(rows,fs,DashboardState())==[{"country":"IN","cost":10}]
    assert DataBinding("employees",x="country",y="cost").source=="employees"

def test_browser_repl_protocol_and_inspector():
    repl=BrowserREPL(lambda s:{"source":s,"length":len(s)})
    r=repl.protocol({"type":"execute","request_id":"1","source":"let x=1"}); assert r["ok"] and r["request_id"]=="1"
    info=DatasetInspector().inspect([{"a":1},{"a":2}],limit=1); assert info["row_count"]==2 and info["rows"]==[{"a":1}]
    prof=DatasetInspector().column_profile([{"a":1},{"a":None},{"a":1}],"a"); assert prof["null_count"]==1 and prof["distinct_count"]==1

def test_jupyter_rich_results_and_kernel_contract():
    frame=DataFrame([{"a":1},{"a":2}]); rich=RichDisplay.dataframe(frame)
    assert "text/html" in rich.data and "application/vnd.pealang.dataframe+json" in rich.data
    k=PeaKernel(lambda code:frame); result=k.execute("data"); assert result["status"]=="ok" and result["execution_count"]==1
    assert kernelspec()["language"]=="pealang"



