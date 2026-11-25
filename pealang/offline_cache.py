"""Content-addressed package cache, portable bundles, and air-gapped lookup."""
from __future__ import annotations
from pathlib import Path
import gzip
import hashlib
import json
import re
import tarfile
import tempfile
import time

from .errors import PeaError
from .package_manager import DEFAULT_REGISTRY, Version, satisfies
from .registry import PackageCache
from .secure_packages import safe_extract

CACHE_SCHEMA = "pealang-offline-cache-v1"


def default_cache_dir() -> Path:
    return Path.home() / ".pealang" / "package_cache"


def _cache_dir(value: str | None) -> Path:
    return Path(value).resolve() if value else default_cache_dir()


def _index_path(directory: Path) -> Path:
    return directory / "index.json"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe(value) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(value))


def cache_key(name: str, version: str, registry: str = "") -> str:
    return f"{_safe(registry)}::{_safe(name)}::{_safe(version)}"


def load_index(cache_dir: str | None = None) -> dict:
    directory = _cache_dir(cache_dir)
    path = _index_path(directory)
    if not path.is_file():
        return {"schema": CACHE_SCHEMA, "entries": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise PeaError(f"Invalid offline cache index: {e}") from e
    if data.get("schema") != CACHE_SCHEMA or not isinstance(data.get("entries"), dict):
        raise PeaError("Unsupported offline cache index")
    return data


def save_index(data: dict, cache_dir: str | None = None) -> Path:
    directory = _cache_dir(cache_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = _index_path(directory)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _derive_identity(package: Path, name: str | None, version: str | None) -> tuple[str, str]:
    match = re.fullmatch(r"(.+)-(\d+\.\d+\.\d+)", package.stem)
    derived_name = match.group(1) if match else package.stem
    derived_version = match.group(2) if match else "0.0.0"
    return name or derived_name, version or derived_version


def cache_package(package: str, signature: str | None = None, *, name: str | None = None,
                  version: str | None = None, registry: str = DEFAULT_REGISTRY,
                  key_id: str | None = None, cache_dir: str | None = None) -> dict:
    """Store a local .pelib and optional detached signature in the offline cache."""
    package_path = Path(package).resolve()
    if not package_path.is_file():
        raise PeaError(f"Package not found: {package_path}")
    package_name, package_version = _derive_identity(package_path, name, version)
    Version.parse(package_version)
    data = package_path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    directory = _cache_dir(cache_dir)
    store = PackageCache(directory)
    stored_path, _ = store.put(f"{package_name}-{package_version}.pelib", data)

    signature_path = None
    signature_data = None
    if signature:
        source = Path(signature).resolve()
        if not source.is_file():
            raise PeaError(f"Signature not found: {source}")
        signature_data = source.read_bytes()
        signature_path = Path(str(stored_path) + ".sig")
        signature_path.write_bytes(signature_data)
        if not key_id:
            try:
                key_id = str(json.loads(signature_data.decode("utf-8")).get("key_id") or "")
            except Exception:
                key_id = ""

    entry = {
        "name": package_name,
        "version": package_version,
        "registry": registry,
        "sha256": digest,
        "package": stored_path.name,
        "signature": signature_path.name if signature_path else "",
        "key_id": key_id or "",
        "cached_at": int(time.time()),
    }
    index = load_index(str(directory))
    index["entries"][cache_key(package_name, package_version, registry)] = entry
    save_index(index, str(directory))
    return {
        "ok": True,
        **entry,
        "package_path": str(stored_path),
        "signature_path": str(signature_path) if signature_path else "",
    }


def find_cached(name: str, version: str | None = None, registry: str | None = None,
                cache_dir: str | None = None) -> dict:
    """Find the best cached package matching a name and optional version constraint."""
    if version and version.startswith("@"):
        version = version[1:]
    directory = _cache_dir(cache_dir)
    index = load_index(str(directory))
    candidates = []
    for key, entry in index["entries"].items():
        if entry.get("name") != name:
            continue
        if registry is not None and entry.get("registry", "") != registry:
            continue
        if version and version not in ("*", "latest"):
            try:
                if not satisfies(entry.get("version", ""), version):
                    continue
            except PeaError:
                continue
        candidates.append((key, entry))
    if not candidates:
        raise PeaError(f"No cached package for {name} {version or ''}".strip())
    candidates.sort(
        key=lambda pair: (Version.parse(pair[1].get("version", "0.0.0")), pair[1].get("cached_at", 0)),
        reverse=True,
    )
    key, entry = candidates[0]
    package_path = directory / entry["package"]
    if not package_path.is_file():
        raise PeaError(f"Cached package file is missing: {package_path}")
    actual = _sha256_file(package_path)
    if actual != entry.get("sha256"):
        raise PeaError(f"Cached package checksum mismatch for {name} {entry.get('version')}")
    signature_name = entry.get("signature", "")
    signature_path = directory / signature_name if signature_name else None
    if signature_path and not signature_path.is_file():
        raise PeaError(f"Cached signature is missing: {signature_path}")
    return {
        "key": key,
        **entry,
        "package_path": str(package_path),
        "signature_path": str(signature_path) if signature_path else "",
    }


def list_cached(cache_dir: str | None = None) -> list[dict]:
    directory = _cache_dir(cache_dir)
    index = load_index(str(directory))
    rows = []
    for entry in index["entries"].values():
        rows.append({
            **entry,
            "package_path": str(directory / entry["package"]),
            "available": (directory / entry["package"]).is_file(),
        })
    rows.sort(key=lambda row: (row.get("name", ""), row.get("version", ""), row.get("registry", "")))
    return rows


def remove_cached(name: str, version: str, registry: str = DEFAULT_REGISTRY,
                  cache_dir: str | None = None) -> dict:
    directory = _cache_dir(cache_dir)
    index = load_index(str(directory))
    key = cache_key(name, version, registry)
    entry = index["entries"].pop(key, None)
    if entry is None:
        raise PeaError(f"Cached package not found: {name} {version}")
    (directory / entry["package"]).unlink(missing_ok=True)
    if entry.get("signature"):
        (directory / entry["signature"]).unlink(missing_ok=True)
    save_index(index, str(directory))
    return {"ok": True, "removed": key}


def export_cache(destination: str, cache_dir: str | None = None) -> dict:
    """Write the cache index and all cached artifacts into a portable gzip bundle."""
    directory = _cache_dir(cache_dir)
    entries = load_index(str(directory))["entries"]
    files = [_index_path(directory)]
    for entry in entries.values():
        files.append(directory / entry["package"])
        if entry.get("signature"):
            files.append(directory / entry["signature"])
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise PeaError(f"Cannot export cache; missing files: {', '.join(missing)}")

    target = Path(destination).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for path in sorted(set(files), key=lambda item: item.relative_to(directory).as_posix()):
                    info = archive.gettarinfo(str(path), arcname=path.relative_to(directory).as_posix())
                    info.mtime = 0
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    with path.open("rb") as handle:
                        archive.addfile(info, handle)
    return {"ok": True, "bundle": str(target), "entries": len(entries), "sha256": _sha256_file(target)}


def import_cache(bundle: str, cache_dir: str | None = None) -> dict:
    """Import a portable cache bundle produced by export_cache()."""
    source = Path(bundle).resolve()
    if not source.is_file():
        raise PeaError(f"Cache bundle not found: {source}")
    directory = _cache_dir(cache_dir)
    imported = 0
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        safe_extract(source, root)
        index_path = root / "index.json"
        if not index_path.is_file():
            raise PeaError("Cache bundle has no index.json")
        data = json.loads(index_path.read_text(encoding="utf-8"))
        if data.get("schema") != CACHE_SCHEMA:
            raise PeaError("Unsupported cache bundle schema")
        for entry in data.get("entries", {}).values():
            package = root / entry["package"]
            signature = root / entry["signature"] if entry.get("signature") else None
            cache_package(
                package, str(signature) if signature else None,
                name=entry.get("name"), version=entry.get("version"),
                registry=entry.get("registry", DEFAULT_REGISTRY),
                key_id=entry.get("key_id"), cache_dir=str(directory),
            )
            imported += 1
    return {"ok": True, "imported": imported, "cache_dir": str(directory)}
