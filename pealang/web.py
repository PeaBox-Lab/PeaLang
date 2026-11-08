"""Lightweight web application toolkit for PeaLang.

This module provides a small, dependency-free web framework that can be used
directly from Python and from PeaLang programs through the ``web`` namespace.
It is designed for prototypes, dashboards, rule services, data apps, and
embeddable PeaLang extensions.
"""

from __future__ import annotations

import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from .errors import PeaError

_CURRENT_INTERPRETER = None


def set_current_interpreter(interpreter):
    global _CURRENT_INTERPRETER
    _CURRENT_INTERPRETER = interpreter


class WebResponse:
    def __init__(self, body: Any = "", status: int = 200, headers: dict[str, str] | None = None,
                 content_type: str | None = None):
        self.status = int(status)
        self.headers = dict(headers or {})
        self.body = body
        if content_type:
            self.headers.setdefault("Content-Type", content_type)

    def to_bytes(self) -> bytes:
        if isinstance(self.body, (bytes, bytearray)):
            return bytes(self.body)
        if isinstance(self.body, str):
            return self.body.encode("utf-8")
        return json.dumps(self.body, ensure_ascii=False, default=str).encode("utf-8")

    def content_type(self) -> str:
        return self.headers.get("Content-Type", "text/plain; charset=utf-8")

    def __getitem__(self, key):
        if key == "status":
            return self.status
        if key == "body":
            return self.body if isinstance(self.body, str) else self.to_bytes().decode("utf-8", "replace")
        if key == "headers":
            return self.headers
        raise KeyError(key)

    def __repr__(self):
        return f"WebResponse(status={self.status})"


def json_response(value: Any, status: int = 200, headers: dict[str, str] | None = None) -> WebResponse:
    h = {"Content-Type": "application/json; charset=utf-8"}
    h.update(headers or {})
    return WebResponse(value, status=status, headers=h)


def html_response(value: Any, status: int = 200, headers: dict[str, str] | None = None) -> WebResponse:
    h = {"Content-Type": "text/html; charset=utf-8"}
    h.update(headers or {})
    return WebResponse(value, status=status, headers=h)


def text_response(value: Any, status: int = 200, headers: dict[str, str] | None = None) -> WebResponse:
    h = {"Content-Type": "text/plain; charset=utf-8"}
    h.update(headers or {})
    return WebResponse(value, status=status, headers=h)


def redirect(location: str, status: int = 302, headers: dict[str, str] | None = None) -> WebResponse:
    h = {"Location": str(location)}
    h.update(headers or {})
    return WebResponse("", status=status, headers=h)


def error_response(message: str, status: int = 400, headers: dict[str, str] | None = None) -> WebResponse:
    return json_response({"error": str(message)}, status=status, headers=headers)


def normalize_response(result: Any) -> WebResponse:
    if isinstance(result, WebResponse):
        return result
    if isinstance(result, dict):
        if any(k in result for k in ("status", "body", "headers", "content_type")):
            status = result.get("status", 200)
            body = result.get("body", result.get("data", ""))
            headers = result.get("headers", {})
            content_type = result.get("content_type")
            if content_type:
                headers = dict(headers or {})
                headers.setdefault("Content-Type", content_type)
            return WebResponse(body, status=status, headers=headers)
        return json_response(result)
    if isinstance(result, (list, tuple)):
        return json_response(list(result))
    if isinstance(result, str):
        return text_response(result)
    if result is None:
        return WebResponse("", status=204)
    return text_response(str(result))


class WebRequest:
    def __init__(self, method: str, path: str, headers: dict[str, str] | None = None,
                 query: dict[str, Any] | None = None, body: str = "", remote_addr: str = "",
                 params: dict[str, Any] | None = None):
        self.method = method.upper()
        self.path = path
        self.headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
        self.query = query or {}
        self.body = body
        self.remote_addr = remote_addr
        self.params = params or {}
        self._json = None
        self._parsed_json = False

    def json(self) -> Any:
        if not self._parsed_json:
            self._parsed_json = True
            try:
                self._json = json.loads(self.body) if self.body else None
            except Exception:
                self._json = None
        return self._json

    def form(self) -> dict[str, str]:
        parsed = urllib.parse.parse_qs(self.body, keep_blank_values=True)
        return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}

    @property
    def cookies(self) -> dict[str, str]:
        raw = self.headers.get("cookie", "")
        out = {}
        for part in raw.split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                out[k.strip()] = urllib.parse.unquote(v.strip())
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "path": self.path,
            "headers": dict(self.headers),
            "query": dict(self.query),
            "params": dict(self.params),
            "cookies": self.cookies,
            "body": self.body,
            "json": self.json(),
            "remote_addr": self.remote_addr,
        }


class PeaWebApp:
    def __init__(self, interpreter: Any = None):
        if interpreter is None:
            interpreter = _CURRENT_INTERPRETER
        self.interpreter = interpreter
        self.routes: dict[tuple[str, str], Any] = {}
        self.middleware: list[Callable[[WebRequest], WebRequest | None]] = []
        self.static: dict[str, str] = {}
        self.not_found_handler: Any = None
        self.error_handler: Any = None
        self._server: ThreadingHTTPServer | None = None
        self._lock = threading.RLock()
        self._cors: dict[str,str] | None = None

    def route(self, method: str, path: str, handler: Any) -> "PeaWebApp":
        self.routes[(method.upper(), path)] = handler
        return self

    def get(self, path: str, handler: Any = None):
        if handler is None:
            def decorator(fn):
                self.route("GET", path, fn)
                return fn
            return decorator
        self.route("GET", path, handler)
        return self

    def post(self, path: str, handler: Any = None):
        if handler is None:
            def decorator(fn):
                self.route("POST", path, fn)
                return fn
            return decorator
        self.route("POST", path, handler)
        return self

    def put(self, path: str, handler: Any = None):
        if handler is None:
            def decorator(fn):
                self.route("PUT", path, fn)
                return fn
            return decorator
        self.route("PUT", path, handler)
        return self

    def delete(self, path: str, handler: Any = None):
        if handler is None:
            def decorator(fn):
                self.route("DELETE", path, fn)
                return fn
            return decorator
        self.route("DELETE", path, handler)
        return self

    def patch(self, path: str, handler: Any = None):
        if handler is None:
            def decorator(fn): self.route("PATCH", path, fn); return fn
            return decorator
        self.route("PATCH", path, handler); return self

    def options(self, path: str, handler: Any = None):
        if handler is None:
            def decorator(fn): self.route("OPTIONS", path, fn); return fn
            return decorator
        self.route("OPTIONS", path, handler); return self

    def group(self, prefix: str):
        app = self
        prefix = prefix.rstrip('/')
        class Group:
            def _p(self, path): return prefix + '/' + path.lstrip('/')
            def route(self, method, path, handler): app.route(method, self._p(path), handler); return self
            def get(self, path, handler=None):
                if handler is None: return lambda fn: self.route('GET', path, fn)
                return self.route('GET', path, handler)
            def post(self, path, handler=None):
                if handler is None: return lambda fn: self.route('POST', path, fn)
                return self.route('POST', path, handler)
            def put(self, path, handler=None):
                if handler is None: return lambda fn: self.route('PUT', path, fn)
                return self.route('PUT', path, handler)
            def delete(self, path, handler=None):
                if handler is None: return lambda fn: self.route('DELETE', path, fn)
                return self.route('DELETE', path, handler)
            def patch(self, path, handler=None):
                if handler is None: return lambda fn: self.route('PATCH', path, fn)
                return self.route('PATCH', path, handler)
        return Group()

    def use(self, middleware: Callable[[WebRequest], WebRequest | None]) -> "PeaWebApp":
        self.middleware.append(middleware)
        return self

    def add_static(self, prefix: str, directory: str) -> "PeaWebApp":
        self.static[prefix.rstrip("/") + "/"] = str(directory)
        return self

    def enable_cors(self, origins: str = "*", methods: str = "GET,POST,PUT,DELETE,OPTIONS,PATCH",
                    headers: str = "Content-Type,Authorization") -> "PeaWebApp":
        self._cors = {"origins": origins, "methods": methods, "headers": headers}
        return self

    def not_found(self, handler) -> "PeaWebApp":
        self.not_found_handler = handler
        return self

    def on_error(self, handler) -> "PeaWebApp":
        self.error_handler = handler
        return self

    def openapi(self, title: str = "PeaLang App", version: str = "1.0.0") -> dict[str, Any]:
        paths = {}
        for (method, path), _ in self.routes.items():
            openapi_path = path
            params = []
            import re
            for m in re.finditer(r"\{([^}]+)\}|:([A-Za-z_]\w*)", path):
                name = m.group(1) or m.group(2)
                openapi_path = openapi_path.replace(m.group(0), "{" + name + "}")
                params.append({"name": name, "in": "path", "required": True, "schema": {"type": "string"}})
            paths.setdefault(openapi_path, {})[method.lower()] = {
                "summary": f"{method} {openapi_path}",
                "responses": {"200": {"description": "Successful response"}},
                **({"parameters": params} if params else {}),
            }
        return {
            "openapi": "3.0.3",
            "info": {"title": title, "version": version},
            "paths": paths,
        }

    def _match_route(self, method: str, path: str):
        if (method, path) in self.routes:
            return self.routes[(method, path)], {}
        # Simple path parameters: /users/{id}
        for (route_method, route_path), handler in self.routes.items():
            if route_method != method:
                continue
            params = _match_path(route_path, path)
            if params is not None:
                return handler, params
        return None, None

    def _invoke(self, handler: Any, request: WebRequest) -> Any:
        req_dict = request.to_dict()
        if self.interpreter is not None and hasattr(self.interpreter, "invoke_user_function"):
            try:
                from .interpreter import UserFunction
                if isinstance(handler, UserFunction):
                    return self.interpreter.invoke_user_function(handler, [req_dict])
            except Exception:
                pass
        if callable(handler):
            return handler(req_dict)
        raise PeaError(f"Route handler is not callable: {type(handler).__name__}: {handler!r}")

    def _apply_cors(self, response: WebResponse) -> WebResponse:
        if self._cors:
            response.headers.setdefault('Access-Control-Allow-Origin', self._cors.get('origins', '*'))
            response.headers.setdefault('Access-Control-Allow-Methods', self._cors.get('methods', 'GET,POST,PUT,DELETE,OPTIONS,PATCH'))
            response.headers.setdefault('Access-Control-Allow-Headers', self._cors.get('headers', 'Content-Type,Authorization'))
        return response

    def dispatch(self, method: str, path: str, headers: dict[str, str] | None = None,
                 body: str = "", remote_addr: str = "") -> WebResponse:
        parsed = urllib.parse.urlsplit(path)
        route_path = parsed.path or "/"
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        query = {k: (v[0] if len(v) == 1 else v) for k, v in query.items()}
        request = WebRequest(method, route_path, headers=headers, query=query, body=body, remote_addr=remote_addr)
        with self._lock:
            if request.method == 'OPTIONS' and self._cors and (request.method, route_path) not in self.routes:
                return self._apply_cors(WebResponse('', status=204))
            for middleware in self.middleware:
                try:
                    updated = middleware(request)
                    if updated is not None:
                        request = updated
                except Exception as exc:
                    return self._apply_cors(error_response(str(exc), status=500))
            handler, params = self._match_route(request.method, route_path)
            if params:
                request.params = params
                request.query = {**params, **request.query}
            if handler is None:
                for prefix, directory in self.static.items():
                    if route_path.startswith(prefix):
                        rel = route_path[len(prefix):]
                        file_path = Path(directory) / rel
                        try:
                            if file_path.is_file():
                                content_type = _guess_content_type(file_path)
                                return self._apply_cors(WebResponse(file_path.read_bytes(), status=200,
                                                  headers={"Content-Type": content_type}))
                        except Exception as exc:
                            return self._apply_cors(error_response(str(exc), status=500))
                if self.not_found_handler is not None:
                    try:
                        return self._apply_cors(normalize_response(self._invoke(self.not_found_handler, request)))
                    except Exception as exc:
                        return self._apply_cors(error_response(str(exc), status=500))
                return self._apply_cors(error_response("Not found", status=404))
            try:
                result = self._invoke(handler, request)
                return self._apply_cors(normalize_response(result))
            except Exception as exc:
                if self.error_handler is not None:
                    try:
                        return self._apply_cors(normalize_response(self._invoke(self.error_handler, request)))
                    except Exception:
                        pass
                return self._apply_cors(error_response(str(exc), status=500))

    def serve(self, host: str = "127.0.0.1", port: int = 8000, background: bool = False) -> ThreadingHTTPServer | None:
        app = self

        class Handler(BaseHTTPRequestHandler):
            def _handle(self, method: str):
                length = int(self.headers.get("Content-Length", "0") or "0")
                body = self.rfile.read(length).decode("utf-8", "replace") if length else ""
                response = app.dispatch(method, self.path, headers=dict(self.headers.items()), body=body,
                                       remote_addr=self.client_address[0])
                data = response.to_bytes()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    self.send_header(key, str(value))
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(data)

            def do_GET(self): self._handle("GET")
            def do_POST(self): self._handle("POST")
            def do_PUT(self): self._handle("PUT")
            def do_DELETE(self): self._handle("DELETE")
            def do_PATCH(self): self._handle("PATCH")
            def do_HEAD(self): self._handle("HEAD")
            def log_message(self, *args):  # quiet by default
                return

        server = ThreadingHTTPServer((host, port), Handler)
        self._server = server
        if background:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            return server
        server.serve_forever()
        return None

    def stop(self) -> None:
        if self._server is not None:
            try:
                self._server.shutdown()
            except Exception:
                pass
            self._server = None


def _match_path(route_path: str, actual_path: str) -> dict[str, str] | None:
    route_parts = route_path.strip("/").split("/") if route_path not in ("", "/") else []
    actual_parts = actual_path.strip("/").split("/") if actual_path not in ("", "/") else []
    if len(route_parts) != len(actual_parts):
        return None
    params: dict[str, str] = {}
    for rp, ap in zip(route_parts, actual_parts):
        if rp.startswith("{") and rp.endswith("}"):
            params[rp[1:-1]] = urllib.parse.unquote(ap)
        elif rp.startswith(":"):
            params[rp[1:]] = urllib.parse.unquote(ap)
        elif rp != ap:
            return None
    return params


def _guess_content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    mapping = {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
        ".txt": "text/plain; charset=utf-8",
    }
    return mapping.get(suffix, "application/octet-stream")


def render_template(template: str, context: dict[str, Any] | None = None) -> str:
    context = context or {}
    result = str(template)
    for key, value in context.items():
        result = result.replace("{{" + str(key) + "}}", str(value))
    return result


def set_cookie(response: WebResponse, name: str, value: str, max_age: int | None = None,
               path: str = "/", http_only: bool = True) -> WebResponse:
    cookie = f"{name}={urllib.parse.quote(str(value))}; Path={path}"
    if max_age is not None:
        cookie += f"; Max-Age={int(max_age)}"
    if http_only:
        cookie += "; HttpOnly"
    response.headers["Set-Cookie"] = cookie
    return response


def file_response(path: str, status: int = 200) -> WebResponse:
    p = Path(path)
    return WebResponse(p.read_bytes() if p.exists() else b"", status=status if p.exists() else 404,
                       headers={"Content-Type": _guess_content_type(p)})


def sse_response(data: Any) -> WebResponse:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, default=str)
    body = "data: " + payload.replace("\n", "\ndata: ") + "\n\n"
    return WebResponse(body, headers={"Content-Type": "text/event-stream; charset=utf-8", "Cache-Control": "no-cache"})


def validate(data: Any, schema: dict[str, Any]) -> dict[str, Any]:
    errors = []
    if not isinstance(data, dict):
        return {"ok": False, "errors": ["data must be an object"]}
    for field, rule in (schema or {}).items():
        required = True
        typ = rule
        if isinstance(rule, dict):
            required = rule.get("required", True)
            typ = rule.get("type", "any")
        val = data.get(field)
        if val is None or val == "":
            if required:
                errors.append(f"missing required field: {field}")
            continue
        checks = {
            "string": lambda v: isinstance(v, str),
            "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "bool": lambda v: isinstance(v, bool),
            "list": lambda v: isinstance(v, list),
            "object": lambda v: isinstance(v, dict),
            "any": lambda v: True,
        }
        if not checks.get(str(typ), checks["any"])(val):
            errors.append(f"field {field} must be {typ}")
    return {"ok": len(errors) == 0, "errors": errors, "data": data}


def rate_limit_middleware(limit: int = 60, window_seconds: int = 60):
    import time as _time
    hits = {}
    def mw(request):
        key = getattr(request, 'remote_addr', '') or request.headers.get('x-forwarded-for', 'anon')
        now = _time.time()
        bucket = [t for t in hits.get(key, []) if now - t < window_seconds]
        if len(bucket) >= limit:
            raise Exception(f"Rate limit exceeded ({limit}/{window_seconds}s)")
        bucket.append(now)
        hits[key] = bucket
        return request
    return mw


def bearer_auth(header: str = "authorization", prefix: str = "Bearer "):
    def get_token(request):
        h = request.headers.get(header.lower(), "")
        return h[len(prefix):].strip() if h.startswith(prefix) else None
    return get_token


def build_web_namespace(interpreter: Any) -> dict[str, Any]:
    def app():
        return PeaWebApp(interpreter if interpreter is not None else _CURRENT_INTERPRETER)

    def parse_json(text):
        try:
            return json.loads(text)
        except Exception:
            return None

    return {
        "app": app,
        "json": json_response,
        "html": html_response,
        "text": text_response,
        "redirect": redirect,
        "error": error_response,
        "file": file_response,
        "sse": sse_response,
        "response": lambda body="", status=200, headers=None, content_type=None: WebResponse(body, status=status, headers=headers, content_type=content_type),
        "parse_json": parse_json,
        "render_template": render_template,
        "set_cookie": set_cookie,
        "validate": validate,
        "rate_limit": rate_limit_middleware,
        "bearer_auth": bearer_auth,
        "openapi": lambda app_obj, title="PeaLang App", version="1.0.0": app_obj.openapi(title, version),
        "serve": lambda app_obj, host="127.0.0.1", port=8000: app_obj.serve(host, port),
    }
