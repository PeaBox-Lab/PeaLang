

import json,zipfile,pytest
from pealang.operations_hardening import *
def test_trace_context():
 e=InMemorySpanExporter();t=Tracer(e);incoming=TraceContext.from_headers({"traceparent":"00-0123456789abcdef0123456789abcdef-0123456789abcdef-01","baggage":"tenant=demo"})
 with t.span("connector.call",context=incoming) as active:
  h=inject_trace_headers();assert active.trace_id==incoming.trace_id and h["baggage"]=="tenant=demo"
 assert e.records[0].parent_span_id==incoming.span_id
def test_trace_error():
 e=InMemorySpanExporter()
 with pytest.raises(ValueError):
  with Tracer(e).span("dag.node"):raise ValueError("bad")
 assert e.records[0].status is SpanStatus.ERROR and e.records[0].error_type=="ValueError"
def test_metrics():
 m=MetricRegistry(max_series=1);assert m.record("connector_requests_total",1,attributes={"connector":"sql"}).name=="pealang_connector_requests_total"
 with pytest.raises(RuntimeError):m.record("connector_requests_total",1,attributes={"connector":"sftp"})
 with pytest.raises(ValueError):m.record("Bad.Name",1)
def test_health():
 h=HealthRegistry();h.add_liveness("runtime",lambda:True);h.add_readiness("db",lambda:False);assert h.liveness().healthy and not h.readiness().healthy
def test_bundle(tmp_path):
 p=tmp_path/"d.zip";DiagnosticBundleBuilder(max_file_bytes=2048).add_runtime_summary("0.80.0a1").add_json("config",{"token":"secret","mode":"test"}).build(p)
 with zipfile.ZipFile(p) as z:assert json.loads(z.read("config.json"))["token"]=="[REDACTED]" and "config.json" in json.loads(z.read("manifest.json"))


