"""Dependency vulnerability advisories and license policy checks."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
import json

from .errors import PeaError
from .package_manager import satisfies

SEVERITIES = ("info", "low", "medium", "high", "critical")


def severity_rank(severity: str) -> int:
    """Return the ordinal rank of a severity, treating unknown values as medium."""
    try:
        return SEVERITIES.index(str(severity).strip().lower())
    except ValueError:
        return SEVERITIES.index("medium")


def _norm_license(value: str | None) -> str:
    return " ".join(str(value or "").strip().upper().split())


@dataclass(frozen=True)
class Advisory:
    id: str
    package: str
    affected: str = "*"
    severity: str = "medium"
    summary: str = ""
    fixed_version: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Advisory":
        if not isinstance(data, dict):
            raise PeaError("Each advisory must be a JSON object")
        advisory_id = str(data.get("id") or data.get("advisory_id") or "").strip()
        package = str(data.get("package") or data.get("name") or "").strip()
        if not advisory_id or not package:
            raise PeaError("Advisory requires id and package")
        return cls(
            id=advisory_id,
            package=package,
            affected=str(data.get("affected") or data.get("range") or "*"),
            severity=str(data.get("severity") or "medium"),
            summary=str(data.get("summary") or ""),
            fixed_version=(str(data["fixed_version"]) if data.get("fixed_version") else None),
        )


@dataclass(frozen=True)
class SecurityPolicy:
    max_severity: str = "high"
    allow_licenses: tuple[str, ...] = ()
    deny_licenses: tuple[str, ...] = ()
    require_license: bool = False
    ignore_advisories: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "max_severity": self.max_severity,
            "allow_licenses": list(self.allow_licenses),
            "deny_licenses": list(self.deny_licenses),
            "require_license": self.require_license,
            "ignore_advisories": list(self.ignore_advisories),
        }

    @classmethod
    def from_dict(cls, data: dict | None = None) -> "SecurityPolicy":
        data = data or {}
        max_severity = str(data.get("max_severity") or "high").strip().lower()
        if max_severity not in SEVERITIES:
            raise PeaError(f"Invalid max_severity: {max_severity}")
        return cls(
            max_severity=max_severity,
            allow_licenses=tuple(_norm_license(x) for x in data.get("allow_licenses", [])),
            deny_licenses=tuple(_norm_license(x) for x in data.get("deny_licenses", [])),
            require_license=bool(data.get("require_license", False)),
            ignore_advisories=tuple(str(x) for x in data.get("ignore_advisories", [])),
        )


DEFAULT_POLICY = SecurityPolicy()


def _default_path(root: Path, name: str) -> Path | None:
    project_path = root / ".pealang" / name
    if project_path.is_file():
        return project_path
    home_path = Path.home() / ".pealang" / name
    return home_path if home_path.is_file() else None


def load_advisories(root: str = ".", path: str | None = None) -> tuple[list[Advisory], str | None]:
    """Load advisory JSON from an explicit path, project config, or user config."""
    root_path = Path(root).resolve()
    source = Path(path) if path else _default_path(root_path, "advisories.json")
    if source is None:
        return [], None
    if not source.is_file():
        raise PeaError(f"Advisory file not found: {source}")
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except Exception as e:
        raise PeaError(f"Invalid advisory JSON: {e}") from e
    rows = data.get("advisories", []) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise PeaError("Advisory file must contain a JSON list")
    return [Advisory.from_dict(row) for row in rows], str(source)


def load_security_policy(root: str = ".", path: str | None = None) -> tuple[SecurityPolicy, str | None]:
    """Load a security policy from an explicit path, project config, or user config."""
    root_path = Path(root).resolve()
    source = Path(path) if path else _default_path(root_path, "security-policy.json")
    if source is None:
        return DEFAULT_POLICY, None
    if not source.is_file():
        raise PeaError(f"Security policy not found: {source}")
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except Exception as e:
        raise PeaError(f"Invalid security policy JSON: {e}") from e
    return SecurityPolicy.from_dict(data), str(source)


def _dependency_rows(root: Path) -> list[dict]:
    from .package_manager import load_pea_toml

    manifest, data = load_pea_toml(str(root))
    lock_path = manifest.parent / "pea.lock"
    dependencies = data.get("dependencies", {})
    rows: list[dict] = []
    if lock_path.is_file():
        locked = json.loads(lock_path.read_text(encoding="utf-8"))
        for dep in locked:
            name = str(dep.get("name", ""))
            spec = dependencies.get(name, {}) if isinstance(dependencies, dict) else {}
            spec = spec if isinstance(spec, dict) else {}
            rows.append({
                "name": name,
                "version": str(dep.get("version", "*")),
                "source": str(dep.get("source", "")),
                "license": str(dep.get("license") or spec.get("license") or ""),
            })
    else:
        for name, spec in sorted(dependencies.items()):
            spec = spec if isinstance(spec, dict) else {}
            rows.append({
                "name": str(name),
                "version": str(spec.get("version", spec.get("constraint", "*"))),
                "source": "registry" if "registry" in spec or "version" in spec else "path",
                "license": str(spec.get("license") or ""),
            })
    return sorted(rows, key=lambda row: (row["name"], row["version"]))


def _is_affected(version: str, affected: str) -> bool:
    affected = str(affected or "*")
    if affected in ("", "*"):
        return True
    try:
        return satisfies(version, affected)
    except PeaError:
        return False


def scan_dependencies(root: str = ".", *, advisories: list[Advisory] | None = None,
                      advisory_path: str | None = None, policy: SecurityPolicy | None = None,
                      policy_path: str | None = None) -> dict:
    """Scan locked dependencies against advisories and license policy."""
    root_path = Path(root).resolve()
    if advisories is None:
        advisories, advisory_source = load_advisories(str(root_path), advisory_path)
    else:
        advisory_source = advisory_path
    if policy is None:
        policy, policy_source = load_security_policy(str(root_path), policy_path)
    else:
        policy_source = policy_path

    dependencies = _dependency_rows(root_path)
    findings: list[dict] = []
    ignored = 0
    max_rank = severity_rank(policy.max_severity)
    ignored_ids = set(policy.ignore_advisories)
    deny = set(policy.deny_licenses)
    allow = set(policy.allow_licenses)

    for dep in dependencies:
        for advisory in advisories:
            if advisory.package != dep["name"] or not _is_affected(dep["version"], advisory.affected):
                continue
            if advisory.id in ignored_ids:
                ignored += 1
                continue
            rank = severity_rank(advisory.severity)
            findings.append({
                "type": "advisory",
                "id": advisory.id,
                "package": dep["name"],
                "version": dep["version"],
                "severity": advisory.severity,
                "summary": advisory.summary,
                "fixed_version": advisory.fixed_version or "",
                "blocking": rank > max_rank,
            })

        license_name = _norm_license(dep["license"])
        if license_name in deny:
            findings.append({
                "type": "license",
                "id": "",
                "package": dep["name"],
                "version": dep["version"],
                "severity": "high",
                "summary": f"License {license_name or 'UNKNOWN'} is denied by policy",
                "fixed_version": "",
                "blocking": True,
            })
        elif allow and license_name and license_name not in allow:
            findings.append({
                "type": "license",
                "id": "",
                "package": dep["name"],
                "version": dep["version"],
                "severity": "high",
                "summary": f"License {license_name} is not in the allow list",
                "fixed_version": "",
                "blocking": True,
            })
        elif policy.require_license and not license_name:
            findings.append({
                "type": "license",
                "id": "",
                "package": dep["name"],
                "version": dep["version"],
                "severity": "medium",
                "summary": "Dependency license is not declared",
                "fixed_version": "",
                "blocking": True,
            })

    findings.sort(key=lambda f: (-severity_rank(f["severity"]), f["type"], f["package"], f["id"]))
    advisory_count = sum(1 for f in findings if f["type"] == "advisory")
    license_count = sum(1 for f in findings if f["type"] == "license")
    blocking_count = sum(1 for f in findings if f["blocking"])
    return {
        "ok": blocking_count == 0,
        "root": str(root_path),
        "dependencies": dependencies,
        "findings": findings,
        "summary": {
            "dependencies": len(dependencies),
            "advisories": advisory_count,
            "license_violations": license_count,
            "blocking": blocking_count,
            "ignored": ignored,
        },
        "policy": policy.to_dict(),
        "advisory_source": advisory_source,
        "policy_source": policy_source,
    }
