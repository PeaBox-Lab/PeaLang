"""PeaLang Developer Portal (v2.36.0).

A self-hosted developer portal web application that provides:

* Template gallery browser for scaffold templates
* Library authoring guide and best practices
* Interactive API reference
* Quick project creation from templates
* Extension registry browser
"""

from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List

from .project import TEMPLATES, TEMPLATE_BUILTINS
from .extension_registry import ExtensionRegistry


class PortalHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the developer portal."""

    server: 'DeveloperPortalServer'

    def send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, status: int, html: str) -> None:
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, status: int, path: Path) -> None:
        body = path.read_bytes()
        mime, _ = mimetypes.guess_type(str(path))
        self.send_response(status)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?")[0]

        # Static assets
        if path.startswith("/static/"):
            asset_path = Path("docs") / path[len("/static/"):]
            if asset_path.is_file():
                self.send_file(200, asset_path)
            else:
                self.send_json(404, {"error": "asset not found"})
            return

        # API endpoints
        if path == "/api/templates":
            self.send_json(200, self.server.list_templates())
            return

        if path == "/api/extensions":
            self.send_json(200, self.server.list_extensions())
            return

        if path.startswith("/api/templates/"):
            name = path[len("/api/templates/"):]
            self.send_json(200, self.server.get_template(name))
            return

        if path == "/":
            self.send_html(200, self.server.index_html())
            return

        self.send_json(404, {"error": "not found"})


class DeveloperPortalServer:
    """Self-hosted developer portal server."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8789,
        storage_dir: str = "./portal-storage",
    ) -> None:
        self.host = host
        self.port = port
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.extension_registry = ExtensionRegistry()

    def list_templates(self) -> Dict[str, Any]:
        """List all available project templates."""
        templates: Dict[str, Any] = {}
        for name, content in TEMPLATES.items():
            templates[name] = {
                "name": name,
                "preview": content[:200],
                "size": len(content),
            }
        return templates

    def get_template(self, name: str) -> Dict[str, Any]:
        """Get details for a specific template."""
        if name not in TEMPLATES:
            return {"error": f"template {name} not found"}
        return {
            "name": name,
            "content": TEMPLATES[name],
            "size": len(TEMPLATES[name]),
        }

    def list_extensions(self) -> Dict[str, Any]:
        """List all registered extensions."""
        return self.extension_registry.list_all()

    def index_html(self) -> str:
        """Render the portal index page."""
        templates = self.list_templates()
        template_list = "\n".join(
            f'<li><a href="/template/{name}">{name}</a> '
            f'({details["size"]} bytes)</li>'
            for name, details in sorted(templates.items())
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PeaLang Developer Portal</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f5f5f7; color: #1d1d1f; }}
        header {{ background: #1d1d1f; color: white; padding: 1.5rem 2rem; }}
        h1 {{ margin: 0; font-size: 1.75rem; }}
        .subtitle {{ margin-top: 0.5rem; opacity: 0.8; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        .card {{ background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .card h2 {{ margin-top: 0; font-size: 1.25rem; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin-bottom: 0.75rem; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; }}
        .tag {{ display: inline-block; background: #e5e5ea; color: #1d1d1f; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.875rem; margin-right: 0.5rem; }}
        .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e5ea; color: #86868b; font-size: 0.875rem; }}
    </style>
</head>
<body>
    <header>
        <h1>PeaLang Developer Portal</h1>
        <div class="subtitle">Build, scaffold, and extend PeaLang applications</div>
    </header>
    <div class="container">
        <div class="card">
            <h2>Template Gallery</h2>
            <p>Choose a template to scaffold a new PeaLang project:</p>
            <ul class="grid">
                {template_list}
            </ul>
        </div>
        <div class="card">
            <h2>API Endpoints</h2>
            <ul>
                <li><a href="/api/templates">GET /api/templates</a> - List all templates</li>
                <li><a href="/api/templates/node-sdk">GET /api/templates/&lt;name&gt;</a> - Get template details</li>
                <li><a href="/api/extensions">GET /api/extensions</a> - List all extensions</li>
            </ul>
        </div>
        <div class="card">
            <h2>Quick Commands</h2>
            <ul>
                <li><code>pea init --template library mylib</code> - Scaffold a library</li>
                <li><code>pea build --library ./mylib</code> - Build a .pelib package</li>
                <li><code>pea publish ./mylib --registry http://registry:8788 --token &lt;token&gt;</code> - Publish to registry</li>
                <li><code>pea search mylib --registry http://registry:8788</code> - Search for packages</li>
            </ul>
        </div>
    </div>
    <div class="footer">
        PeaLang Developer Portal &mdash; Build powerful applications with PeaLang
    </div>
</body>
</html>"""


def serve(
    host: str = "127.0.0.1",
    port: int = 8789,
    storage_dir: str = "./portal-storage",
) -> None:
    """Start the PeaLang developer portal server."""
    server = ThreadingHTTPServer((host, port), PortalHandler)
    server.server = DeveloperPortalServer(host, port, storage_dir)  # type: ignore[attr-defined]
    print(f"PeaLang Developer Portal on http://{host}:{port}")
    print(f"Storage: {storage_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPortal server stopped.")
        server.server_close()

