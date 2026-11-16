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

    files["README.md"] = (
        f"# {name}\n\n"
        f"Backend service scaffolded by PeaLang frameworks toolkit.\n\n"
        f"Framework: {b['framework']} ({b['language']})\n"
        f"Entrypoint: `{b['entrypoint']}`\nPort: {port}\n\n"
        "```bash\n"
        + ("pip install -r requirements.txt && uvicorn app.main:app --reload\n" if framework in ("fastapi", "flask")
           else "npm install && npm start\n" if framework == "express" else "go run ./cmd/server\n")
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
    else:
        files["frontend/README.md"] = f"# {name} frontend\nFramework '{frontend}' not scaffolded; choose 'react'.\n"

    files["README.md"] = (
        f"# {name}\n\n"
        f"Full-stack PeaLang task skeleton: `{backend}` backend + `{frontend}` frontend.\n\n"
        f"- Backend under `backend/` (port {port})\n- Frontend under `frontend/`\n\n"
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
# Architecture tooling (solution architects)
# ---------------------------------------------------------------------------

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


def adr_index(records: list[dict[str, str]]) -> str:
    """Generate an index markdown for a list of ADRs."""
    lines = ["# Architecture Decision Records", ""]
    for rec in records:
        num = rec.get("number", "?")
        title = rec.get("title", "Untitled")
        status = rec.get("status", "unknown")
        lines.append(f"- ADR-{num}: {title} — {status}")
    return "\n".join(lines) + "\n"


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
                                version: str | None = None) -> dict[str, Any]:
    """Convert a service_contract dict into an OpenAPI 3.0 specification.

    Routes become paths/operations; `auth: jwt` maps to a bearer security
    scheme; `owner` is surfaced as x-owner. Endpoints get no input schemas
    (contracts intentionally carry no payloads), so this is an honest minimal
    spec suitable both for web clients (via generate_typescript_client) and
    for backend/architect documentation.
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
            "summary": f"{ep.get('method', 'GET').upper()} {path}",
            "x-owner": ep.get("owner", "unassigned"),
            "responses": {"200": {"description": "Success"}},
        }
        if str(ep.get("auth", "none")).lower() == "jwt":
            op["security"] = [{"bearerAuth": []}]
            needs_bearer = True
        path_item[method] = op

    spec: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": spec_title, "version": spec_version},
        "paths": paths,
    }
    if needs_bearer:
        spec["components"] = {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
            },
        }
    return spec


def openapi_json(contract: dict[str, Any], title: str | None = None,
                 version: str | None = None) -> str:
    """Return the OpenAPI document for a service contract as a JSON string."""
    spec = service_contract_to_openapi(contract, title=title, version=version)
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
        "service_contract": service_contract,
        "service_contract_to_openapi": service_contract_to_openapi,
        "openapi_json": openapi_json,
        "layered_architecture_check": layered_architecture_check,
    }
