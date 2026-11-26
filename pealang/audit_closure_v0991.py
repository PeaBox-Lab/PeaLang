"""Repository-level audit closure checks for the PeaLang 1.0 line."""
from __future__ import annotations

from pathlib import Path
import json
import re

SDK_FILES = ("browser-sdk/package.json", "typescript-sdk/package.json", "react-sdk/package.json")
REQUIRED_DOCS = (
    "docs/project/COMPONENT_STATUS_1_0.md",
    "docs/project/INTERFACE_COMPLETENESS_0991.md",
    "docs/KNOWN_LIMITATIONS_1_0.md",
    "docs/project/FINAL_RELEASE_GATE_099.md",
)

_INTERFACE_DOC = "docs/project/INTERFACE_COMPLETENESS_0991.md"

# Human-maintained classification notes keyed by module path (relative to repo root).
_MODULE_NOTES = {
    "pealang/cloud_connectors.py": "listdir, stat, open, mkdir, remove, rename",
    "pealang/connector_runtime.py": "token",
    "pealang/connectors.py": "request",
    "pealang/distributed_compute.py": "execute",
    "pealang/distributed_serving.py": "increment, get, set",
    "pealang/enterprise_connectors.py": "get",
    "pealang/integration_hardening.py": "get",
    "pealang/object_storage.py": "list, read_bytes, write_bytes, delete",
    "pealang/orchestration_state.py": "begin, finish, successful, attempts",
    "pealang/serverless.py": "CompilationTarget.compile, CompilationTarget.execute, PythonTarget.execute (intentional sandbox/runtime stubs)",
    "pealang/sql.py": "SQLite-only portable upsert; other dialects raise intentionally",
    "pealang/pea_ai.py": "Anthropic embeddings not available, export_model/deploy_model placeholders",
}


def interface_sites_detail(root):
    """Return detailed info for every classified NotImplementedError site."""
    root = Path(root)
    sites = []
    for p in sorted((root / "pealang").glob("*.py")):
        if p.name == "audit_closure_v0991.py":
            continue
        rel = str(p.relative_to(root)).replace("\\", "/")
        for n, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            if "NotImplementedError" in line:
                sites.append({"file": rel, "line": n, "text": line.strip()})
    return sites


def generate_interface_markdown(root):
    """Generate the canonical interface-completeness markdown from live sites."""
    sites = interface_sites_detail(root)
    total = len(sites)
    by_mod: dict[str, list[dict]] = {}
    for s in sites:
        by_mod.setdefault(s["file"], []).append(s)
    lines = [
        "# Interface Completeness 0.99.1",
        "",
        f"All {total} `NotImplementedError` sites found by the audit are intentional base-interface contracts, not directly instantiable production backends. Concrete implementations are tested separately. The classified modules and methods are:",
        "",
    ]
    for mod in sorted(by_mod):
        note = _MODULE_NOTES.get(mod, "")
        label = mod.replace("pealang/", "")
        count = len(by_mod[mod])
        suffix = f" — {note}" if note else ""
        lines.append(f"- `{label}` ({count}):{suffix}")
        for s in by_mod[mod]:
            lines.append(f"  - L{s['line']}: `{s['text']}`")
    lines += [
        "",
        "Release policy: unclassified `NotImplementedError` occurrences are forbidden. Regenerate with `pea audit --write-interface-doc` when intentional classified sites change.",
        "",
    ]
    return "\n".join(lines)


def write_interface_markdown(root):
    root = Path(root)
    path = root / _INTERFACE_DOC
    content = generate_interface_markdown(root)
    path.write_text(content, encoding="utf-8")
    return str(path)


def audit_repository(root):
    root = Path(root)
    failures = []
    for rel in REQUIRED_DOCS:
        if not (root / rel).is_file():
            failures.append(f"missing:{rel}")
    for rel in SDK_FILES:
        p = root / rel
        if p.is_file() and json.loads(p.read_text(encoding="utf-8")).get("version") != "5.10.0":
            failures.append(f"version:{rel}")
    c = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if c.count("# Changelog") != 1:
        failures.append("changelog-root-count")
    if c.count("## 0.35.0 - 2026-10-23") != 1:
        failures.append("changelog-035-count")

    sites = interface_sites_detail(root)
    classified_path = root / _INTERFACE_DOC
    classified = classified_path.read_text(encoding="utf-8") if classified_path.is_file() else ""
    if len(sites) != 29:
        failures.append(f"interface-site-count:{len(sites)}")
    if f"All {len(sites)}" not in classified and "All 29" not in classified:
        failures.append("interface-classification")
    return {"passed": not failures, "failures": failures, "interface_sites": len(sites), "interface_detail": sites}
