

# Security Hardening Help

```python
from pealang import SecurityPolicy, SecurityValidator, redact_secrets, SignedAuditChain
v = SecurityValidator(SecurityPolicy(allowed_roots=("./workspace",)))
v.url("https://example.com/data")
safe = redact_secrets({"api_key": "secret", "message": "ok"})
audit = SignedAuditChain(key=b"application-managed-key")
audit.append({"action": "query", "token": "secret"})
assert audit.verify()
```

Use application-managed secret storage for HMAC keys. Treat URL validation as one layer; production HTTP transports should also validate resolved IP addresses and redirects.


