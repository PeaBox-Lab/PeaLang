"""Regression coverage for frameworks & architecture toolkit."""

from pealang.frameworks import (
    build_frameworks_namespace,
    scaffold_backend,
    scaffold_fullstack,
    adr,
    adr_index,
    service_contract,
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


def test_build_frameworks_namespace():
    ns = build_frameworks_namespace()
    for key in ("scaffold_backend", "scaffold_fullstack", "adr", "adr_index",
                "service_contract", "layered_architecture_check"):
        assert key in ns
