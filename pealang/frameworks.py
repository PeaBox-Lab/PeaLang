"""Developer frameworks & architecture toolkit for PeaLang (v2.14.0).

Generates ready-to-use project skeletons and architecture documentation for
web, full-stack, backend, and solution-architect workflows. These are
generators (they return file-content dictionaries / markdown strings), not
runtime frameworks — generated projects remain ordinary FastAPI / Flask /
Express / Gin codebases that you build and run independently.
"""

from __future__ import annotations

import json
import re
import time
import os
import base64
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Backend service scaffolding
# ---------------------------------------------------------------------------

_BACKENDS = {
    "fastapi": {
        "language": "python",
        "framework": "fastapi",
        "entrypoint": "app/main.py",
    },
    "flask": {
        "language": "python",
        "framework": "flask",
        "entrypoint": "app/main.py",
    },
    "express": {
        "language": "node",
        "framework": "express",
        "entrypoint": "src/index.js",
    },
    "gin": {
        "language": "go",
        "framework": "gin",
        "entrypoint": "cmd/server/main.go",
    },
    "django": {
        "language": "python",
        "framework": "django",
        "entrypoint": "config/settings.py",
    },
}


def scaffold_backend(name: str, framework: str = "fastapi", port: int = 8000) -> dict[str, Any]:
    """Return a {path: content} file map for a backend service skeleton."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,63}", name):
        return {"error": f"Invalid service name: {name!r}"}
    framework = framework.lower()
    if framework not in _BACKENDS:
        return {"error": f"Unsupported framework {framework!r}", "available": sorted(_BACKENDS)}

    slug = name.replace("-", "_")
    b = _BACKENDS[framework]
    files: dict[str, str] = {}

    if framework == "fastapi":
        files["requirements.txt"] = "fastapi>=0.104\\nuvicorn[standard]>=0.24\\npytest>=7.4\\n"
        files["app/__init__.py"] = ""
        files["app/main.py"] = (
            "from fastapi import FastAPI\n\n"
            f"app = FastAPI(title=\"{name}\")\n\n"
            "@app.get(\"/health\")\n"
            "def health():\n"
            "    return {\"status\": \"ok\", \"service\": \"" + name + "\"}\n"
        )
        files["tests/test_health.py"] = (
            "import os\nimport sys\n"
            "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
            "from fastapi.testclient import TestClient\n"
            "from app.main import app\n\n"
            "client = TestClient(app)\n\n"
            "def test_health():\n"
            "    assert client.get(\"/health\").json()[\"status\"] == \"ok\"\n"
        )
        files["Dockerfile"] = (
            "FROM python:3.12-slim\nWORKDIR /srv\nCOPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\n"
            f"CMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"{port}\"]\n"
        )
    elif framework == "flask":
        files["requirements.txt"] = "flask>=3.0\\ngunicorn>=21\\npytest>=7.4\\n"
        files["app/__init__.py"] = ""
        files["app/main.py"] = (
            "from flask import Flask, jsonify\n\n"
            f"app = Flask(__name__)\n\n"
            "@app.get(\"/health\")\n"
            "def health():\n"
            f"    return jsonify(status=\"ok\", service=\"{name}\")\n"
        )
        files["tests/test_health.py"] = (
            "import os\nimport sys\n"
            "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
            "from app.main import app\n\n"
            "def test_health():\n"
            "    assert app.test_client().get(\"/health\").get_json()[\"status\"] == \"ok\"\n"
        )
        files["Dockerfile"] = (
            "FROM python:3.12-slim\nWORKDIR /srv\nCOPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\n"
            f"CMD [\"gunicorn\", \"-b\", \"0.0.0.0:{port}\", \"app.main:app\"]\n"
        )
    elif framework == "express":
        files["package.json"] = json.dumps({
            "name": name, "version": "1.0.0", "private": True,
            "scripts": {"start": "node src/index.js", "test": "node --test"},
            "dependencies": {"express": "^4.19.0"},
        }, indent=2) + "\n"
        files["src/index.js"] = (
            "const express = require('express');\n"
            f"const app = express();\n"
            "app.get('/health', (req, res) => res.json({ status: 'ok', service: '" + name + "' }));\n"
            f"const port = process.env.PORT || {port};\n"
            "app.listen(port, () => console.log(`listening on ${port}`));\n"
        )
        files["Dockerfile"] = (
            "FROM node:20-slim\nWORKDIR /srv\nCOPY package*.json ./\nRUN npm install --omit=dev\nCOPY . .\n"
            f"CMD [\"node\", \"src/index.js\"]\n"
        )
    elif framework == "gin":
        files["go.mod"] = f"module {slug}\n\ngo 1.21\n\nrequire github.com/gin-gonic/gin v1.9.1\n"
        files["cmd/server/main.go"] = (
            "package main\n\n"
            "import (\n    \"net/http\"\n    \"github.com/gin-gonic/gin\"\n)\n\n"
            "func main() {\n"
            "    r := gin.Default()\n"
            "    r.GET(\"/health\", func(c *gin.Context) {\n"
            f"        c.JSON(http.StatusOK, gin.H{{\"status\": \"ok\", \"service\": \"{name}\"}})\n"
            "    })\n"
            f"    r.Run(\":{port}\")\n"
            "}\n"
        )
    elif framework == "django":
        files["requirements.txt"] = "django>=5.0\\ngunicorn>=21\\npytest>=7.4\\npytest-django>=4.8\\n"
        files["manage.py"] = (
            "#!/usr/bin/env python\n"
            "import os\nimport sys\n"
            "if __name__ == \"__main__\":\n"
            "    os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", \"config.settings\")\n"
            "    from django.core.management import execute_from_command_line\n"
            "    execute_from_command_line(sys.argv)\n"
        )
        files["config/settings.py"] = (
            "SECRET_KEY = \"change-me-in-production\"\n"
            "DEBUG = True\n"
            "ALLOWED_HOSTS = [\"*\"]\n"
            "ROOT_URLCONF = \"config.urls\"\n"
            "INSTALLED_APPS = [\"django.contrib.contenttypes\", \"django.contrib.auth\", \"services\"]\n"
            "DATABASES = {}\n"
            "MIDDLEWARE = []\n"
            "TEMPLATES = []\n"
            "TIME_ZONE = \"UTC\"\n"
            "DEFAULT_AUTO_FIELD = \"django.db.models.BigAutoField\"\n"
        )
        files["config/wsgi.py"] = (
            "import os\n"
            "from django.core.wsgi import get_wsgi_application\n\n"
            "os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", \"config.settings\")\n"
            "application = get_wsgi_application()\n"
        )
        files["config/urls.py"] = (
            "from django.urls import path\n"
            "from services.views import health\n\n"
            "urlpatterns = [path(\"health\", health)]\n"
        )
        files["services/views.py"] = (
            "from django.http import JsonResponse\n\n"
            f"def health(request):\n"
            f"    return JsonResponse({{\"status\": \"ok\", \"service\": \"{name}\"}})\n"
        )
        files["services/apps.py"] = (
            "from django.apps import AppConfig\n\n"
            "class ServicesConfig(AppConfig):\n"
            "    name = \"services\"\n"
        )
        files["services/test_health.py"] = (
            "from django.test import Client\n\n"
            "def test_health():\n"
            "    c = Client()\n"
            "    r = c.get(\"/health\")\n"
            "    assert r.status_code == 200\n"
            "    assert r.json()[\"status\"] == \"ok\"\n"
        )
        files["Dockerfile"] = (
            "FROM python:3.12-slim\nWORKDIR /srv\nCOPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\n"
            f"CMD [\"gunicorn\", \"--bind\", \"0.0.0.0:{port}\", \"config.wsgi:application\"]\n"
        )

    # Starter API contract + OpenAPI spec (contract-first workflow)
    _contract = service_contract(name, routes=[
        {"method": "get", "path": "/health", "name": "health", "owner": "platform",
         "response_schema": {"type": "object", "properties": {"status": {"type": "string"}, "service": {"type": "string"}}}},
    ], version="1.0.0")
    files["service_contract.json"] = json.dumps(_contract, indent=2) + "\n"
    files["openapi.json"] = openapi_json(_contract, title=f"{name} API", version="1.0.0") + "\n"

    files["README.md"] = (
        f"# {name}\n\n"
        f"Backend service scaffolded by PeaLang frameworks toolkit.\n\n"
        f"Framework: {b['framework']} ({b['language']})\n"
        f"Entrypoint: `{b['entrypoint']}`\nPort: {port}\n\n"
        "Includes starter `service_contract.json` and `openapi.json`.\n\n"
        "```bash\n"
        + ("pip install -r requirements.txt && uvicorn app.main:app --reload\n" if framework == "fastapi"
           else "pip install -r requirements.txt && gunicorn -b 0.0.0.0:8000 app.main:app\n" if framework == "flask"
           else "npm install && npm start\n" if framework == "express"
           else "go run ./cmd/server\n" if framework == "gin"
           else "pip install -r requirements.txt && python manage.py runserver 0.0.0.0:{port}\n".format(port=port))
        + "```\n"
    )
    return {"name": name, "framework": framework, "language": b["language"],
            "port": port, "entrypoint": b["entrypoint"], "files": files}


def scaffold_fullstack(name: str, backend: str = "fastapi",
                       frontend: str = "react", port: int = 8000) -> dict[str, Any]:
    """Generate a combined backend + frontend monorepo skeleton."""
    svc = scaffold_backend(name, framework=backend, port=port)
    if "error" in svc:
        return svc
    files: dict[str, str] = {f"backend/{k}": v for k, v in svc["files"].items()}

    if frontend.lower() == "react":
        files["frontend/package.json"] = json.dumps({
            "name": f"{name}-ui", "version": "1.0.0", "private": True,
            "scripts": {"dev": "vite", "build": "vite build"},
            "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"},
            "devDependencies": {"vite": "^5.0.0", "@vitejs/plugin-react": "^4.2.0"},
        }, indent=2) + "\n"
        files["frontend/src/App.jsx"] = (
            "import { useEffect, useState } from 'react';\n\n"
            "export default function App() {\n"
            "  const [health, setHealth] = useState(null);\n"
            "  useEffect(() => {\n"
            f"    fetch('http://localhost:{port}/health').then(r => r.json()).then(setHealth).catch(() => setHealth({{error:'backend unreachable'}}));\n"
            "  }, []);\n"
            "  return <pre>{JSON.stringify(health, null, 2)}</pre>;\n"
            "}\n"
        )
        files["frontend/index.html"] = (
            "<!doctype html><html><body><div id=\"root\"></div>"
            "<script type=\"module\" src=\"/src/main.jsx\"></script></body></html>\n"
        )
        files["frontend/src/main.jsx"] = (
            "import React from 'react';\nimport { createRoot } from 'react-dom/client';\nimport App from './App.jsx';\n"
            "createRoot(document.getElementById('root')).render(<App />);\n"
        )
    elif frontend.lower() == "nextjs":
        files["frontend/package.json"] = json.dumps({
            "name": f"{name}-ui", "version": "1.0.0", "private": True,
            "scripts": {"dev": "next dev", "build": "next build", "start": "next start"},
            "dependencies": {"next": "^14.2.0", "react": "^18.2.0", "react-dom": "^18.2.0"},
        }, indent=2) + "\n"
        files["frontend/pages/index.js"] = (
            "import { useEffect, useState } from 'react';\n\n"
            "export default function Home() {\n"
            "  const [health, setHealth] = useState(null);\n"
            "  useEffect(() => {\n"
            f"    fetch('http://localhost:{port}/health').then(r => r.json()).then(setHealth).catch(() => setHealth({{error:'backend unreachable'}}));\n"
            "  }, []);\n"
            "  return <pre>{JSON.stringify(health, null, 2)}</pre>;\n"
            "}\n"
        )
        files["frontend/next.config.js"] = "module.exports = { reactStrictMode: true };\n"
    else:
        files["frontend/README.md"] = f"# {name} frontend\nFramework '{frontend}' not scaffolded; choose 'react' or 'nextjs'.\n"

    files["README.md"] = (
        f"# {name}\n\n"
        f"Full-stack PeaLang task skeleton: `{backend}` backend + `{frontend}` frontend.\n\n"
        f"- Backend under `backend/` (port {port}, with `service_contract.json` and `openapi.json`)\n- Frontend under `frontend/`\n\n"
        "```bash\ncd backend && pip install -r requirements.txt && uvicorn app.main:app --reload\n"
        "cd frontend && npm install && npm run dev\n```\n"
    )
    return {"name": name, "backend": backend, "frontend": frontend,
            "port": port, "files": files,
            "layout": ["backend/" + k for k in svc["files"]] + list(files)}


def write_scaffold(name: str, kind: str = "backend", target_dir: str = ".",
                   framework: str = "fastapi", port: int = 8000,
                   frontend: str = "react") -> dict[str, Any]:
    """Write a generated backend or full-stack skeleton into target_dir.

    Refuses to write outside the resolved target directory: any generated path
    containing '..' after normalisation aborts the write before anything is
    written, so accidents cannot scatter files across the filesystem.
    """
    kind = kind.lower()
    if kind == "backend":
        gen = scaffold_backend(name, framework=framework, port=port)
    elif kind == "fullstack":
        gen = scaffold_fullstack(name, backend=framework, frontend=frontend, port=port)
    else:
        return {"error": f"Unknown kind {kind!r}", "available": ["backend", "fullstack"]}
    if "error" in gen:
        return gen

    root = Path(target_dir).resolve()
    for rel in gen["files"]:
        parts = Path(rel).parts
        if ".." in parts:
            return {"error": f"Refusing to write outside target: {rel!r}"}

    root.mkdir(parents=True, exist_ok=True)
    written = []
    for rel, content in gen["files"].items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        written.append(rel)
    return {"root": str(root), "name": gen.get("name"), "kind": kind,
            "files": sorted(written), "file_count": len(written)}


# ---------------------------------------------------------------------------
# Platform & Deployment scaffolding (Phase 3)
# ---------------------------------------------------------------------------

def _get_multistage_dockerfile(framework: str, port: int, use_distroless: bool = False) -> str:
    """Generate multi-stage Dockerfile for production."""
    if framework == "fastapi":
        if use_distroless:
            return f'''# Build stage
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM gcr.io/distroless/python3-debian12:nonroot
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
EXPOSE {port}
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{port}"]
'''
        else:
            return f'''# Build stage
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.12-slim
WORKDIR /app
RUN groupadd --gid 10001 appuser && useradd --uid 10001 --gid 10001 --create-home appuser
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .
ENV PATH=/home/appuser/.local/bin:$PATH
USER 10001:10001
EXPOSE {port}
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{port}"]
'''
    elif framework == "flask":
        if use_distroless:
            return f'''# Build stage
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM gcr.io/distroless/python3-debian12:nonroot
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
EXPOSE {port}
CMD ["gunicorn", "-b", "0.0.0.0:{port}", "app.main:app"]
'''
        else:
            return f'''# Build stage
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.12-slim
WORKDIR /app
RUN groupadd --gid 10001 appuser && useradd --uid 10001 --gid 10001 --create-home appuser
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .
ENV PATH=/home/appuser/.local/bin:$PATH
USER 10001:10001
EXPOSE {port}
CMD ["gunicorn", "-b", "0.0.0.0:{port}", "app.main:app"]
'''
    else:
        return f'''# Generic single-stage (extend for other frameworks)
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE {port}
CMD ["python", "main.py"]
'''


def _get_k8s_deployment(name: str, framework: str, port: int, replicas: int = 3,
                        image: str | None = None, namespace: str = "default",
                        resources: dict | None = None) -> str:
    """Generate Kubernetes Deployment YAML."""
    img = image or f"{name}:latest"
    res = resources or {"requests": {"cpu": "100m", "memory": "128Mi"}, "limits": {"cpu": "500m", "memory": "512Mi"}}
    return f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {namespace}
  labels:
    app: {name}
    framework: {framework}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
        framework: {framework}
    spec:
      containers:
      - name: {name}
        image: {img}
        ports:
        - containerPort: {port}
        resources:
          requests:
            cpu: "{res['requests']['cpu']}"
            memory: "{res['requests']['memory']}"
          limits:
            cpu: "{res['limits']['cpu']}"
            memory: "{res['limits']['memory']}"
        livenessProbe:
          httpGet:
            path: /health
            port: {port}
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: {port}
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: PORT
          value: "{port}"
'''


def _get_k8s_service(name: str, port: int, service_type: str = "ClusterIP", namespace: str = "default") -> str:
    """Generate Kubernetes Service YAML."""
    return f'''apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: {namespace}
  labels:
    app: {name}
spec:
  type: {service_type}
  ports:
  - port: 80
    targetPort: {port}
    protocol: TCP
    name: http
  selector:
    app: {name}
'''


def _get_k8s_hpa(name: str, min_replicas: int = 3, max_replicas: int = 20,
                 cpu_target: int = 70, namespace: str = "default") -> str:
    """Generate Kubernetes HorizontalPodAutoscaler YAML."""
    return f'''apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {name}-hpa
  namespace: {namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {name}
  minReplicas: {min_replicas}
  maxReplicas: {max_replicas}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {cpu_target}
'''


def _get_k8s_ingress(name: str, host: str, port: int = 80, namespace: str = "default",
                     tls_secret: str | None = None) -> str:
    """Generate Kubernetes Ingress YAML."""
    tls_section = f'''
  tls:
  - hosts:
    - {host}
    secretName: {tls_secret}
''' if tls_secret else ''
    return f'''apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {name}-ingress
  namespace: {namespace}
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:{tls_section}
  rules:
  - host: {host}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {name}
            port:
              number: {port}
'''


def _get_otel_config(service_name: str, endpoint: str = "http://jaeger:4318/v1/traces",
                     metrics_endpoint: str = "http://prometheus:9090",
                     sample_rate: float = 1.0) -> dict[str, str]:
    """Generate OpenTelemetry configuration files."""
    return {
        "otel-config.yaml": f'''receivers:
  otlp:
    protocols:
      grpc:
      http:
exporters:
  otlp:
    endpoint: {endpoint}
    tls:
      insecure: true
  prometheus:
    endpoint: "{metrics_endpoint}"
  logging:
    loglevel: debug
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [otlp, logging]
    metrics:
      receivers: [otlp]
      exporters: [prometheus, logging]
''',
        "Dockerfile.otel": f'''# OpenTelemetry Collector sidecar
FROM otel/opentelemetry-collector-contrib:latest
COPY otel-config.yaml /etc/otel/config.yaml
CMD ["--config=/etc/otel/config.yaml"]
''',
        "instrumentation.py": f'''# Add to your app for auto-instrumentation
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="{endpoint.replace('http://', '').replace('v1/traces', '')}"))
)

# Auto-instrument FastAPI
def instrument_app(app):
    FastAPIInstrumentor.instrument_app(app)
    RequestsInstrumentor().instrument()
    return app
''',
    }


def _get_istio_configs(name: str, namespace: str = "default", port: int = 8000) -> dict[str, str]:
    """Generate Istio service mesh configurations."""
    return {
        f"{name}-virtualservice.yaml": f'''apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: {name}
  namespace: {namespace}
spec:
  hosts:
  - {name}
  http:
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: {name}.{namespace}.svc.cluster.local
        port:
          number: {port}
    retries:
      attempts: 3
      perTryTimeout: 2s
      retryOn: connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes
    timeout: 10s
''',
        f"{name}-destinationrule.yaml": f'''apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: {name}
  namespace: {namespace}
spec:
  host: {name}.{namespace}.svc.cluster.local
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        h2UpgradePolicy: UPGRADE
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
    circuitBreaker:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
    loadBalancer:
      simple: LEAST_REQUEST
''',
        f"{name}-peerauth.yaml": f'''apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: {name}
  namespace: {namespace}
spec:
  selector:
    matchLabels:
      app: {name}
  mtls:
    mode: STRICT
''',
        f"{name}-authorization.yaml": f'''apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: {name}
  namespace: {namespace}
spec:
  selector:
    matchLabels:
      app: {name}
  rules:
  - to:
    - operation:
        methods: ["GET", "POST"]
    - from:
    - source:
        principals: ["cluster.local/ns/{namespace}/sa/default"]
''',
    }


def scaffold_k8s(name: str, framework: str = "fastapi", port: int = 8000,
                 replicas: int = 3, namespace: str = "default",
                 image: str | None = None, resources: dict | None = None,
                 include_hpa: bool = True, include_ingress: bool = False,
                 ingress_host: str | None = None, ingress_tls_secret: str | None = None,
                 include_otel: bool = False, otel_endpoint: str = "http://jaeger:4318/v1/traces",
                 include_istio: bool = False) -> dict[str, Any]:
    """Generate complete Kubernetes manifests for a service."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,63}", name):
        return {"error": f"Invalid service name: {name!r}"}
    
    files = {}
    
    # Multi-stage Dockerfile
    files["Dockerfile"] = _get_multistage_dockerfile(framework, port, use_distroless=True)
    files["Dockerfile.dev"] = _get_multistage_dockerfile(framework, port, use_distroless=False)
    
    # K8s manifests
    files[f"k8s/{name}-deployment.yaml"] = _get_k8s_deployment(name, framework, port, replicas, image, namespace, resources)
    files[f"k8s/{name}-service.yaml"] = _get_k8s_service(name, port, "ClusterIP", namespace)
    
    if include_hpa:
        files[f"k8s/{name}-hpa.yaml"] = _get_k8s_hpa(name, namespace=namespace)
    
    if include_ingress and ingress_host:
        files[f"k8s/{name}-ingress.yaml"] = _get_k8s_ingress(name, ingress_host, port, namespace, ingress_tls_secret)
    
    if include_otel:
        otel_files = _get_otel_config(name, otel_endpoint)
        for fname, content in otel_files.items():
            files[f"otel/{fname}"] = content
    
    if include_istio:
        istio_files = _get_istio_configs(name, namespace, port)
        for fname, content in istio_files.items():
            files[f"istio/{fname}"] = content
    
    # Kustomize
    files["k8s/kustomization.yaml"] = f'''apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- {name}-deployment.yaml
- {name}-service.yaml
{'  - ' + name + '-hpa.yaml' if include_hpa else ''}
{'  - ' + name + '-ingress.yaml' if include_ingress else ''}
commonLabels:
  app: {name}
  framework: {framework}
'''
    
    # README
    files["README.md"] = f'''# {name} - Kubernetes Deployment

## Quick Start

```bash
# Build and push
docker build -t {image or name}:latest .
docker push {image or name}:latest

# Deploy
kubectl apply -k k8s/

# Or with Helm (if using)
helm upgrade --install {name} ./helm/
```

## Files

- `Dockerfile` - Multi-stage production build (distroless)
- `Dockerfile.dev` - Development build
- `k8s/` - Kubernetes manifests (Deployment, Service, HPA, Ingress)
- `k8s/kustomization.yaml` - Kustomize config
- `otel/` - OpenTelemetry Collector config (if enabled)
- `istio/` - Istio service mesh configs (if enabled)

## Configuration

- Service: `{name}`
- Framework: `{framework}`
- Port: `{port}`
- Replicas: `{replicas}`
- Namespace: `{namespace}`
- Image: `{image or name}:latest`
- Resources: {json.dumps(resources or {"requests": {"cpu": "100m", "memory": "128Mi"}, "limits": {"cpu": "500m", "memory": "512Mi"}})}
'''
    
    return {"name": name, "framework": framework, "port": port,
            "replicas": replicas, "namespace": namespace,
            "files": files, "file_count": len(files)}


def scaffold_helm_chart(name: str, framework: str = "fastapi", port: int = 8000,
                        image: str | None = None, namespace: str = "default") -> dict[str, Any]:
    """Generate a Helm chart for the service."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,63}", name):
        return {"error": f"Invalid service name: {name!r}"}
    
    files = {}
    chart_name = name.replace("-", "_")
    
    files[f"helm/{chart_name}/Chart.yaml"] = f'''apiVersion: v2
name: {chart_name}
description: Helm chart for {name} ({framework})
type: application
version: 0.1.0
appVersion: "1.0.0"
'''
    
    files[f"helm/{chart_name}/values.yaml"] = f'''# Default values for {chart_name}
replicaCount: 3

image:
  repository: {image or name}
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: ClusterIP
  port: 80
  targetPort: {port}

ingress:
  enabled: false
  className: "nginx"
  annotations: {{}}
  hosts:
    - host: {name}.example.com
      paths:
        - path: /
          pathType: Prefix
  tls: []

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70

nodeSelector: {{}}
tolerations: []
affinity: {{}}

# OpenTelemetry
otel:
  enabled: false
  endpoint: "http://jaeger:4318/v1/traces"

# Istio
istio:
  enabled: false
  mtls: strict
'''
    
    files[f"helm/{chart_name}/templates/deployment.yaml"] = f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "{chart_name}.fullname" . }}
  labels:
    {{- include "{chart_name}.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "{chart_name}.selectors" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "{chart_name}.selectors" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {port}
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
'''
    
    files[f"helm/{chart_name}/templates/service.yaml"] = f'''apiVersion: v1
kind: Service
metadata:
  name: {{ include "{chart_name}.fullname" . }}
  labels:
    {{- include "{chart_name}.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
      protocol: TCP
      name: http
  selector:
    {{- include "{chart_name}.selectors" . | nindent 4 }}
'''
    
    files[f"helm/{chart_name}/templates/hpa.yaml"] = f'''{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "{chart_name}.fullname" . }}
  labels:
    {{- include "{chart_name}.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "{chart_name}.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
{{- end }}
'''
    
    files[f"helm/{chart_name}/templates/ingress.yaml"] = f'''{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "{chart_name}.fullname" . }}
  labels:
    {{- include "{chart_name}.labels" . | nindent 4 }}
  annotations:
    {{- toYaml .Values.ingress.annotations | nindent 4 }}
spec:
  ingressClassName: {{ .Values.ingress.className }}
  {{- if .Values.ingress.tls }}
  tls:
    {{- toYaml .Values.ingress.tls | nindent 4 }}
  {{- end }}
  rules:
    {{- toYaml .Values.ingress.hosts | nindent 4 }}
{{- end }}
'''
    
    files[f"helm/{chart_name}/templates/_helpers.tpl"] = f'''{{- define "{chart_name}.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "{chart_name}.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "{chart_name}.labels" -}}
helm.sh/chart: {{ include "{chart_name}.chart" . }}
{{ include "{chart_name}.selectors" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "{chart_name}.selectors" -}}
app.kubernetes.io/name: {{ include "{chart_name}.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "{chart_name}.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | trunc 63 | trimSuffix "-" }}
{{- end }}
'''
    
    return {"name": name, "chart_name": chart_name, "framework": framework,
            "files": files, "file_count": len(files)}


def scaffold_terraform(name: str, framework: str = "fastapi", cloud: str = "aws",
                       region: str = "us-east-1", port: int = 8000) -> dict[str, Any]:
    """Generate Terraform configuration for cloud deployment."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,63}", name):
        return {"error": f"Invalid service name: {name!r}"}
    
    files = {}
    
    if cloud == "aws":
        files["terraform/main.tf"] = f'''terraform {{
  required_version = ">= 1.5"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "{region}"
}}

# ECR Repository
resource "aws_ecr_repository" "app" {{
  name                 = "{name}"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {{
    scan_on_push = true
  }}
}}

# ECS Cluster
resource "aws_ecs_cluster" "app" {{
  name = "{name}"
}}

# Task Definition
resource "aws_ecs_task_definition" "app" {{
  family                   = "{name}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {{
      name      = "{name}"
      image     = "${{aws_ecr_repository.app.repository_url}}:latest"
      cpu       = 256
      memory    = 512
      portMappings = [
        {{
          containerPort = {port}
          protocol      = "tcp"
        }}
      ]
      logConfiguration = {{
        logDriver = "awslogs"
        options = {{
          "awslogs-group"         = "/ecs/{name}"
          "awslogs-region"        = "{region}"
          "awslogs-stream-prefix" = "ecs"
        }}
      }}
      healthCheck = {{
        command  = ["CMD-SHELL", "curl -f http://localhost:{port}/health || exit 1"]
        interval = 30
        timeout  = 5
        retries  = 3
      }}
    }}
  ]
}}

# Service
resource "aws_ecs_service" "app" {{
  name            = "{name}"
  cluster         = aws_ecs_cluster.app.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 3
  launch_type     = "FARGATE"
  network_configuration {{
    subnets         = var.private_subnets
    security_groups = [aws_security_group.ecs.id]
    assign_public_ip = false
  }}
  load_balancer {{
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "{name}"
    container_port   = {port}
  }}
}}

# ALB
resource "aws_lb" "app" {{
  name               = "{name}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnets
}}

resource "aws_lb_target_group" "app" {{
  name        = "{name}"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check {{
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }}
}}

resource "aws_lb_listener" "http" {{
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"
  default_action {{
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }}
}}

# IAM Roles
resource "aws_iam_role" "ecs_execution" {{
  name = "{name}-ecs-execution"
  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{
        Service = "ecs-tasks.amazonaws.com"
      }}
    }}]
  }})
}}

resource "aws_iam_role" "ecs_task" {{
  name = "{name}-ecs-task"
  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{
        Service = "ecs-tasks.amazonaws.com"
      }}
    }}]
  }})
}}

# Security Groups
resource "aws_security_group" "ecs" {{
  name        = "{name}-ecs"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id
  ingress {{
    from_port   = {port}
    to_port     = {port}
    protocol    = "tcp"
    security_groups = [aws_security_group.alb.id]
  }}
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}

resource "aws_security_group" "alb" {{
  name        = "{name}-alb"
  description = "Security group for ALB"
  vpc_id      = var.vpc_id
  ingress {{
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {{
  name = "/ecs/{name}"
}}
'''
        files["terraform/variables.tf"] = f'''variable "vpc_id" {{
  description = "VPC ID"
  type        = string
}}

variable "private_subnets" {{
  description = "Private subnet IDs"
  type        = list(string)
}}

variable "public_subnets" {{
  description = "Public subnet IDs"
  type        = list(string)
}}
'''
        files["terraform/outputs.tf"] = f'''output "ecr_repository_url" {{
  value = aws_ecr_repository.app.repository_url
}}

output "ecs_cluster_name" {{
  value = aws_ecs_cluster.app.name
}}

output "service_url" {{
  value = "http://${{aws_lb.app.dns_name}}"
}}
'''
    
    return {"name": name, "cloud": cloud, "framework": framework,
            "files": files, "file_count": len(files)}


def scaffold_cloudbuild(name: str, framework: str = "fastapi", 
                        cloud: str = "gcp", region: str = "us-central1") -> dict[str, Any]:
    """Generate Cloud Build / CI configuration for container builds."""
    files = {}
    
    if cloud == "gcp":
        files["cloudbuild.yaml"] = f'''steps:
# Build and push to Artifact Registry
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', '{region}-docker.pkg.dev/$PROJECT_ID/{name}/{name}:$SHORT_SHA', '-t', '{region}-docker.pkg.dev/$PROJECT_ID/{name}/{name}:latest', '-f', 'Dockerfile', '.']
  env:
    - 'DOCKER_BUILDKIT=1'

# Run tests
- name: 'python:3.12-slim'
  entrypoint: 'bash'
  args:
    - '-c'
    - |
      pip install -r requirements.txt
      python -m pytest tests/ -v

# Deploy to Cloud Run
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: 'gcloud'
  args:
    - 'run'
    - 'deploy'
    - '{name}'
    - '--image={region}-docker.pkg.dev/$PROJECT_ID/{name}/{name}:$SHORT_SHA'
    - '--region={region}'
    - '--platform=managed'
    - '--allow-unauthenticated'
    - '--port=8080'
    - '--cpu=1'
    - '--memory=512Mi'
    - '--min-instances=1'
    - '--max-instances=100'
    - '--set-env-vars=PORT=8080'

images:
- '{region}-docker.pkg.dev/$PROJECT_ID/{name}/{name}'

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'E2_HIGHCPU_8'
'''
        files["cloudbuild.yaml.prod"] = f'''# Production deployment with canary
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', '{region}-docker.pkg.dev/$PROJECT_ID/{name}/{name}:$SHORT_SHA', '-f', 'Dockerfile', '.']

- name: 'python:3.12-slim'
  entrypoint: 'bash'
  args:
    - '-c'
    - |
      pip install -r requirements.txt
      python -m pytest tests/ -v

# Canary deployment (10% traffic)
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: 'gcloud'
  args:
    - 'run'
    - 'deploy'
    - '{name}-canary'
    - '--image={region}-docker.pkg.dev/$PROJECT_ID/{name}/{name}:$SHORT_SHA'
    - '--region={region}'
    - '--platform=managed'
    - '--no-allow-unauthenticated'
    - '--tag=canary'
    - '--cpu=1'
    - '--memory=512Mi'

# Promote canary after validation
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: 'bash'
  args:
    - '-c'
    - |
      sleep 60
      # Check canary health
      CANARY_URL=$(gcloud run services describe {name}-canary --region={region} --format="value(status.url)")
      if curl -f "$CANARY_URL/health"; then
        gcloud run services update-traffic {name} --to-tags=canary=100 --region={region}
      else
        echo "Canary failed health check"
        exit 1
      fi

images:
- '{region}-docker.pkg.dev/$PROJECT_ID/{name}/{name}'
'''
    elif cloud == "aws":
        files["buildspec.yml"] = f'''version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.{region}.amazonaws.com
      - REPOSITORY_URI=$ACCOUNT_ID.dkr.ecr.{region}.amazonaws.com/{name}
      - IMAGE_TAG=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $REPOSITORY_URI:latest -t $REPOSITORY_URI:$IMAGE_TAG -f Dockerfile .
      - echo Running tests...
      - docker run --rm $REPOSITORY_URI:$IMAGE_TAG python -m pytest tests/ -v
  post_build:
    commands:
      - echo Pushing the Docker images...
      - docker push $REPOSITORY_URI:latest
      - docker push $REPOSITORY_URI:$IMAGE_TAG
      - echo Writing image definitions file...
      - printf '[{{"name":"%s","imageUri":"%s"}}]' {name} $REPOSITORY_URI:$IMAGE_TAG > imagedefinitions.json
artifacts:
  files: imagedefinitions.json
'''
    
    return {"name": name, "cloud": cloud, "framework": framework,
            "files": files, "file_count": len(files)}


# ---------------------------------------------------------------------------
# Registry & Package Hub scaffolding
# ---------------------------------------------------------------------------

def scaffold_registry_config(name: str, registry_type: str = "oci",
                             public: bool = True) -> dict[str, Any]:
    """Generate registry configuration for package publishing."""
    files = {}
    
    if registry_type == "oci":
        files[".docker/config.json"] = f'''{{
  "auths": {{
    "ghcr.io": {{}},
    "docker.io": {{}},
    "{name}.azurecr.io": {{}}
  }},
  "credHelpers": {{
    "gcr.io": "gcloud",
    "ecr.aws": "ecr-login"
  }},
  "experimental": "enabled"
}}
'''
        files[".npmrc"] = f'''@pea:registry=https://registry.pea.dev
@pea:always-auth=true
//registry.pea.dev/:_authToken=${{PEA_REGISTRY_TOKEN}}
'''
        files["pea-publish.yml"] = f'''# GitHub Action for publishing to Pea registry
name: Publish to Pea Registry

on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install PeaLang
        run: pip install pealang
      
      - name: Build package
        run: pea build .
      
      - name: Sign package
        run: pea sign dist/*.whl --key ${{ secrets.PEA_SIGNING_KEY }}
      
      - name: Publish to registry
        run: pea publish dist/*.whl --registry https://registry.pea.dev
        env:
          PEA_REGISTRY_TOKEN: ${{ secrets.PEA_REGISTRY_TOKEN }}
'''
    
    return {"name": name, "registry_type": registry_type,
            "files": files, "file_count": len(files)}


# ---------------------------------------------------------------------------
# WASM production scaffolding
# ---------------------------------------------------------------------------

def scaffold_wasm_production(name: str, framework: str = "fastapi",
                             target: str = "wasm32-wasip1") -> dict[str, Any]:
    """Generate WASM production build configuration."""
    files = {}
    
    files["wasm-build.yml"] = f'''# GitHub Action for WASM build
name: Build WASM

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
          target: {target}
      
      - name: Install cargo-wasi
        run: cargo install cargo-wasi
      
      - name: Build WASM
        run: |
          cargo wasi build --release
      
      - name: Optimize WASM
        run: |
          wasm-opt -Oz target/{target}/release/{name}.wasm -o {name}.wasm
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: {name}-wasm
          path: {name}.wasm
          retention-days: 30
'''
    
    files["Dockerfile.wasm"] = f'''# Multi-stage WASM build
FROM rust:1.75 AS builder
RUN rustup target add {target}
RUN cargo install cargo-wasi wasm-opt

WORKDIR /build
COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo wasi build --release
RUN wasm-opt -Oz target/{target}/release/{name}.wasm -o {name}.wasm

# Runtime stage - using wasmtime
FROM ghcr.io/bytecodealliance/wasmtime:latest
WORKDIR /app
COPY --from=builder /build/{name}.wasm ./
COPY --from=builder /build/pea.wasm ./

EXPOSE 8080
CMD ["wasmtime", "--dir=.", "--env=PORT=8080", "pea.wasm"]
'''
    
    files["wasm-component.wit"] = f'''package pea:{name};

interface pea-api {{
  // HTTP handler
  handle-request: func(request: http-request) -> http-response;
  
  // Health check
  health: func() -> string;
  
  // Metrics
  metrics: func() -> metrics-data;
}}

world pea-component {{
  export pea-api;
  import wasi:cli/environment@0.2.0;
  import wasi:http/incoming-handler@0.2.0;
  import wasi:logging/logging@0.2.0;
}}
'''
    
    return {"name": name, "framework": framework, "target": target,
            "files": files, "file_count": len(files)}


# ---------------------------------------------------------------------------
# Edge/Serverless scaffolding
# ---------------------------------------------------------------------------

def scaffold_edge_worker(name: str, platform: str = "cloudflare",
                         framework: str = "fastapi") -> dict[str, Any]:
    """Generate Edge Worker / Serverless configuration."""
    files = {}
    
    if platform == "cloudflare":
        files["wrangler.toml"] = f'''name = "{name}"
main = "worker.js"
compatibility_date = "2024-01-01"

[vars]
ENVIRONMENT = "production"

[build]
command = "python -m pealang.wasm_build --target wasm32-wasip1"

[triggers]
crons = ["0 * * * *"]

[[kv_namespaces]]
binding = "CACHE"
id = "your-kv-namespace-id"

[[d1_databases]]
binding = "DB"
database_name = "{name}-db"
database_id = "your-database-id"
'''
        files["worker.py"] = f'''# Cloudflare Worker entry point for PeaLang
import json
import os

# This runs in the Cloudflare Workers Python runtime
# The actual PeaLang WASM module is loaded by the runtime

def handler(request):
    """Handle incoming HTTP request."""
    try:
        # Parse request
        method = request.method
        url = request.url
        headers = dict(request.headers)
        body = request.body if hasattr(request, 'body') else None
        
        # Route to PeaLang app
        from pealang import execute
        
        # In production, the app would be pre-compiled
        # This is a simplified example
        return {{
            "status": 200,
            "headers": {{"Content-Type": "application/json"}},
            "body": json.dumps({{
                "message": "Hello from PeaLang on Cloudflare Workers",
                "method": method,
                "url": url
            }})
        }}
    except Exception as e:
        return {{
            "status": 500,
            "headers": {{"Content-Type": "application/json"}},
            "body": json.dumps({{"error": str(e)}})
        }}

# Export for Workers runtime
addEventListener("fetch", lambda event: event.respondWith(handler(event.request)))
'''
        files["package.json"] = f'''{{
  "name": "{name}-worker",
  "version": "1.0.0",
  "private": true,
  "scripts": {{
    "dev": "wrangler dev",
    "deploy": "wrangler deploy",
    "build": "python -m pealang.wasm_build"
  }},
  "devDependencies": {{
    "@cloudflare/workers-types": "^4.20240101.0",
    "wrangler": "^3.0.0"
  }}
}}
'''
    elif platform == "vercel":
        files["vercel.json"] = f'''{{
  "buildCommand": "python -m pealang.wasm_build --target wasm32-wasip1",
  "outputDirectory": "dist",
  "framework": "python",
  "functions": {{
    "api/index.py": {{
      "runtime": "python3.12",
      "maxDuration": 30
    }}
  }},
  "headers": [
    {{
      "source": "/(.*)",
      "headers": [
        {{"key": "X-Content-Type-Options", "value": "nosniff"}},
        {{"key": "X-Frame-Options", "value": "DENY"}},
        {{"key": "X-XSS-Protection", "value": "1; mode=block"}}
      ]
    }}
  ]
}}
'''
        files["api/index.py"] = f'''# Vercel Python Serverless Function
import json
from pealang import execute

def handler(request):
    try:
        # In production, use pre-compiled WASM
        result = execute("""
import web
app = web.app()

@app.get("/health")
def health(req):
    return {{"status": "ok", "service": "{name}"}}

app.serve("0.0.0.0", 8000)
""", source_name="vercel.pea")
        
        # For serverless, we return the response directly
        return {{
            "statusCode": 200,
            "headers": {{"Content-Type": "application/json"}},
            "body": json.dumps({{"message": "PeaLang on Vercel"}})
        }}
    except Exception as e:
        return {{
            "statusCode": 500,
            "headers": {{"Content-Type": "application/json"}},
            "body": json.dumps({{"error": str(e)}})
        }}

# Vercel expects a handler function
from http.server import BaseHTTPRequestHandler
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({{"message": "PeaLang on Vercel"}}).encode())
'''
    elif platform == "aws":
        files["template.yaml"] = f'''AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: PeaLang Lambda function

Globals:
  Function:
    Timeout: 30
    MemorySize: 512
    Runtime: python3.12
    Environment:
      Variables:
        PORT: 8080

Resources:
  PeaLangFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: {name}
      Handler: lambda_function.handler
      CodeUri: .
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /{{proxy+}}
            Method: any
      Policies:
        - AWSLambdaBasicExecutionRole
        - AWSXRayDaemonWriteAccess

Outputs:
  ApiUrl:
    Description: "API Gateway endpoint URL"
    Value: !Sub "https://${{ServerlessRestApi}}.execute-api.${{AWS::Region}}.amazonaws.com/Prod/"
'''
        files["lambda_function.py"] = f'''# AWS Lambda handler for PeaLang
import json
import os
from pealang import execute

def handler(event, context):
    """Lambda entry point."""
    try:
        # Parse API Gateway event
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        headers = event.get('headers', {{}})
        body = event.get('body', '')
        query_params = event.get('queryStringParameters', {{}}) or {{}}
        
        # Route to PeaLang app (simplified)
        # In production, use pre-compiled WASM module
        
        return {{
            'statusCode': 200,
            'headers': {{
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }},
            'body': json.dumps({{
                'message': 'PeaLang on AWS Lambda',
                'method': http_method,
                'path': path
            }})
        }}
    except Exception as e:
        return {{
            'statusCode': 500,
            'headers': {{'Content-Type': 'application/json'}},
            'body': json.dumps({{'error': str(e)}})
        }}
'''
    
    return {"name": name, "platform": platform, "framework": framework,
            "files": files, "file_count": len(files)}


# ---------------------------------------------------------------------------
# Update namespace builder
# ---------------------------------------------------------------------------

def build_frameworks_namespace() -> dict[str, Any]:
    return {
        "scaffold_backend": scaffold_backend,
        "scaffold_fullstack": scaffold_fullstack,
        "write_scaffold": write_scaffold,
        "adr": adr,
        "adr_index": adr_index,
        "adr_transition": adr_transition,
        "adr_filter": adr_filter,
        "service_contract": service_contract,
        "service_contract_to_openapi": service_contract_to_openapi,
        "openapi_json": openapi_json,
        "layered_architecture_check": layered_architecture_check,
        # Platform & Deployment (Phase 3)
        "scaffold_k8s": scaffold_k8s,
        "scaffold_helm_chart": scaffold_helm_chart,
        "scaffold_terraform": scaffold_terraform,
        "scaffold_cloudbuild": scaffold_cloudbuild,
        "scaffold_registry_config": scaffold_registry_config,
        "scaffold_wasm_production": scaffold_wasm_production,
        "scaffold_edge_worker": scaffold_edge_worker,
    }

def adr(title: str, context: str, decision: str,
        consequences: str, status: str = "accepted", adr_number: int | None = None) -> str:
    """Generate a markdown Architecture Decision Record."""
    num = adr_number if adr_number is not None else int(time.time()) % 10000
    return (
        f"# ADR-{num:04d}: {title}\n\n"
        f"- Status: {status}\n"
        f"- Date: {time.strftime('%Y-%m-%d')}\n\n"
        f"## Context\n\n{context}\n\n"
        f"## Decision\n\n{decision}\n\n"
        f"## Consequences\n\n{consequences}\n"
    )


def adr_index(records: list[dict[str, str]], status: str | None = None, owner: str | None = None) -> str:
    """Generate an index markdown for a list of ADRs, optionally filtered by status/owner."""
    lines = ["# Architecture Decision Records", ""]
    for rec in records:
        rec_status = rec.get("status", "unknown")
        rec_owner = rec.get("owner")
        if status is not None and str(rec_status or "").lower() != str(status).lower():
            continue
        if owner is not None and str(rec_owner or "") != str(owner):
            continue
        num = rec.get("number", "?")
        title = rec.get("title", "Untitled")
        superseded_by = rec.get("superseded_by")
        line = f"- ADR-{num}: {title} — {rec_status}"
        if rec_owner:
            line += f" (owner: {rec_owner})"
        if superseded_by:
            line += f" (superseded by ADR-{superseded_by})"
        supersedes = rec.get("supersedes")
        if supersedes:
            line += f" (supersedes ADR-{supersedes})"
        lines.append(line)
    return "\n".join(lines) + "\n"


_ADR_STATUSES = ("proposed", "accepted", "deprecated", "superseded", "rejected")


def adr_transition(record: dict[str, Any], new_status: str, superseded_by: str | None = None) -> dict[str, Any]:
    """Return a copy of an ADR record with an updated, validated status."""
    if new_status not in _ADR_STATUSES:
        return {"error": f"Invalid ADR status {new_status!r}", "allowed": list(_ADR_STATUSES)}
    updated = dict(record)
    updated["status"] = new_status
    if superseded_by is not None:
        updated["superseded_by"] = superseded_by
    return updated


def adr_filter(records: list[dict[str, Any]], status: str | None = None,
               owner: str | None = None) -> list[dict[str, Any]]:
    """Filter ADR records by status and/or owner."""
    out = []
    for rec in records:
        if status is not None and rec.get("status") != status:
            continue
        if owner is not None and rec.get("owner") != owner:
            continue
        out.append(rec)
    return out


def service_contract(service: str, routes: list[dict[str, Any]] | None = None,
                     version: str = "1.0.0") -> dict[str, Any]:
    """Build a simple service contract manifest (routes, owners, version)."""
    routes = routes or []
    endpoints = []
    for r in routes:
        endpoints.append({
            "method": r.get("method", "GET").upper(),
            "path": r.get("path", "/"),
            "name": r.get("name") or r.get("path", "/").strip("/").replace("/", "_") or "index",
            "owner": r.get("owner", "unassigned"),
            "auth": r.get("auth", "none"),
            "request_body": r.get("request_body"),
            "response_body": r.get("response_body"),
            "response_schema": r.get("response_schema"),
        })
    return {
        "service": service,
        "version": version,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "endpoints": endpoints,
        "endpoint_count": len(endpoints),
    }


def service_contract_to_openapi(contract: dict[str, Any],
                                title: str | None = None,
                                version: str | None = None,
                                contact: dict[str, Any] | None = None,
                                license: dict[str, Any] | None = None,
                                description: str | None = None,
                                include_error_responses: bool = True) -> dict[str, Any]:
    """Convert a service_contract dict into an OpenAPI 3.0 specification.

    Routes become paths/operations; `auth: jwt` maps to a bearer security
    scheme; `owner` is surfaced as x-owner. Endpoints may include request/
    response schemas. Optional info metadata (contact/license/description) and
    default error response schemas (4xx/5xx) can be included for richer API docs.
    """
    if not isinstance(contract, dict):
        return {"error": "Expected a service_contract dict"}

    service = contract.get("service", "service")
    spec_version = version or contract.get("version") or "1.0.0"
    spec_title = title or f"{service} API"

    paths: dict[str, Any] = {}
    needs_bearer = False
    for ep in contract.get("endpoints", []):
        method = str(ep.get("method", "GET")).lower()
        path = ep.get("path", "/")
        path_item = paths.setdefault(path, {})
        op: dict[str, Any] = {
            "operationId": ep.get("name") or path.strip("/").replace("/", "_") or "index",
            "summary": ep.get("summary") or f"{ep.get('method', 'GET').upper()} {path}",
            "x-owner": ep.get("owner", "unassigned"),
            "responses": {"200": {"description": "Success"}},
        }
        if ep.get("description"):
            op["description"] = ep["description"]
        req_body = ep.get("request_body")
        if req_body is not None:
            op["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": req_body}},
            }
        resp_schema = ep.get("response_schema")
        if resp_schema is not None:
            op["responses"]["200"] = {
                "description": "Success",
                "content": {"application/json": {"schema": resp_schema}},
            }
        if str(ep.get("auth", "none")).lower() == "jwt":
            op["security"] = [{"bearerAuth": []}]
            needs_bearer = True
        if include_error_responses:
            error_schema = {"$ref": "#/components/schemas/Error"}
            for code, desc in (("400", "Bad Request"), ("401", "Unauthorized"),
                               ("403", "Forbidden"), ("404", "Not Found"),
                               ("422", "Unprocessable Entity"), ("429", "Too Many Requests"),
                               ("500", "Internal Server Error")):
                op["responses"][code] = {
                    "description": desc,
                    "content": {"application/json": {"schema": error_schema}},
                }
        path_item[method] = op

    info: dict[str, Any] = {"title": spec_title, "version": spec_version}
    desc = description or contract.get("description")
    if desc:
        info["description"] = desc
    contact_info = contact or contract.get("contact")
    if isinstance(contact_info, dict):
        info["contact"] = contact_info
    license_info = license or contract.get("license")
    if isinstance(license_info, dict):
        info["license"] = license_info
    terms = contract.get("termsOfService")
    if terms:
        info["termsOfService"] = terms

    spec: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": info,
        "paths": paths,
    }
    components: dict[str, Any] = {}
    if needs_bearer:
        components["securitySchemes"] = {
            "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
        }
    if include_error_responses:
        components.setdefault("schemas", {})
        components["schemas"]["Error"] = {
            "type": "object",
            "properties": {
                "error": {"type": "string"},
                "message": {"type": "string"},
                "code": {"type": "string"},
                "details": {"type": "object"},
            },
            "required": ["error", "message"],
        }
    if components:
        spec["components"] = components
    return spec


def openapi_json(contract: dict[str, Any], title: str | None = None,
                 version: str | None = None, contact: dict[str, Any] | None = None,
                 license: dict[str, Any] | None = None, description: str | None = None,
                 include_error_responses: bool = True) -> str:
    """Return the OpenAPI document for a service contract as a JSON string."""
    spec = service_contract_to_openapi(
        contract, title=title, version=version, contact=contact,
        license=license, description=description,
        include_error_responses=include_error_responses,
    )
    return json.dumps(spec, indent=2, sort_keys=True)


def layered_architecture_check(source: str) -> dict[str, Any]:
    """Detect layering-style violations in PeaLang sources.

    Flags raw SQL/string literals executed from the UI/presentation layer and
    direct network calls from the data layer — a lightweight, honest check,
    not a full architecture enforcer.
    """
    findings: list[dict[str, Any]] = []
    lines = source.splitlines()
    layer = None
    for i, line in enumerate(lines, 1):
        m = re.match(r"^\s*//\s*layer:\s*([a-z_]+)", line)
        if m:
            layer = m.group(1)
            continue
        stripped = line.strip()
        if layer == "ui" and re.search(r"SELECT\s|INSERT\s|UPDATE\s|DELETE\s", stripped, re.I):
            findings.append({"line": i, "severity": "warning",
                             "message": "Raw SQL in UI layer; move to data layer"})
        if layer == "data" and re.search(r"\bfetch\(|http_get\(|http_post\(", stripped):
            findings.append({"line": i, "severity": "warning",
                             "message": "Direct network call in data layer; route via service layer"})
    return {"findings": findings, "ok": not any(f["severity"] == "error" for f in findings)}


# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------

def build_frameworks_namespace() -> dict[str, Any]:
    return {
        "scaffold_backend": scaffold_backend,
        "scaffold_fullstack": scaffold_fullstack,
        "write_scaffold": write_scaffold,
        "adr": adr,
        "adr_index": adr_index,
        "adr_transition": adr_transition,
        "adr_filter": adr_filter,
        "service_contract": service_contract,
        "service_contract_to_openapi": service_contract_to_openapi,
        "openapi_json": openapi_json,
        "layered_architecture_check": layered_architecture_check,
    }
