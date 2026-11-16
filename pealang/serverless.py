"""Serverless and cross-compilation support for PeaLang (v2.8.0).

Provides:
- Lambda function adaptation
- Vercel/Edge runtime stub
- Cross-compilation targets
- Deployment helpers
"""

from __future__ import annotations

import json
import base64
import hashlib
import time
import threading
from collections import defaultdict, OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# ---------------------------------------------------------------------------
# Lambda Adaptation
# ---------------------------------------------------------------------------

class LambdaHandler:
    """Adapt a PeaLang program as an AWS Lambda handler.

    The handler function signature expected by AWS Lambda:
        handler(event, context) -> dict
    """
    def __init__(self, source: str, output: callable | None = None):
        self.source = source
        self.output = output or (lambda x: None)
        self._env: dict[str, Any] = {}
        self._pc: int = 0
        self._breakpoints: set[int] = set()
        self._running: bool = False
        self._vars: dict[str, Any] = {}
        self._last_reason: str = "end"

    def handle(self, event: dict[str, Any], context: Any | None = None) -> dict[str, Any]:
        """Execute the PeaLang program as a Lambda handler.

        *event* contains the HTTP request or trigger data.
        *context* contains runtime information.

        Returns a dict with at least 'statusCode' and 'body'.
        """
        # Reset state
        self._env = {}
        self._pc = 0
        self._vars = {}
        self._last_reason = "end"
        self._running = True

        # Extract payload from event (supports API Gateway format)
        body = event.get("body", "{}")
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        if isinstance(body, dict):
            body = json.dumps(body)

        try:
            # Very simple: parse the body as a PeaLang let expression
            # or just return a stub response
            # In production would compile and execute the PeaLang source
            # with the event data as input
            result = self._execute_stub(body)
        except Exception as e:
            result = {"error": str(e)}

        # Build Lambda response
        return {
            "statusCode": 200 if not result.get("error") else 500,
            "body": json.dumps(result),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    def _execute_stub(self, body: str) -> dict[str, Any]:
        """Stub execution: parse simple PeaLang and return result.

        Supports: let x = value; x
        """
        import re
        # Try to extract a variable assignment
        m = re.match(r"^\s*let\s+(\w+)\s*=\s*(.+)", body)
        if m:
            name = m.group(1)
            val = m.group(2).strip()
            try:
                if val.isdigit():
                    self._env[name] = int(val)
                else:
                    self._env[name] = val
                self._vars[name] = self._env[name]
                return self._vars
            except Exception:
                pass
        # Default: return the body as-is (for HTTP passthrough)
        return {"received": body}


class LambdaRuntime:
    """Runtime environment for Lambda adaptation."""

    def __init__(self, handler: LambdaHandler):
        self.handler = handler
        self.initialized = False

    def initialize(self) -> dict:
        """Return the initialization response."""
        self.initialized = True
        return {
            "isInitialized": True,
            "callback": None,
        }

    # --- Lambda core hooks ---

    def invoke(self, event: dict[str, Any], context: Any | None = None) -> dict[str, Any]:
        """Invoke the handler with *event* and *context*."""
        return self.handler.handle(event, context)

    # --- (Optional) CloudWatch metrics, etc. ---

# ---------------------------------------------------------------------------
# Vercel/Edge Adaptation
# ---------------------------------------------------------------------------

class VercelHandler:
    """Adapt a PeaLang program as a Vercel Edge Function."""

    def __init__(self, source: str, output: callable | None = None):
        self.source = source
        self.output = output or (lambda x: None)
        self._env: dict[str, Any] = {}
        self._pc: int = 0

    def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a Vercel edge request.

        *request* contains: method, path, query, headers, body
        Returns a Vercel-compatible response.
        """
        method = request.get("method", "GET")
        path = request.get("path", "/")
        headers = request.get("headers", {})
        body = request.get("body", "")

        # Very stub: route based on path
        if path == "/health":
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "text/plain"},
                "body": "OK",
            }
        elif path == "/echo":
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"echo": body}),
            }
        else:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "text/plain"},
                "body": "Not Found",
            }


# ---------------------------------------------------------------------------
# Cross-Compilation Targets
# ---------------------------------------------------------------------------

class CompilationTarget:
    """Abstract base for cross-compilation targets."""

    def compile(self, source: str) -> bytes:
        """Compile *source* PeaLang code to the target format.

        Returns compiled bytecode or representation.
        """
        raise NotImplementedError

    def execute(self, code: bytes) -> Any:
        """Execute compiled *code*.

        Returns the result of execution.
        """
        raise NotImplementedError


class WebAssemblyTarget(CompilationTarget):
    """Compile PeaLang to WebAssembly text format (stub)."""

    def compile(self, source: str) -> bytes:
        # Stub: in production would use a Wasm compiler backend
        # For now, return a Wasm module marker
        wasm_marker = b"\x00asm"
        payload = source.encode("utf-8")
        return wasm_marker + len(payload).to_bytes(4, "big") + payload

    def execute(self, code: bytes) -> Any:
        # Stub: would instantiate a Wasm engine
        return {"wasm_exec": True, "code_len": len(code)}


class PythonTarget(CompilationTarget):
    """Compile PeaLang to Python source (stub)."""

    def compile(self, source: str) -> str:
        # Stub: translate PeaLang syntax to equivalent Python
        # For now, just wrap in a Python function template
        return f"def pea_main():\n    # Compiled from PeaLang\n    {source}\n\nif __name__ == \"__main__\":\n    pea_main()"

    def execute(self, source: str) -> Any:
        # Intentionally unimplemented: compiling to Python is a stub in this
        # release and no code is ever executed here. Implementing execution
        # would require a sandboxed Python runtime, which does not exist yet.
        raise NotImplementedError("PythonTarget.execute requires a sandboxed Python runtime that is not implemented in this release")


# ---------------------------------------------------------------------------
# Deployment Helpers
# ---------------------------------------------------------------------------

def deploy_lambda(function_name: str, handler: LambdaHandler, role_arn: str | None = None) -> dict:
    """Deploy a Lambda handler.

    Stub: in production would use boto3/awslambda.
    """
    return {
        "functionName": function_name,
        "handler": "pealang_handler.handle",
        "runtime": "python3.12",
        "role": role_arn or "arn:aws:iam::123456789012:role/lambda-role",
        "status": "deployed",
    }


def deploy_vercel(entrypoint: str, alias: str | None = None) -> dict:
    """Deploy a Vercel edge function.

    Stub: in production would use the Vercel API.
    """
    return {
        "entrypoint": entrypoint,
        "alias": alias or "preview",
        "status": "deployed",
    }


# ---------------------------------------------------------------------------
# Namespace exporter
# ---------------------------------------------------------------------------

def build_serverless_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis/stats/numerics."""
    return {
        "LambdaHandler": LambdaHandler,
        "LambdaRuntime": LambdaRuntime,
        "VercelHandler": VercelHandler,
        "CompilationTarget": CompilationTarget,
        "WebAssemblyTarget": WebAssemblyTarget,
        "PythonTarget": PythonTarget,
        "deploy_lambda": deploy_lambda,
        "deploy_vercel": deploy_vercel,
        "build_serverless_namespace": build_serverless_namespace,
    }
