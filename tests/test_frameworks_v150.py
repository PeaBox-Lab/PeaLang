"""Regression coverage for frameworks & architecture toolkit."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parent.parent)

from pealang.frameworks import (
    build_frameworks_namespace,
    scaffold_backend,
    scaffold_fullstack,
    write_scaffold,
    adr,
    adr_index,
    adr_transition,
    adr_filter,
    service_contract,
    service_contract_to_openapi,
    openapi_json,
    layered_architecture_check,
)


def test_scaffold_backend_fastapi():
    out = scaffold_backend("orders", framework="fastapi", port=8080)
    assert out["framework"] == "fastapi"
    assert "requirements.txt" in out["files"]
    assert "fastapi" in out["files"]["requirements.txt"]
    assert "app/main.py" in out["files"]
    assert "/health" in out["files"]["app/main.py"]
    assert "8080" in out["files"]["Dockerfile"]


def test_scaffold_backend_flask():
    out = scaffold_backend("catalog", framework="flask")
    assert out["framework"] == "flask"
    assert "Flask" in out["files"]["app/main.py"]


def test_scaffold_backend_express():
    out = scaffold_backend("payments", framework="express")
    assert out["framework"] == "express"
    assert "express" in out["files"]["package.json"]
    assert "express()" in out["files"]["src/index.js"]


def test_scaffold_backend_gin():
    out = scaffold_backend("gateway", framework="gin")
    assert out["framework"] == "gin"
    assert "gin-gonic/gin" in out["files"]["go.mod"]
    assert "c.JSON" in out["files"]["cmd/server/main.go"]


def test_scaffold_backend_invalid_framework():
    out = scaffold_backend("svc", framework="rails")
    assert "error" in out
    assert "available" in out


def test_scaffold_backend_invalid_name():
    out = scaffold_backend("bad name!", framework="fastapi")
    assert "error" in out


def test_scaffold_fullstack():
    out = scaffold_fullstack("shop", backend="fastapi", frontend="react")
    assert "backend/app/main.py" in out["files"]
    assert "frontend/src/App.jsx" in out["files"]
    assert "frontend/package.json" in out["files"]
    assert "README.md" in out["files"]


def test_adr_generation():
    md = adr("Use PeaLang", "We need a single language.", "Adopt PeaLang.",
             "Fewer runtimes to maintain.", adr_number=42)
    assert "ADR-0042" in md
    assert "Use PeaLang" in md
    assert "Context" in md and "Decision" in md and "Consequences" in md


def test_adr_index():
    md = adr_index([
        {"number": "0001", "title": "Use PeaLang", "status": "accepted"},
        {"number": "0002", "title": "PostgreSQL", "status": "proposed"},
    ])
    assert "ADR-0001" in md
    assert "ADR-0002" in md
    assert "Architecture Decision Records" in md


def test_service_contract():
    c = service_contract("orders", routes=[
        {"method": "get", "path": "/orders", "owner": "team-a"},
        {"method": "post", "path": "/orders", "name": "create_order", "auth": "jwt"},
    ])
    assert c["service"] == "orders"
    assert c["endpoint_count"] == 2
    assert c["endpoints"][0]["method"] == "GET"
    assert c["endpoints"][1]["auth"] == "jwt"


def test_service_contract_to_openapi():
    c = service_contract("orders", routes=[
        {"method": "get", "path": "/orders", "owner": "team-a"},
        {"method": "post", "path": "/orders", "name": "create_order", "auth": "jwt"},
    ], version="2.20.0")
    spec = service_contract_to_openapi(c)
    assert spec["openapi"] == "3.0.3"
    assert spec["info"]["title"] == "orders API"
    assert spec["info"]["version"] == "2.20.0"
    assert spec["paths"]["/orders"]["get"]["operationId"] == "orders"
    assert spec["paths"]["/orders"]["post"]["operationId"] == "create_order"
    assert spec["paths"]["/orders"]["get"]["x-owner"] == "team-a"
    assert spec["paths"]["/orders"]["post"]["security"] == [{"bearerAuth": []}]
    assert spec["components"]["securitySchemes"]["bearerAuth"]["scheme"] == "bearer"


def test_service_contract_to_openapi_overrides_title_and_no_bearer():
    c = service_contract("health", routes=[{"method": "get", "path": "/health"}])
    spec = service_contract_to_openapi(c, title="Health API", version="1.2.3")
    assert spec["info"]["title"] == "Health API"
    assert spec["info"]["version"] == "1.2.3"
    assert "components" not in spec


def test_openapi_json_round_trip():
    import json
    c = service_contract("orders", routes=[{"method": "get", "path": "/orders"}])
    raw = openapi_json(c)
    spec = json.loads(raw)
    assert spec["openapi"] == "3.0.3"
    assert spec["paths"]["/orders"]["get"]["responses"]["200"]["description"] == "Success"


def test_service_contract_to_openapi_invalid():
    assert "error" in service_contract_to_openapi("nope")


def test_layered_architecture_check_good():
    src = "// layer: service\nlet x = 1\n"
    out = layered_architecture_check(src)
    assert out["ok"]
    assert out["findings"] == []


def test_layered_architecture_check_sql_in_ui():
    src = "// layer: ui\nlet q = \"SELECT * FROM users\"\n"
    out = layered_architecture_check(src)
    assert any("SQL" in f["message"] for f in out["findings"])


def test_layered_architecture_check_network_in_data():
    src = "// layer: data\nlet r = http_get(\"https://x\")\n"
    out = layered_architecture_check(src)
    assert any("network" in f["message"].lower() for f in out["findings"])


def test_write_backend_scaffold(tmp_path):
    target = tmp_path / "svc"
    out = write_scaffold("svc", kind="backend", target_dir=str(target), port=8080)
    assert "error" not in out
    assert out["file_count"] == len(out["files"])
    assert (target / "app" / "main.py").exists()
    assert (target / "requirements.txt").exists()
    assert "8080" in (target / "Dockerfile").read_text(encoding="utf-8")


def test_write_fullstack_scaffold(tmp_path):
    target = tmp_path / "shop"
    out = write_scaffold("shop", kind="fullstack", target_dir=str(target))
    assert "error" not in out
    assert (target / "backend" / "app" / "main.py").exists()
    assert (target / "frontend" / "src" / "App.jsx").exists()
    assert (target / "frontend" / "package.json").exists()


def test_write_scaffold_invalid_kind(tmp_path):
    out = write_scaffold("svc", kind="frontend", target_dir=str(tmp_path / "svc"))
    assert "error" in out
    assert "available" in out


def test_write_scaffold_invalid_framework(tmp_path):
    out = write_scaffold("svc", kind="backend", target_dir=str(tmp_path / "svc2"), framework="rails")
    assert "error" in out


def test_build_frameworks_namespace_includes_write_scaffold():
    ns = build_frameworks_namespace()
    assert "write_scaffold" in ns


def test_cli_scaffold_backend(tmp_path):
    target = tmp_path / "clisvc"
    r = subprocess.run(
        [sys.executable, "-m", "pealang.cli", "scaffold", "fastapi", str(target), "--port", "8081"],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert r.returncode == 0, r.stderr
    info = json.loads(r.stdout)
    assert info["file_count"] >= 5
    assert (target / "app" / "main.py").exists()


def test_cli_scaffold_fullstack(tmp_path):
    target = tmp_path / "clishop"
    r = subprocess.run(
        [sys.executable, "-m", "pealang.cli", "scaffold", "fullstack", str(target)],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert r.returncode == 0, r.stderr
    info = json.loads(r.stdout)
    assert (target / "backend" / "app" / "main.py").exists()
    assert (target / "frontend" / "src" / "App.jsx").exists()


def test_build_frameworks_namespace():
    ns = build_frameworks_namespace()
    for key in ("scaffold_backend", "scaffold_fullstack", "write_scaffold",
                "adr", "adr_index", "adr_transition", "adr_filter",
                "service_contract", "service_contract_to_openapi", "openapi_json",
                "layered_architecture_check"):
        assert key in ns


def test_scaffold_backend_django():
    out = scaffold_backend("orders", framework="django", port=8080)
    assert out["framework"] == "django"
    assert "manage.py" in out["files"]
    assert "config/settings.py" in out["files"]
    assert "services/views.py" in out["files"]
    assert "services/test_health.py" in out["files"]
    assert "JsonResponse" in out["files"]["services/views.py"]
    assert "health" in out["files"]["config/urls.py"]


def test_scaffold_fullstack_nextjs():
    out = scaffold_fullstack("shop", backend="fastapi", frontend="nextjs")
    assert out["frontend"] == "nextjs"
    assert "frontend/pages/index.js" in out["files"]
    assert "frontend/package.json" in out["files"]
    assert "next" in out["files"]["frontend/package.json"]


def test_scaffold_fullstack_bad_frontend():
    out = scaffold_fullstack("shop", backend="fastapi", frontend="angular")
    assert "frontend/README.md" in out["files"]
    assert "angular" in out["files"]["frontend/README.md"]


def test_service_contract_with_schemas():
    c = service_contract("orders", routes=[
        {"method": "post", "path": "/orders",
         "request_body": {"type": "object", "required": ["item"],
                          "properties": {"item": {"type": "string"}}},
         "response_schema": {"type": "object",
                             "properties": {"id": {"type": "integer"}}}},
    ])
    assert c["endpoints"][0]["request_body"]["required"] == ["item"]
    assert c["endpoints"][0]["response_schema"]["type"] == "object"


def test_openapi_with_request_response_schemas():
    c = service_contract("orders", routes=[
        {"method": "post", "path": "/orders",
         "request_body": {"type": "object",
                          "properties": {"item": {"type": "string"}}},
         "response_schema": {"type": "object",
                             "properties": {"id": {"type": "integer"}}}},
    ])
    spec = service_contract_to_openapi(c)
    op = spec["paths"]["/orders"]["post"]
    body_schema = op["requestBody"]["content"]["application/json"]["schema"]
    assert body_schema["type"] == "object"
    resp_schema = op["responses"]["200"]["content"]["application/json"]["schema"]
    assert resp_schema["type"] == "object"


def test_adr_transition_valid():
    rec = {"number": "0001", "title": "Use PeaLang", "status": "proposed", "owner": "team-a"}
    updated = adr_transition(rec, "accepted")
    assert updated["status"] == "accepted"
    assert rec["status"] == "proposed"  # original unchanged


def test_adr_transition_invalid():
    rec = {"number": "0001", "status": "proposed"}
    out = adr_transition(rec, "maybe")
    assert "error" in out
    assert "allowed" in out


def test_adr_filter():
    recs = [
        {"number": "1", "status": "accepted", "owner": "a"},
        {"number": "2", "status": "proposed", "owner": "a"},
        {"number": "3", "status": "accepted", "owner": "b"},
    ]
    assert [r["number"] for r in adr_filter(recs, status="accepted")] == ["1", "3"]
    assert [r["number"] for r in adr_filter(recs, owner="a")] == ["1", "2"]
    assert [r["number"] for r in adr_filter(recs, status="accepted", owner="b")] == ["3"]
