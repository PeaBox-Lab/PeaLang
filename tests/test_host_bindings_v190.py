"""Regression coverage for v1.9.0 host bindings."""

import json
import tempfile
import os
from pathlib import Path

from pealang.host_bindings import (
    build_host_bindings_namespace,
    register_host_function,
    generate_python_export_decorator as generate_python_export,
    generate_typescript_export,
    generate_java_export,
    scaffold_go_sdk,
    scaffold_node_sdk,
    import_openapi,
    generate_connector_package,
)


def test_register_host_function():
    result = register_host_function("my_func", "mymod", "my_func", ["int", "str"], "float")
    assert result["name"] == "my_func"
    assert result["registered"] is True
    assert result["arg_types"] == ["int", "str"]


def test_generate_python_export():
    src = generate_python_export("add", ["int", "int"], "int")
    assert "pea_export" in src
    assert "add" in src


def test_generate_typescript_export():
    src = generate_typescript_export("multiply", ["number"], "number")
    assert "peaExport" in src
    assert "multiply" in src


def test_generate_java_export():
    src = generate_java_export("compute", ["int"], "double")
    assert "PeaExport" in src
    assert "compute" in src


def test_scaffold_go_sdk():
    with tempfile.TemporaryDirectory() as d:
        result = scaffold_go_sdk(os.path.join(d, "go-sdk"))
        assert "root" in result
        assert "pealang/client.go" in result["files"]
        assert Path(result["root"], "go.mod").exists()


def test_scaffold_node_sdk():
    with tempfile.TemporaryDirectory() as d:
        result = scaffold_node_sdk(os.path.join(d, "node-sdk"))
        assert "root" in result
        assert "src/index.ts" in result["files"]
        assert Path(result["root"], "package.json").exists()


def test_import_openapi():
    spec = {
        "info": {"title": "Test API", "version": "1.0"},
        "servers": [{"url": "http://localhost:8000"}],
        "paths": {
            "/users": {
                "get": {"operationId": "getUsers", "summary": "Get users", "responses": {"200": {}}},
                "post": {"operationId": "createUser", "summary": "Create user", "responses": {"201": {}}},
            }
        }
    }
    result = import_openapi(spec)
    assert result["title"] == "Test API"
    assert result["count"] == 2
    assert result["base_url"] == "http://localhost:8000"


def test_generate_connector_package():
    imported = {
        "title": "Test API",
        "version": "1.0",
        "base_url": "http://localhost:8000",
        "connectors": [{"name": "getUsers", "method": "GET", "path": "/users"}],
    }
    pkg = generate_connector_package(imported)
    assert "Test API" in pkg
    assert "getUsers" in pkg
    assert "BASE_URL" in pkg


def test_build_host_bindings_namespace():
    ns = build_host_bindings_namespace()
    assert "register_host_function" in ns
    assert "scaffold_go_sdk" in ns
    assert "import_openapi" in ns
    assert len(ns) == 8
