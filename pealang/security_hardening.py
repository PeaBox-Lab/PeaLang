"""PeaLang v0.78 security hardening primitives.

Small, dependency-free controls intended for hosts embedding PeaLang. They do not
replace the existing VM sandbox; they provide reusable validation/redaction at
trust boundaries before work reaches the runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import hmac, hashlib, ipaddress, json, re
from urllib.parse import urlparse

_SECRET_KEYS = re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|authorization|cookie)")
_BEARER = re.compile(r"(?i)\b(Bearer\s+)[A-Za-z0-9._~+\-/=]+")

@dataclass(frozen=True)
class SecurityPolicy:
    max_text_bytes: int = 1_000_000
    max_collection_items: int = 10_000
    allowed_url_schemes: tuple[str, ...] = ("https",)
    block_private_networks: bool = True
    allowed_roots: tuple[str, ...] = ()
    max_path_bytes: int = 4096

class SecurityViolation(ValueError):
    """Raised when a value violates a host security policy."""

class SecurityValidator:
    def __init__(self, policy: SecurityPolicy | None = None): self.policy = policy or SecurityPolicy()
    def text(self, value: str) -> str:
        if len(value.encode("utf-8")) > self.policy.max_text_bytes: raise SecurityViolation("text size limit exceeded")
        return value
    def collection(self, value):
        if len(value) > self.policy.max_collection_items: raise SecurityViolation("collection item limit exceeded")
        return value
    def path(self, value: str | Path) -> Path:
        raw=str(value)
        if len(raw.encode()) > self.policy.max_path_bytes: raise SecurityViolation("path size limit exceeded")
        p=Path(raw).expanduser().resolve()
        if self.policy.allowed_roots:
            roots=[Path(r).expanduser().resolve() for r in self.policy.allowed_roots]
            if not any(p == r or r in p.parents for r in roots): raise SecurityViolation("path is outside allowed roots")
        return p
    def url(self, value: str) -> str:
        u=urlparse(value)
        if u.scheme.lower() not in self.policy.allowed_url_schemes: raise SecurityViolation("URL scheme is not allowed")
        if not u.hostname: raise SecurityViolation("URL hostname is required")
        host=u.hostname.lower()
        if self.policy.block_private_networks:
            if host in {"localhost","localhost.localdomain"} or host.endswith(".localhost"): raise SecurityViolation("private network target blocked")
            try:
                a=ipaddress.ip_address(host)
            except ValueError:
                a=None
            if a is not None and (a.is_private or a.is_loopback or a.is_link_local or a.is_reserved or a.is_multicast or a.is_unspecified):
                raise SecurityViolation("private network target blocked")
        return value

def redact_secrets(value, replacement="[REDACTED]"):
    """Recursively redact common credential fields and bearer tokens."""
    if isinstance(value, dict):
        return {k:(replacement if _SECRET_KEYS.search(str(k)) else redact_secrets(v,replacement)) for k,v in value.items()}
    if isinstance(value, list): return [redact_secrets(v,replacement) for v in value]
    if isinstance(value, tuple): return tuple(redact_secrets(v,replacement) for v in value)
    if isinstance(value, str): return _BEARER.sub(lambda m:m.group(1)+replacement,value)
    return value

@dataclass
class SignedAuditChain:
    """Append-only hash chain with optional HMAC authentication."""
    key: bytes | None = None
    entries: list[dict] = field(default_factory=list)
    def append(self, event: dict) -> dict:
        clean=redact_secrets(event)
        previous=self.entries[-1]["digest"] if self.entries else ""
        payload=json.dumps(clean,sort_keys=True,separators=(",",":"),default=str)
        raw=(previous+"\n"+payload).encode()
        digest=hmac.new(self.key,raw,hashlib.sha256).hexdigest() if self.key else hashlib.sha256(raw).hexdigest()
        row={"sequence":len(self.entries)+1,"previous":previous,"event":clean,"digest":digest}
        self.entries.append(row); return row
    def verify(self) -> bool:
        previous=""
        for n,row in enumerate(self.entries,1):
            if row.get("sequence") != n or row.get("previous") != previous: return False
            payload=json.dumps(row.get("event"),sort_keys=True,separators=(",",":"),default=str)
            raw=(previous+"\n"+payload).encode()
            expected=hmac.new(self.key,raw,hashlib.sha256).hexdigest() if self.key else hashlib.sha256(raw).hexdigest()
            if not hmac.compare_digest(expected,str(row.get("digest",""))): return False
            previous=expected
        return True
