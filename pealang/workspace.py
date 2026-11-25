"""Workspace discovery, member graph analysis, and deterministic workspace locks."""
from __future__ import annotations
from pathlib import Path
import json

from .errors import PeaError
from .package_manager import (
    load_pea_toml, dependency_entries, write_lock, sha256_file, tomllib,
)

WORKSPACE_FILE = "pea.workspace.toml"
WORKSPACE_LOCK = "pea.workspace.lock"


def _string(value) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def find_workspace(root: str = ".") -> Path | None:
    """Find the nearest workspace file at or above root."""
    path = Path(root).resolve()
    if path.is_file():
        path = path.parent
    for candidate in (path, *path.parents):
        workspace = candidate / WORKSPACE_FILE
        if workspace.is_file():
            return workspace
    return None


def _write_workspace(path: Path, name: str, members: list[str]) -> None:
    lines = ["[workspace]", f"name = {_string(name)}", "members = ["]
    lines.extend(f"  {_string(member)}," for member in members)
    lines.append("]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def init_workspace(root: str = ".", name: str | None = None) -> Path:
    """Create an empty workspace manifest at root."""
    path = Path(root).resolve()
    path.mkdir(parents=True, exist_ok=True)
    manifest = path / WORKSPACE_FILE
    if manifest.exists():
        raise PeaError(f"Workspace already exists: {manifest}")
    _write_workspace(manifest, name or path.name, [])
    return manifest


def load_workspace(root: str = ".") -> dict:
    """Load the nearest workspace manifest and resolve its member directories."""
    manifest = find_workspace(root)
    if manifest is None:
        raise PeaError(f"No {WORKSPACE_FILE} found from {Path(root).resolve()}")
    try:
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except Exception as e:
        raise PeaError(f"Invalid workspace manifest: {e}") from e
    section = data.get("workspace", {})
    raw_members = section.get("members", [])
    if not isinstance(raw_members, list):
        raise PeaError("Workspace members must be a list")
    members: list[Path] = []
    for entry in raw_members:
        value = str(entry.get("path", "")) if isinstance(entry, dict) else str(entry)
        if not value:
            continue
        candidate = (manifest.parent / value).resolve()
        if not (candidate / "pea.toml").is_file():
            raise PeaError(f"Workspace member has no pea.toml: {candidate}")
        if candidate not in members:
            members.append(candidate)
    return {
        "path": manifest,
        "root": manifest.parent,
        "name": str(section.get("name") or manifest.parent.name),
        "members": members,
        "raw": section,
    }


def add_workspace_member(root: str, member: str) -> dict:
    """Add a project directory to the nearest workspace manifest."""
    workspace = load_workspace(root)
    member_path = Path(member).resolve()
    if not (member_path / "pea.toml").is_file():
        raise PeaError(f"Workspace member has no pea.toml: {member_path}")
    members = [str(item) for item in workspace["members"]]
    relative = _relative(member_path, workspace["root"])
    if relative not in members:
        members.append(relative)
    _write_workspace(workspace["path"], workspace["name"], members)
    return {
        "ok": True,
        "workspace": str(workspace["path"]),
        "member": relative,
        "members": members,
    }


def workspace_members(root: str = ".") -> dict:
    """Return deterministic metadata for every workspace member."""
    workspace = load_workspace(root)
    rows = []
    for path in sorted(workspace["members"], key=lambda item: _relative(item, workspace["root"])):
        manifest, data = load_pea_toml(path)
        project = data.get("project", {})
        rows.append({
            "name": str(project.get("name", path.name)),
            "version": str(project.get("version", "")),
            "path": str(path),
            "relative_path": _relative(path, workspace["root"]),
            "manifest_sha256": sha256_file(manifest),
            "dependencies": sorted(dependency_entries(data)),
        })
    return {
        "ok": True,
        "workspace": workspace["name"],
        "root": str(workspace["root"]),
        "manifest": str(workspace["path"]),
        "members": rows,
    }


def workspace_graph(root: str = ".") -> dict:
    """Analyze local workspace links for cycles and produce a build order."""
    members = workspace_members(root)["members"]
    by_path = {member["path"]: member for member in members}
    by_name = {member["name"]: member for member in members}
    nodes = [member["name"] for member in members]
    edges = []

    for member in members:
        _, data = load_pea_toml(member["path"])
        for dep_name, raw_spec in sorted(dependency_entries(data).items()):
            spec = {"path": raw_spec} if isinstance(raw_spec, str) else dict(raw_spec)
            target = None
            if "path" in spec:
                resolved = (Path(member["path"]) / str(spec["path"])).resolve()
                target = by_path.get(str(resolved))
            elif spec.get("workspace"):
                requested = spec.get("workspace")
                requested_name = str(requested) if isinstance(requested, str) else str(dep_name)
                target = by_name.get(requested_name)
            if target and target["name"] != member["name"]:
                edges.append({
                    "from": member["name"],
                    "to": target["name"],
                    "source": "workspace",
                })

    duplicates = sorted({name for name in nodes if nodes.count(name) > 1})
    adjacency: dict[str, list[str]] = {name: [] for name in nodes}
    order_adjacency: dict[str, list[str]] = {name: [] for name in nodes}
    indegree = {name: 0 for name in nodes}
    for edge in edges:
        if edge["to"] not in adjacency[edge["from"]]:
            adjacency[edge["from"]].append(edge["to"])
        if edge["from"] not in order_adjacency[edge["to"]]:
            order_adjacency[edge["to"]].append(edge["from"])
            indegree[edge["from"]] += 1
    for name in adjacency:
        adjacency[name].sort()
        order_adjacency[name].sort()

    state: dict[str, int] = {}
    stack: list[str] = []
    cycles: list[dict] = []

    def visit(name: str) -> None:
        state[name] = 1
        stack.append(name)
        for neighbor in adjacency[name]:
            if state.get(neighbor) == 1:
                cycles.append({"cycle": stack[stack.index(neighbor):] + [neighbor]})
            elif state.get(neighbor, 0) == 0:
                visit(neighbor)
        stack.pop()
        state[name] = 2

    for name in sorted(nodes):
        if state.get(name, 0) == 0:
            visit(name)

    ready = sorted(name for name, degree in indegree.items() if degree == 0)
    order = []
    while ready:
        name = ready.pop(0)
        order.append(name)
        for neighbor in order_adjacency[name]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                ready.append(neighbor)
        ready.sort()

    return {
        "ok": not cycles and not duplicates,
        "workspace": workspace_members(root)["workspace"],
        "members": nodes,
        "edges": sorted(edges, key=lambda item: (item["from"], item["to"])),
        "cycles": cycles,
        "duplicates": [{"name": name, "count": nodes.count(name)} for name in duplicates],
        "order": order,
    }


def workspace_lock(root: str = ".", *, registry_resolve: bool = False, offline: bool = False,
                   registry: str | None = None, token: str | None = None) -> dict:
    """Refresh every member lock and write a deterministic workspace lock."""
    workspace = load_workspace(root)
    graph = workspace_graph(root)
    if not graph["ok"]:
        raise PeaError("Cannot lock a workspace with cycles or duplicate member names")

    members = []
    for path in sorted(workspace["members"], key=lambda item: _relative(item, workspace["root"])):
        manifest, data = load_pea_toml(path)
        lock_path, _ = write_lock(
            path, registry_resolve=registry_resolve, offline=offline,
            registry=registry, token=token,
        )
        project = data.get("project", {})
        members.append({
            "name": str(project.get("name", path.name)),
            "version": str(project.get("version", "")),
            "path": _relative(path, workspace["root"]),
            "lock": _relative(lock_path, workspace["root"]),
            "manifest_sha256": sha256_file(manifest),
            "lock_sha256": sha256_file(lock_path),
        })

    payload = {
        "lock_version": 1,
        "workspace": workspace["name"],
        "order": graph["order"],
        "members": members,
    }
    out = workspace["root"] / WORKSPACE_LOCK
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "lock": str(out),
        "sha256": sha256_file(out),
        "workspace": workspace["name"],
        "order": graph["order"],
        "members": members,
    }
