"""Trusted plugin manifests, capability policy, and verified loading."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import importlib.util
import inspect
import json
import re
import sys
import tempfile
from typing import Any, Dict, Iterable, Tuple

from .errors import PeaError
from .ed25519_signing import PublicTrustStore, default_trust_store_path, verify_ed25519
from .extension_registry import (
    ExtensionFunction,
    ExtensionNamespace,
    ExtensionOperator,
    ExtensionRegistry,
    ExtensionType,
)

PLUGIN_MANIFEST_SCHEMA = "pealang-plugin-v1"
PLUGIN_POLICY_SCHEMA = "pealang-plugin-policy-v1"
DEFAULT_PLUGIN_DIR = ".pealang/plugins"
DEFAULT_PLUGIN_POLICY = ".pealang/plugin-policy.json"

KNOWN_CAPABILITIES = frozenset({
    "language-function",
    "language-type",
    "language-operator",
    "stdlib-namespace",
    "host-callback",
    "filesystem",
    "network",
    "process",
})
DEFAULT_ALLOWED_CAPABILITIES = (
    "language-function",
    "language-type",
    "language-operator",
    "stdlib-namespace",
    "host-callback",
)

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _root(root: str = ".") -> Path:
    return Path(root).resolve()


def _within(root: Path, value: str, label: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        raise PeaError(f"{label} must be relative to the project: {value}")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise PeaError(f"{label} escapes the project root: {value}")
    return resolved


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _string_tuple(value: Any, label: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise PeaError(f"{label} must be a list")
    result = tuple(str(item) for item in value)
    if len(result) != len(set(result)):
        raise PeaError(f"{label} contains duplicates")
    return result


@dataclass
class PluginManifest:
    """Declarative metadata for a trusted local plugin."""

    name: str
    version: str
    module: str
    schema: str = PLUGIN_MANIFEST_SCHEMA
    entry_point: str = "init_plugin"
    description: str = ""
    capabilities: Tuple[str, ...] = ()
    functions: Tuple[str, ...] = ()
    types: Tuple[str, ...] = ()
    operators: Tuple[str, ...] = ()
    namespaces: Tuple[str, ...] = ()
    sha256: str = ""
    signature: str = ""
    key_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        return cls(
            name=str(data.get("name", "")),
            version=str(data.get("version", "")),
            module=str(data.get("module", "")),
            schema=str(data.get("schema", PLUGIN_MANIFEST_SCHEMA)),
            entry_point=str(data.get("entry_point", "init_plugin")),
            description=str(data.get("description", "")),
            capabilities=_string_tuple(data.get("capabilities", []), "capabilities"),
            functions=_string_tuple(data.get("functions", []), "functions"),
            types=_string_tuple(data.get("types", []), "types"),
            operators=_string_tuple(data.get("operators", []), "operators"),
            namespaces=_string_tuple(data.get("namespaces", []), "namespaces"),
            sha256=str(data.get("sha256", "")),
            signature=str(data.get("signature", "")),
            key_id=str(data.get("key_id", "")),
        )


@dataclass
class PluginPolicy:
    """Local trust and capability policy for plugin loading."""

    schema: str = PLUGIN_POLICY_SCHEMA
    allowed_capabilities: Tuple[str, ...] = DEFAULT_ALLOWED_CAPABILITIES
    trusted_key_ids: Tuple[str, ...] = ()
    require_signature: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginPolicy":
        if str(data.get("schema", PLUGIN_POLICY_SCHEMA)) != PLUGIN_POLICY_SCHEMA:
            raise PeaError("Unsupported plugin policy schema")
        allowed = _string_tuple(
            data.get("allowed_capabilities", list(DEFAULT_ALLOWED_CAPABILITIES)),
            "allowed_capabilities",
        )
        unknown = sorted(set(allowed) - KNOWN_CAPABILITIES)
        if unknown:
            raise PeaError(f"Unknown plugin capabilities in policy: {', '.join(unknown)}")
        return cls(
            allowed_capabilities=allowed,
            trusted_key_ids=_string_tuple(data.get("trusted_key_ids", []), "trusted_key_ids"),
            require_signature=bool(data.get("require_signature", False)),
        )


def load_plugin_policy(root: str = ".", policy_path: str | None = None) -> Tuple[PluginPolicy, str | None]:
    """Load policy from an explicit path, project config, or return the default."""
    base = _root(root)
    source = Path(policy_path).resolve() if policy_path else base / ".pealang" / "plugin-policy.json"
    if not source.is_file():
        return PluginPolicy(), None
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except Exception as e:
        raise PeaError(f"Invalid plugin policy JSON: {e}") from e
    return PluginPolicy.from_dict(data), str(source)


def discover_plugins(root: str = ".", plugin_dir: str | None = None) -> list[Path]:
    """Return plugin manifests in deterministic name order."""
    base = _root(root)
    directory = _within(base, plugin_dir or DEFAULT_PLUGIN_DIR, "plugin directory")
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.json"), key=lambda path: path.name)


def _verify_plugin_signature(module_path: Path, signature_path: Path, key_id: str,
                             trust_store: str | None) -> None:
    if not signature_path.is_file():
        raise PeaError(f"Plugin signature not found: {signature_path}")
    try:
        envelope = json.loads(signature_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise PeaError(f"Invalid plugin signature JSON: {e}") from e
    if str(envelope.get("key_id", "")) != key_id:
        raise PeaError("Plugin manifest key ID does not match the signature")

    store = PublicTrustStore(trust_store or default_trust_store_path())
    if key_id in store.data.get("revoked", {}):
        raise PeaError(f"Plugin signing key is revoked: {key_id}")
    key = store.data.get("keys", {}).get(key_id)
    if not key or not key.get("public_key"):
        raise PeaError(f"Plugin signing key is not trusted: {key_id}")

    with tempfile.TemporaryDirectory() as td:
        public_key = Path(td) / "plugin-public.key"
        public_key.write_text(str(key["public_key"]) + "\n", encoding="utf-8")
        verify_ed25519(
            str(module_path), str(signature_path), str(public_key),
            revoked=list(store.data.get("revoked", {})),
        )


def validate_plugin_manifest(manifest_path: str, root: str = ".", *,
                             policy: PluginPolicy | None = None,
                             policy_path: str | None = None,
                             trust_store: str | None = None) -> Dict[str, Any]:
    """Validate a plugin manifest without importing or executing plugin code."""
    base = _root(root)
    path = _within(base, str(manifest_path), "plugin manifest") if not Path(manifest_path).is_absolute() else Path(manifest_path).resolve()
    if not path.is_relative_to(base):
        raise PeaError("Plugin manifest must be inside the project root")
    issues: list[str] = []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        manifest = PluginManifest.from_dict(data)
    except Exception as e:
        raise PeaError(f"Invalid plugin manifest: {e}") from e

    if policy is None:
        policy, policy_source = load_plugin_policy(root, policy_path)
    else:
        policy_source = policy_path

    if manifest.schema != PLUGIN_MANIFEST_SCHEMA:
        issues.append(f"Unsupported manifest schema: {manifest.schema}")
    if not _NAME_RE.fullmatch(manifest.name):
        issues.append(f"Invalid plugin name: {manifest.name}")
    if not _VERSION_RE.fullmatch(manifest.version):
        issues.append(f"Invalid plugin version: {manifest.version}")
    if not manifest.module:
        issues.append("Plugin manifest has no module path")

    unknown = sorted(set(manifest.capabilities) - KNOWN_CAPABILITIES)
    if unknown:
        issues.append(f"Unknown plugin capabilities: {', '.join(unknown)}")
    forbidden = sorted(set(manifest.capabilities) - set(policy.allowed_capabilities))
    if forbidden:
        issues.append(f"Capabilities denied by policy: {', '.join(forbidden)}")

    for label, symbols in (
        ("functions", manifest.functions), ("types", manifest.types),
        ("operators", manifest.operators), ("namespaces", manifest.namespaces),
    ):
        invalid = [name for name in symbols if not _NAME_RE.fullmatch(name)]
        if invalid:
            issues.append(f"Invalid {label}: {', '.join(invalid)}")

    module_path = None
    if manifest.module:
        try:
            module_path = _within(base, manifest.module, "plugin module")
        except PeaError as e:
            issues.append(str(e))
        else:
            if not module_path.is_file():
                issues.append(f"Plugin module not found: {manifest.module}")
            elif manifest.sha256:
                actual = _sha256_file(module_path)
                if actual != manifest.sha256:
                    issues.append(f"Plugin checksum mismatch: expected {manifest.sha256}, got {actual}")
            else:
                issues.append("Plugin manifest has no SHA-256 checksum")

    signature_path = None
    checksum_verified = False
    signature_verified = False
    if module_path is not None and module_path.is_file() and not any("checksum" in item for item in issues):
        checksum_verified = True

    if manifest.signature and not manifest.key_id:
        issues.append("Signed plugin manifest has no key_id")
    if manifest.key_id and not manifest.signature:
        issues.append("Plugin key_id requires a signature")
    if policy.require_signature and not manifest.signature:
        issues.append("Plugin signature required by policy")

    if manifest.signature:
        try:
            signature_path = _within(base, manifest.signature, "plugin signature")
        except PeaError as e:
            issues.append(str(e))
        else:
            if manifest.key_id not in policy.trusted_key_ids:
                issues.append(f"Plugin signing key is not allow-listed by policy: {manifest.key_id}")
            elif checksum_verified:
                try:
                    _verify_plugin_signature(module_path, signature_path, manifest.key_id, trust_store)
                    signature_verified = True
                except Exception as e:
                    issues.append(str(e))

    return {
        "ok": not issues,
        "issues": issues,
        "manifest": str(path),
        "policy_source": policy_source,
        "policy": policy.to_dict(),
        "plugin": manifest.to_dict(),
        "module_path": str(module_path) if module_path else "",
        "signature_path": str(signature_path) if signature_path else "",
        "checksum_verified": checksum_verified,
        "signature_verified": signature_verified,
    }


def scan_plugins(root: str = ".", *, policy: PluginPolicy | None = None,
                 policy_path: str | None = None,
                 trust_store: str | None = None) -> Dict[str, Any]:
    """Report validation status for every discovered plugin manifest."""
    reports = [
        validate_plugin_manifest(str(path), root, policy=policy, policy_path=policy_path, trust_store=trust_store)
        for path in discover_plugins(root)
    ]
    return {
        "ok": all(report["ok"] for report in reports),
        "count": len(reports),
        "plugins": reports,
    }


def _fallback(registry: ExtensionRegistry, container: str, name: str, doc: str) -> None:
    existing = getattr(registry, container)
    if name in existing:
        return
    if container == "functions":
        existing[name] = ExtensionFunction(name, None, doc=doc)
    elif container == "types":
        existing[name] = ExtensionType(name, None, doc=doc)
    elif container == "operators":
        existing[name] = ExtensionOperator(name, None, doc=doc)
    elif container == "namespaces":
        existing[name] = ExtensionNamespace(name, doc=doc)


def load_trusted_plugin(manifest_path: str, root: str = ".", *,
                        registry: ExtensionRegistry | None = None,
                        policy: PluginPolicy | None = None,
                        policy_path: str | None = None,
                        trust_store: str | None = None) -> Dict[str, Any]:
    """Verify a manifest, then import and register its declared extensions."""
    report = validate_plugin_manifest(
        manifest_path, root, policy=policy, policy_path=policy_path, trust_store=trust_store
    )
    if not report["ok"]:
        raise PeaError("Plugin validation failed: " + "; ".join(report["issues"]))

    manifest = PluginManifest.from_dict(report["plugin"])
    module_path = Path(report["module_path"])
    module_name = f"pealang_trusted_plugin_{manifest.name}_{manifest.version.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise PeaError(f"Cannot import plugin module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    active = registry or ExtensionRegistry()
    init = getattr(module, manifest.entry_point, None)
    initialized = False
    if callable(init):
        try:
            parameters = inspect.signature(init).parameters
        except (TypeError, ValueError):
            parameters = {}
        if parameters and registry is not None:
            init(registry)
        elif parameters:
            init(active)
        else:
            init()
        initialized = True

    for function_name in manifest.functions:
        candidate = getattr(module, function_name, None)
        if callable(candidate):
            active.register_function(function_name, candidate, doc=getattr(candidate, "__doc__", "") or "")
        else:
            _fallback(active, "functions", function_name, f"External plugin function: {function_name}")

    for type_name in manifest.types:
        candidate = getattr(module, type_name, None)
        if callable(candidate):
            active.register_type(type_name, candidate, doc=getattr(candidate, "__doc__", "") or "")
        else:
            _fallback(active, "types", type_name, f"External plugin type: {type_name}")

    for symbol in manifest.operators:
        candidate = getattr(module, symbol, None)
        if callable(candidate):
            active.register_operator(symbol, candidate, doc=getattr(candidate, "__doc__", "") or "")
        else:
            _fallback(active, "operators", symbol, f"External plugin operator: {symbol}")

    for namespace_name in manifest.namespaces:
        candidate = getattr(module, namespace_name, None)
        if isinstance(candidate, dict):
            active.register_namespace(namespace_name, candidate)
        else:
            _fallback(active, "namespaces", namespace_name, f"External plugin namespace: {namespace_name}")

    report.update({
        "loaded": True,
        "initialized": initialized,
        "entry_point": manifest.entry_point,
        "registered": active.list_all(),
    })
    return report


def init_plugin_manifest(root: str = ".", name: str = "", module: str = "",
                         version: str = "0.1.0", *, description: str = "",
                         capabilities: Iterable[str] = (), functions: Iterable[str] = (),
                         types: Iterable[str] = (), operators: Iterable[str] = (),
                         namespaces: Iterable[str] = (), signature: str | None = None,
                         key_id: str | None = None, policy_path: str | None = None,
                         require_signature: bool = False,
                         trusted_key_ids: Iterable[str] = ()) -> Dict[str, Any]:
    """Create a plugin manifest and update the local plugin policy."""
    base = _root(root)
    if not _NAME_RE.fullmatch(name):
        raise PeaError(f"Invalid plugin name: {name}")
    if not _VERSION_RE.fullmatch(version):
        raise PeaError(f"Invalid plugin version: {version}")
    module_path = _within(base, module, "plugin module")
    if not module_path.is_file():
        raise PeaError(f"Plugin module not found: {module}")

    signature_value = ""
    if signature:
        signature_value = _relative(base, _within(base, signature, "plugin signature"))
    policy_target = Path(policy_path).resolve() if policy_path else base / DEFAULT_PLUGIN_POLICY
    if policy_target.is_file():
        policy, _ = load_plugin_policy(root, str(policy_target))
    else:
        policy = PluginPolicy()
    allowed = list(dict.fromkeys([*policy.allowed_capabilities, *capabilities]))
    keys = list(dict.fromkeys([*policy.trusted_key_ids, *(trusted_key_ids or [])]))
    updated = PluginPolicy(
        allowed_capabilities=tuple(allowed),
        trusted_key_ids=tuple(keys),
        require_signature=bool(policy.require_signature or require_signature),
    )
    policy_target.parent.mkdir(parents=True, exist_ok=True)
    policy_target.write_text(
        json.dumps(updated.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    manifest = PluginManifest(
        name=name,
        version=version,
        module=_relative(base, module_path),
        description=description,
        capabilities=tuple(capabilities),
        functions=tuple(functions),
        types=tuple(types),
        operators=tuple(operators),
        namespaces=tuple(namespaces),
        sha256=_sha256_file(module_path),
        signature=signature_value,
        key_id=key_id or "",
    )
    manifest_dir = base / DEFAULT_PLUGIN_DIR
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{name}.json"
    manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "ok": True,
        "manifest": str(manifest_path),
        "policy": str(policy_target),
        "plugin": manifest.to_dict(),
    }
