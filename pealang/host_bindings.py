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


def scaffold_browser_sdk(target_dir: str = "browser-sdk") -> dict[str, Any]:
    """Scaffold a browser host SDK directory structure.

    Emits the browser runtime bridge (WebAssembly instantiation + host
    capability bridge) plus a small TypeScript client so browser hosts can
    load a ``PEAWASM`` artifact and invoke the exported ``pea_run`` / ``pea_health``
    functions.
    """
    root = Path(target_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir(exist_ok=True)
    (root / "src" / "browserClient.ts").write_text(
        "// PeaLang browser host SDK: WebAssembly loading + runtime bridge\n"
        "export interface BrowserWasmModule {\n"
        "  exports: { pea_run: (...args: any[]) => any; pea_health: (...args: any[]) => any };\n"
        "}\n\n"
        "export function createBrowserWasmModule(url: string, capabilities: string[] = []) {\n"
        "  // Placeholder for real artifact fetching/instantiation; hosts provide bytes.\n"
        "  throw new Error(\"browser_sdk: artifact bytes must be provided via a real loader\");\n"
        "}\n",
        encoding="utf-8",
    )
    (root / "src" / "browserLoader.ts").write_text(
        "// PeaLang browser loader: fetch + instantiate PEAWASM artifact.\n"
        "export async function loadPeaWasm(url: string, imports: Record<string, unknown> = {}) {\n"
        "  const res = await fetch(url);\n"
        "  const bytes = await res.arrayBuffer();\n"
        "  const mod = await WebAssembly.instantiate(bytes, imports);\n"
        "  return mod;\n"
        "}\n",
        encoding="utf-8",
    )
    (root / "package.json").write_text(
        json.dumps({
            "name": "pealang-browser-sdk",
            "version": "1.0.0",
            "main": "src/browserClient.ts",
            "types": "src/browserClient.ts",
            "scripts": {"build": "tsc", "test": "jest"},
        }, indent=2),
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "# PeaLang Browser SDK\n\nBrowser client for PeaLang runtime via WebAssembly.\n",
        encoding="utf-8",
    )
    return {
        "root": str(root),
        "files": ["src/browserClient.ts", "src/browserLoader.ts", "package.json", "README.md"],
    }



def scaffold_java_sdk(target_dir: str = "java-sdk") -> dict[str, Any]:
    """Scaffold a Java host SDK directory structure.

    Generates a Maven starter project with a PeaLang runtime connector,
    main class, health endpoint, and build configuration.
    """
    root = Path(target_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "src" / "main" / "java").mkdir(parents=True, exist_ok=True)
    (root / "src" / "main" / "java" / "com" / "pealang").mkdir(parents=True, exist_ok=True)
    (root / "src" / "main" / "resources").mkdir(parents=True, exist_ok=True)
    (root / "pom.xml").write_text('''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.pealang</groupId>
    <artifactId>pealang-java-sdk</artifactId>
    <version>1.0.0</version>
    <properties>
        <java.version>17</java.version>
        <pealang.sdk.version>2.22.0</pealang.sdk.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>com.pealang</groupId>
            <artifactId>pealang-runtime</artifactId>
            <version>${pealang.sdk.version}</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.8.1</version>
                <configuration>
                    <release>${java.version}</release>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
''', encoding="utf-8")
    (root / "src" / "main" / "java" / "com" / "pealang" / "SdkClient.java").write_text(r'''package com.pealang;

import com.pealang.runtime.PeaClient;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class SdkClient {
    private final PeaClient client;
    private final HttpClient http;

    public SdkClient(String baseUrl) {
        this.client = new PeaClient(baseUrl);
        this.http = HttpClient.newHttpClient();
    }

    public String invoke(String module, String function, String... args) throws Exception {
        String payload = "{\"module\":\"" + module + "\",\"function\":\"" + function + "\",\"args\":\"" + String.join(",", args) + "\"}";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(client.getBaseUrl() + "/v1/invoke"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payload))
                .build();
        HttpResponse<String> response = http.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) {
            throw new RuntimeException("Invocation failed: " + response.body());
        }
        return response.body();
    }

    public String health() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(client.getBaseUrl() + "/health"))
                .GET()
                .build();
        HttpResponse<String> response = http.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) {
            throw new RuntimeException("Health check failed: " + response.body());
        }
        return response.body();
    }
}
''', encoding="utf-8")
    (root / "src" / "main" / "resources" / "application.yml").write_text(
        "server:\n  port: 8080\n\npealang:\n  base-url: http://localhost:8080\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "# PeaLang Java SDK\n\nMaven-based Java client for PeaLang runtime.\n",
        encoding="utf-8",
    )
    return {
        "root": str(root),
        "files": [
            "src/main/java/com/pealang/SdkClient.java",
            "pom.xml",
            "src/main/resources/application.yml",
            "README.md",
        ],
    }


def scaffold_csharp_sdk(target_dir: str = "csharp-sdk") -> dict[str, Any]:
    """Scaffold a C#/.NET host SDK directory structure.

    Generates a .NET 8 starter project with a PeaLang runtime connector,
    main client class, configuration, and build configuration.
    """
    root = Path(target_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "pealang").mkdir(parents=True, exist_ok=True)
    (root / "pealang" / "SdkClient.cs").write_text(
        "using System;\\n"
        "using System.Net.Http;\\n"
        "using System.Text;\\n"
        "using System.Text.Json;\\n\\n"
        "namespace PeaLang;\\n\\n"
        "public class SdkClient\\n"
        "{\\n"
        "    private readonly HttpClient _http;\\n"
        "    private readonly string _baseUrl;\\n\\n"
        "    public SdkClient(string baseUrl)\\n"
        "    {\\n"
        "        _baseUrl = baseUrl.TrimEnd('/');\\n"
        "        _http = new HttpClient();\\n"
        "    }\\n\\n"
        "    public string Invoke(string module, string function, params string[] args)\\n"
        "    {\\n"
        "        var payload = JsonSerializer.Serialize(new\\n"
        "        {\\n"
        "            module = module,\\n"
        "            function = function,\\n"
        "            args = args\\n"
        "        });\\n"
        "        var content = new StringContent(payload, Encoding.UTF8, \"application/json\");\\n"
        "        var response = _http.PostAsync($\"{_baseUrl}/v1/invoke\", content).Result;\\n"
        "        if (!response.IsSuccessStatusCode)\\n"
        "        {\\n"
        "            throw new Exception($\"Invocation failed: {response.StatusCode}\");\\n"
        "        }\\n"
        "        return response.Content.ReadAsStringAsync().Result;\\n"
        "    }\\n\\n"
        "    public string Health()\\n"
        "    {\\n"
        "        var response = _http.GetAsync($\"{_baseUrl}/health\").Result;\\n"
        "        if (!response.IsSuccessStatusCode)\\n"
        "        {\\n"
        "            throw new Exception($\"Health check failed: {response.StatusCode}\");\\n"
        "        }\\n"
        "        return response.Content.ReadAsStringAsync().Result;\\n"
        "    }\\n"
        "}\\n",
        encoding="utf-8",
    )
    (root / "pealang.csproj").write_text(
        "<Project Sdk=\"Microsoft.NET.Sdk\">\\n"
        "  <PropertyGroup>\\n"
        "    <OutputType>Exe</OutputType>\\n"
        "    <TargetFramework>net8.0</TargetFramework>\\n"
        "    <ImplicitUsings>enable</ImplicitUsings>\\n"
        "    <Nullable>enable</Nullable>\\n"
        "    <RootNamespace>PeaLang</RootNamespace>\\n"
        "    <AssemblyName>pealang-csharp-sdk</AssemblyName>\\n"
        "    <PealangSdkVersion>2.25.0</PealangSdkVersion>\\n"
        "  </PropertyGroup>\\n\\n"
        "  <ItemGroup>\\n"
        "    <PackageReference Include=\"System.Text.Json\" Version=\"8.0.0\" />\\n"
        "  </ItemGroup>\\n"
        "</Project>\\n",
        encoding="utf-8",
    )
    (root / "appsettings.json").write_text(
        "{\\n"
        "  \"PeaLang\": {\\n"
        "    \"BaseUrl\": \"http://localhost:8080\"\\n"
        "  }\\n"
        "}\\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "# PeaLang C# SDK\\n\\n.NET client for PeaLang runtime.\\n",
        encoding="utf-8",
    )
    return {
        "root": str(root),
        "files": [
            "pealang/SdkClient.cs",
            "pealang.csproj",
            "appsettings.json",
            "README.md",
        ],
    }


def scaffold_rust_sdk(target_dir: str = "rust-sdk") -> dict[str, Any]:
    """Scaffold a Rust host SDK directory structure.

    Generates a Rust starter project with a PeaLang runtime connector,
    main client, configuration, and build configuration.
    """
    root = Path(target_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src" / "main.rs").write_text(
        "use reqwest::Client;\\n"
        "use serde::{Serialize, Deserialize};\\n\\n"
        "#[derive(Serialize)]\\n"
        "struct InvokeRequest {\\n"
        "    module: String,\\n"
        "    function: String,\\n"
        "    args: Vec<String>,\\n"
        "}\\n\\n"
        "pub struct SdkClient {\\n"
        "    client: Client,\\n"
        "    base_url: String,\\n"
        "}\\n\\n"
        "impl SdkClient {\\n"
        "    pub fn new(base_url: &str) -> Self {\\n"
        "        SdkClient {\\n"
        "            client: Client::new(),\\n"
        "            base_url: base_url.trim_end_matches('/').to_string(),\\n"
        "        }\\n"
        "    }\\n\\n"
        "    pub async fn invoke(&self, module: &str, function: &str, args: Vec<String>) -> Result<String, reqwest::Error> {\\n"
        "        let payload = InvokeRequest {\\n"
        "            module: module.to_string(),\\n"
        "            function: function.to_string(),\\n"
        "            args,\\n"
        "        };\\n"
        "        let response = self.client\\n"
        "            .post(&format!(\"{}/v1/invoke\", self.base_url))\\n"
        "            .json(&payload)\\n"
        "            .send()\\n"
        "            .await?;\\n"
        "        if !response.status().is_success() {\\n"
        "            return Err(reqwest::Error::status(response.status()));\\n"
        "        }\\n"
        "        response.text().await\\n"
        "    }\\n\\n"
        "    pub async fn health(&self) -> Result<String, reqwest::Error> {\\n"
        "        let response = self.client\\n"
        "            .get(&format!(\"{}/health\", self.base_url))\\n"
        "            .send()\\n"
        "            .await?;\\n"
        "        if !response.status().is_success() {\\n"
        "            return Err(reqwest::Error::status(response.status()));\\n"
        "        }\\n"
        "        response.text().await\\n"
        "    }\\n"
        "}\\n",
        encoding="utf-8",
    )
    (root / "Cargo.toml").write_text(
        "[package]\\n"
        "name = \"pealang-rust-sdk\"\\n"
        "version = \"1.0.0\"\\n"
        "edition = \"2021\"\\n\\n"
        "[dependencies]\\n"
        "reqwest = { version = \"0.11\", features = [\"json\"] }\\n"
        "serde = { version = \"1.0\", features = [\"derive\"] }\\n"
        "tokio = { version = \"1\", features = [\"full\"] }\\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "# PeaLang Rust SDK\\n\\nRust client for PeaLang runtime.\\n",
        encoding="utf-8",
    )
    return {
        "root": str(root),
        "files": [
            "src/main.rs",
            "Cargo.toml",
            "README.md",
        ],
    }


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


def build_host_sdk_namespace() -> dict[str, Any]:
    """Expose all host SDK scaffolding functions in a single namespace."""
    return {
        "scaffold_node_sdk": scaffold_node_sdk,
        "scaffold_go_sdk": scaffold_go_sdk,
        "scaffold_python_sdk": scaffold_python_sdk,
        "scaffold_browser_sdk": scaffold_browser_sdk,
        "scaffold_java_sdk": scaffold_java_sdk,
        "scaffold_csharp_sdk": scaffold_csharp_sdk,
        "scaffold_rust_sdk": scaffold_rust_sdk,
    }


# Map of SDK name to scaffold function for CLI discovery.
HOST_SDK_NAMES = {
    "node": scaffold_node_sdk,
    "go": scaffold_go_sdk,
    "python": scaffold_python_sdk,
    "browser": scaffold_browser_sdk,
    "java": scaffold_java_sdk,
    "csharp": scaffold_csharp_sdk,
    "rust": scaffold_rust_sdk,
}
