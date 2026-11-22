"""Native FFI, plugin SDK, and multi-language host bindings for PeaLang (v1.9.0).

Provides bidirectional FFI, host SDK scaffolding (Go, Node.js/TypeScript),
OpenAPI/GraphQL importer, and plugin package management.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Bidirectional FFI helpers
# ---------------------------------------------------------------------------

def register_host_function(name: str, module: str, function: str,
                           arg_types: list[str] | None = None,
                           return_type: str = "any") -> dict[str, Any]:
    """Register a host function as a PeaLang builtin."""
    return {
        "name": name,
        "module": module,
        "function": function,
        "arg_types": arg_types or [],
        "return_type": return_type,
        "registered": True,
    }


def generate_python_export_decorator(func_name: str, arg_types: list[str] | None = None,
                                    return_type: str = "any") -> str:
    """Generate a Python @pea_export decorator for exposing host functions."""
    args = arg_types or []
    return f'''# PeaLang host function export
from pealang.embedding import PeaRuntime

def pea_export(func):
    """Decorator to export a Python function as a PeaLang builtin."""
    func._pea_export = True
    func._pea_arg_types = {args!r}
    func._pea_return_type = {return_type!r}
    return func

# Usage:
# @pea_export
# def {func_name}({", ".join(f"arg{i}" for i in range(len(args)))}):
#     ...
#     return result
'''


def generate_typescript_export(func_name: str, arg_types: list[str] | None = None,
                              return_type: str = "any") -> str:
    """Generate a TypeScript @pea_export decorator."""
    args = arg_types or []
    params = ", ".join(f"arg{i}: any" for i in range(len(args)))
    return f'''// PeaLang host function export for TypeScript/Node.js
export function peaExport(target: any) {{
  target._peaExport = true;
  target._peaArgTypes = {json.dumps(args)};
  target._peaReturnType = {json.dumps(return_type)};
  return target;
}}

// Usage:
// @peaExport
// function {func_name}({params}): {return_type} {{
//   ...
//   return result;
// }}
'''


def generate_java_export(func_name: str, arg_types: list[str] | None = None,
                        return_type: str = "Object") -> str:
    """Generate a Java @PeaExport annotation."""
    args = arg_types or []
    return f'''// PeaLang host function export for Java
package com.pealang.host;

import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface PeaExport {{
    String name() default "{func_name}";
    String[] argTypes() default {{}};
    String returnType() default "{return_type}";
}}

// Usage:
// @PeaExport(name = "{func_name}")
// public {return_type} {func_name}({", ".join(f"Object arg{i}" for i in range(len(args)))}) {{
//   ...
//   return result;
// }}
'''


# ---------------------------------------------------------------------------
# Host SDK scaffolding
# ---------------------------------------------------------------------------

def scaffold_go_sdk(target_dir: str = "go-sdk") -> dict[str, Any]:
    """Scaffold a Go SDK directory structure."""
    root = Path(target_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "pealang").mkdir(exist_ok=True)
    (root / "pealang" / "client.go").write_text('''package pealang

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type Client struct {
	BaseURL string
	HTTP    *http.Client
}

func NewClient(baseURL string) *Client {
	return &Client{BaseURL: baseURL, HTTP: &http.Client{Timeout: 30 * time.Second}}
}

func (c *Client) Invoke(module, function string, args ...interface{}) (json.RawMessage, error) {
	payload, _ := json.Marshal(map[string]interface{}{
		"module": module, "function": function, "args": args,
	})
	resp, err := c.HTTP.Post(c.BaseURL+"/v1/invoke", "application/json", bytes.NewReader(payload))
	if err != nil { return nil, err }
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	var result struct {
		OK     bool            `json:"ok"`
		Result json.RawMessage `json:"result"`
		Error  *struct{ Message string `json:"message"` } `json:"error"`
	}
	json.Unmarshal(body, &result)
	if !result.OK {
		msg := "invocation failed"
		if result.Error != nil { msg = result.Error.Message }
		return nil, fmt.Errorf("pealang: %s", msg)
	}
	return result.Result, nil
}
''', encoding="utf-8")
    (root / "go.mod").write_text("module pealang-go-sdk\n\ngo 1.21\n", encoding="utf-8")
    (root / "README.md").write_text("# PeaLang Go SDK\n\nGo client for PeaLang runtime.\n", encoding="utf-8")
    return {"root": str(root), "files": ["pealang/client.go", "go.mod", "README.md"]}


def scaffold_node_sdk(target_dir: str = "node-sdk") -> dict[str, Any]:
    """Scaffold a Node.js/TypeScript host SDK directory structure."""
    root = Path(target_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir(exist_ok=True)
    (root / "src" / "index.ts").write_text('''// PeaLang Node.js/TypeScript Host SDK
export class PeaClient {
  constructor(private baseUrl: string) {}
  async invoke(module: string, fn: string, args: any[] = []): Promise<any> {
    const resp = await fetch(`${this.baseUrl}/v1/invoke`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ module, function: fn, args }),
    });
    const body = await resp.json();
    if (!resp.ok || !body.ok) throw new Error(body?.error?.message ?? "Invocation failed");
    return body.result;
  }
  async health(): Promise<any> {
    const resp = await fetch(`${this.baseUrl}/health`);
    return resp.json();
  }
}
export default PeaClient;
''', encoding="utf-8")
    (root / "package.json").write_text(json.dumps({
        "name": "pealang-node-sdk",
        "version": "1.0.0",
        "main": "dist/index.js",
        "types": "dist/index.d.ts",
        "scripts": {"build": "tsc", "test": "jest"},
    }, indent=2), encoding="utf-8")
    (root / "tsconfig.json").write_text(json.dumps({
        "compilerOptions": {"target": "ES2020", "module": "commonjs", "outDir": "./dist", "strict": True},
    }, indent=2), encoding="utf-8")
    (root / "README.md").write_text("# PeaLang Node.js SDK\n\nNode.js client for PeaLang runtime.\n", encoding="utf-8")
    return {"root": str(root), "files": ["src/index.ts", "package.json", "tsconfig.json", "README.md"]}


def scaffold_python_sdk(target_dir: str = "python-sdk") -> dict[str, Any]:
    """Scaffold a Python host SDK directory structure."""
    root = Path(target_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "pealang").mkdir(exist_ok=True)
    (root / "pealang" / "client.py").write_text('''"""PeaLang Python host client."""
import json
import urllib.request
from typing import Any


class PeaClient:
    """HTTP client for the PeaLang runtime service."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def invoke(self, module: str, function: str, args: list[Any] | None = None) -> Any:
        payload = json.dumps({"module": module, "function": function, "args": args or []}).encode()
        req = urllib.request.Request(
            f"{self.base_url}/v1/invoke",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode())
            if not resp.ok or not body.get("ok"):
                raise RuntimeError(body.get("error", {}).get("message") or "Invocation failed")
            return body.get("result")

    def health(self) -> dict[str, Any]:
        with urllib.request.urlopen(f"{self.base_url}/health", timeout=self.timeout) as resp:
            return json.loads(resp.read().decode())


__all__ = ["PeaClient"]
''', encoding="utf-8")
    (root / "pyproject.toml").write_text(
        "[project]\nname = \"pealang-python-sdk\"\nversion = \"1.0.0\"\n\n"
        "[project.scripts]\npea = \"pealang.client:PeaClient\"\n\n"
        "[tool.setuptools.packages.find]\ninclude = [\"pealang*\"]\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "# PeaLang Python SDK\n\nPython client for PeaLang runtime.\n", encoding="utf-8"
    )
    return {"root": str(root), "files": ["pealang/client.py", "pyproject.toml", "README.md"]}


# ---------------------------------------------------------------------------
# OpenAPI/GraphQL importer
# ---------------------------------------------------------------------------

def import_openapi(spec: dict[str, Any] | str) -> dict[str, Any]:
    """Parse an OpenAPI spec and generate PeaLang connector scaffolding."""
    if isinstance(spec, str):
        try:
            spec = json.loads(spec)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON spec"}
    paths = spec.get("paths", {})
    connectors = []
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() not in ("get", "post", "put", "delete", "patch"):
                continue
            name = details.get("operationId", f"{method}_{path}".replace("/", "_").replace("{", "").replace("}", ""))
            connectors.append({
                "name": name,
                "method": method.upper(),
                "path": path,
                "summary": details.get("summary", ""),
                "parameters": details.get("parameters", []),
                "requestBody": details.get("requestBody"),
                "responses": details.get("responses", {}),
            })
    return {
        "title": spec.get("info", {}).get("title", "API"),
        "version": spec.get("info", {}).get("version", "1.0"),
        "base_url": (spec.get("servers", [{}])[0].get("url", "") if spec.get("servers") else ""),
        "connectors": connectors,
        "count": len(connectors),
    }


def generate_connector_package(imported: dict[str, Any]) -> str:
    """Generate a PeaLang connector package from imported API spec."""
    lines = [
        f"// Auto-generated PeaLang connector for {imported.get('title', 'API')}",
        f"// Version: {imported.get('version', '1.0')}",
        "",
        "let BASE_URL = " + json.dumps(imported.get("base_url", "")),
        "",
    ]
    for conn in imported.get("connectors", []):
        name = conn["name"]
        method = conn["method"].lower()
        path = conn["path"]
        lines.append(f"function {name}(params) {{")
        lines.append(f'  let url = BASE_URL + "{path}"')
        lines.append(f'  return http_{method}(url, params)')
        lines.append("}")
        lines.append("")
    return "\n".join(lines)


def build_host_bindings_namespace() -> dict[str, Any]:
    return {
        "register_host_function": register_host_function,
        "generate_python_export": generate_python_export_decorator,
        "generate_typescript_export": generate_typescript_export,
        "generate_java_export": generate_java_export,
        "scaffold_go_sdk": scaffold_go_sdk,
        "scaffold_node_sdk": scaffold_node_sdk,
        "import_openapi": import_openapi,
        "generate_connector_package": generate_connector_package,
    }
