"""Regression coverage for v1.5.0 web SDK."""

from pealang.web_sdk import (
    build_web_sdk_namespace,
    generate_typescript_client,
    sse_endpoint_source,
    websocket_handler_source,
    jwt_middleware_source,
    rate_limiter_source,
    api_versioning_source,
)


def test_generate_typescript_client():
    routes = [
        {"method": "GET", "path": "/users", "name": "getUsers", "params": []},
        {"method": "POST", "path": "/users", "name": "createUser", "params": [{"name": "name", "type": "string"}]},
    ]
    client = generate_typescript_client(routes, "http://localhost:8000", "MyClient")
    assert "PEA_BASE_URL" in client
    assert "getUsers" in client
    assert "createUser" in client
    assert "peaFetch" in client
    assert "peaSSE" in client
    assert "peaWebSocket" in client


def test_sse_endpoint_source():
    src = sse_endpoint_source()
    assert "text/event-stream" in src
    assert "setInterval" in src


def test_websocket_handler_source():
    src = websocket_handler_source()
    assert "WebSocket" in src
    assert "connection" in src


def test_jwt_middleware_source():
    src = jwt_middleware_source()
    assert "Bearer" in src
    assert "401" in src


def test_rate_limiter_source():
    src = rate_limiter_source()
    assert "429" in src
    assert "maxRequests" in src


def test_api_versioning_source():
    src = api_versioning_source()
    assert "version" in src.lower()
    assert "Unsupported" in src


def test_build_web_sdk_namespace():
    ns = build_web_sdk_namespace()
    assert "generate_typescript_client" in ns
    assert "sse_endpoint_source" in ns
    assert "websocket_handler_source" in ns
    assert "jwt_middleware_source" in ns
    assert "rate_limiter_source" in ns
    assert "api_versioning_source" in ns
    assert len(ns) == 6
