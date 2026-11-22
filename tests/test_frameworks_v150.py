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
    scaffold_k8s,
    scaffold_helm_chart,
    scaffold_terraform,
    scaffold_cloudbuild,
    scaffold_registry_config,
    scaffold_wasm_production,
    scaffold_edge_worker,
    _get_multistage_dockerfile,
    _get_k8s_deployment,
    _get_k8s_service,
    _get_k8s_hpa,
    _get_istio_configs,
    _get_otel_config,
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
    spec = service_contract_to_openapi(c, title="Health API", version="1.2.3", include_error_responses=False)
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
    assert spec["paths"]["/orders"]["get"]["responses"]["400"]["description"] == "Bad Request"
    assert spec["components"]["schemas"]["Error"]["type"] == "object"


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


def test_adr_transition_superseded_by():
    rec = {"number": "0001", "title": "Old", "status": "accepted"}
    updated = adr_transition(rec, "superseded", superseded_by="0002")
    assert updated["status"] == "superseded"
    assert updated["superseded_by"] == "0002"
    assert rec.get("superseded_by") is None


def test_adr_index_with_links():
    md = adr_index([
        {"number": "0001", "title": "Use PeaLang", "status": "superseded", "owner": "arch", "superseded_by": "0002"},
        {"number": "0002", "title": "Use PeaLang v2", "status": "accepted", "supersedes": "0001"},
    ])
    assert "owner: arch" in md
    assert "superseded by ADR-0002" in md
    assert "supersedes ADR-0001" in md


def test_openapi_contact_license_and_errors():
    c = service_contract("orders", routes=[{"method": "get", "path": "/orders"}], version="2.20.0")
    c["contact"] = {"name": "API Team", "email": "api@example.com"}
    c["license"] = {"name": "MIT"}
    c["description"] = "Orders service API"
    spec = service_contract_to_openapi(c)
    assert spec["info"]["contact"]["email"] == "api@example.com"
    assert spec["info"]["license"]["name"] == "MIT"
    assert spec["info"]["description"] == "Orders service API"
    assert "Error" in spec["components"]["schemas"]
    responses = spec["paths"]["/orders"]["get"]["responses"]
    for code in ("400", "401", "403", "404", "422", "429", "500"):
        assert code in responses
        assert responses[code]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/Error"


def test_openapi_disable_error_responses():
    c = service_contract("orders", routes=[{"method": "get", "path": "/orders"}])
    spec = service_contract_to_openapi(c, include_error_responses=False)
    responses = spec["paths"]["/orders"]["get"]["responses"]
    assert "400" not in responses
    assert "components" not in spec or "Error" not in spec.get("components", {}).get("schemas", {})


# --- Phase 3: Platform & Deployment scaffolding tests ---

def test_scaffold_k8s_basic():
    out = scaffold_k8s("orders", framework="fastapi", port=8080, replicas=3)
    assert out["name"] == "orders"
    assert "Dockerfile" in out["files"]
    assert "Dockerfile.dev" in out["files"]
    assert "k8s/orders-deployment.yaml" in out["files"]
    assert "k8s/orders-service.yaml" in out["files"]
    assert "k8s/kustomization.yaml" in out["files"]
    assert "replicas: 3" in out["files"]["k8s/orders-deployment.yaml"]
    assert "containerPort: 8080" in out["files"]["k8s/orders-deployment.yaml"]
    assert "FROM gcr.io/distroless/python3-debian12:nonroot" in out["files"]["Dockerfile"]


def test_scaffold_k8s_with_hpa_and_ingress():
    out = scaffold_k8s("orders", framework="fastapi", port=8080, replicas=3,
                       include_hpa=True, include_ingress=True, ingress_host="orders.example.com")
    assert "k8s/orders-hpa.yaml" in out["files"]
    assert "k8s/orders-ingress.yaml" in out["files"]
    assert "orders.example.com" in out["files"]["k8s/orders-ingress.yaml"]
    assert "minReplicas: 3" in out["files"]["k8s/orders-hpa.yaml"]
    assert "maxReplicas: 20" in out["files"]["k8s/orders-hpa.yaml"]


def test_scaffold_k8s_with_otel_and_istio():
    out = scaffold_k8s("orders", framework="fastapi", port=8080,
                       include_otel=True, include_istio=True)
    assert "otel/otel-config.yaml" in out["files"]
    assert "otel/instrumentation.py" in out["files"]
    assert "istio/orders-virtualservice.yaml" in out["files"]
    assert "istio/orders-destinationrule.yaml" in out["files"]
    assert "istio/orders-peerauth.yaml" in out["files"]
    assert "istio/orders-authorization.yaml" in out["files"]
    assert "mtls:" in out["files"]["istio/orders-peerauth.yaml"]


def test_scaffold_helm_chart():
    out = scaffold_helm_chart("orders", framework="fastapi", port=8080)
    assert out["chart_name"] == "orders"
    assert "helm/orders/Chart.yaml" in out["files"]
    assert "helm/orders/values.yaml" in out["files"]
    assert "helm/orders/templates/deployment.yaml" in out["files"]
    assert "helm/orders/templates/service.yaml" in out["files"]
    assert "helm/orders/templates/hpa.yaml" in out["files"]
    assert "helm/orders/templates/ingress.yaml" in out["files"]
    assert "helm/orders/templates/_helpers.tpl" in out["files"]
    assert 'name: orders' in out["files"]["helm/orders/Chart.yaml"]


def test_scaffold_terraform_aws():
    out = scaffold_terraform("orders", cloud="aws", region="us-east-1")
    assert "terraform/main.tf" in out["files"]
    assert "terraform/variables.tf" in out["files"]
    assert "terraform/outputs.tf" in out["files"]
    assert "aws_ecr_repository" in out["files"]["terraform/main.tf"]
    assert "aws_ecs_cluster" in out["files"]["terraform/main.tf"]
    assert "aws_ecs_service" in out["files"]["terraform/main.tf"]
    assert "us-east-1" in out["files"]["terraform/main.tf"]


def test_scaffold_cloudbuild_gcp():
    out = scaffold_cloudbuild("orders", cloud="gcp", region="us-central1")
    assert "cloudbuild.yaml" in out["files"]
    assert "cloudbuild.yaml.prod" in out["files"]
    assert "gcr.io/cloud-builders/docker" in out["files"]["cloudbuild.yaml"]
    # Check for gcloud run deploy in the YAML (split across lines)
    content = out["files"]["cloudbuild.yaml"]
    assert "gcloud" in content
    assert "run" in content
    assert "deploy" in content


def test_scaffold_cloudbuild_aws():
    out = scaffold_cloudbuild("orders", cloud="aws", region="us-east-1")
    assert "buildspec.yml" in out["files"]
    assert "ecr get-login-password" in out["files"]["buildspec.yml"]


def test_scaffold_registry_config():
    out = scaffold_registry_config("orders", registry_type="oci")
    assert ".docker/config.json" in out["files"]
    assert ".npmrc" in out["files"]
    assert "pea-publish.yml" in out["files"]
    assert "ghcr.io" in out["files"][".docker/config.json"]
    assert "registry.pea.dev" in out["files"][".npmrc"]


def test_scaffold_wasm_production():
    out = scaffold_wasm_production("orders", target="wasm32-wasip1")
    assert "wasm-build.yml" in out["files"]
    assert "Dockerfile.wasm" in out["files"]
    assert "wasm-component.wit" in out["files"]
    assert "wasm32-wasip1" in out["files"]["wasm-build.yml"]
    assert "wasm-opt" in out["files"]["wasm-build.yml"]


def test_scaffold_edge_worker_cloudflare():
    out = scaffold_edge_worker("orders", platform="cloudflare")
    assert "wrangler.toml" in out["files"]
    assert "worker.py" in out["files"]
    assert "package.json" in out["files"]
    assert "orders" in out["files"]["wrangler.toml"]


def test_scaffold_edge_worker_vercel():
    out = scaffold_edge_worker("orders", platform="vercel")
    assert "vercel.json" in out["files"]
    assert "api/index.py" in out["files"]
    assert "python3.12" in out["files"]["vercel.json"]


def test_scaffold_edge_worker_aws():
    out = scaffold_edge_worker("orders", platform="aws")
    assert "template.yaml" in out["files"]
    assert "lambda_function.py" in out["files"]
    assert "AWS::Serverless::Function" in out["files"]["template.yaml"]


def test_multistage_dockerfile_distroless():
    df = _get_multistage_dockerfile("fastapi", 8000, use_distroless=True)
    assert "FROM gcr.io/distroless/python3-debian12:nonroot" in df
    assert "FROM python:3.12-slim AS builder" in df


def test_multistage_dockerfile_dev():
    df = _get_multistage_dockerfile("fastapi", 8000, use_distroless=False)
    assert "FROM python:3.12-slim" in df
    assert "USER 10001:10001" in df
    assert "gcr.io/distroless" not in df


def test_k8s_deployment_yaml():
    yaml = _get_k8s_deployment("orders", "fastapi", 8000, 3)
    assert "replicas: 3" in yaml
    assert "containerPort: 8000" in yaml
    assert "livenessProbe:" in yaml
    assert "readinessProbe:" in yaml
    assert "/health" in yaml


def test_k8s_service_yaml():
    yaml = _get_k8s_service("orders", 8000)
    assert "type: ClusterIP" in yaml
    assert "targetPort: 8000" in yaml


def test_k8s_hpa_yaml():
    yaml = _get_k8s_hpa("orders", min_replicas=3, max_replicas=20)
    assert "minReplicas: 3" in yaml
    assert "maxReplicas: 20" in yaml
    assert "averageUtilization: 70" in yaml


def test_istio_configs():
    configs = _get_istio_configs("orders", "default", 8000)
    assert "orders-virtualservice.yaml" in configs
    assert "orders-destinationrule.yaml" in configs
    assert "orders-peerauth.yaml" in configs
    assert "orders-authorization.yaml" in configs
    assert "mtls:" in configs["orders-peerauth.yaml"]
    assert "STRICT" in configs["orders-peerauth.yaml"]
    assert "circuitBreaker:" in configs["orders-destinationrule.yaml"]


def test_otel_configs():
    configs = _get_otel_config("orders", "http://jaeger:4318/v1/traces")
    assert "otel-config.yaml" in configs
    assert "Dockerfile.otel" in configs
    assert "instrumentation.py" in configs
    assert "FastAPIInstrumentor" in configs["instrumentation.py"]


def test_scaffold_k8s_invalid_name():
    out = scaffold_k8s("bad name!", framework="fastapi")
    assert "error" in out
