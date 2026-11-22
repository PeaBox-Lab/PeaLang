from __future__ import annotations

import json
import re
import os
import shutil
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Callable
from .errors import PeaError


DEFAULT_MANIFEST = {
    'project': {'name': 'my-pea-project', 'version': '0.1.0', 'entry': 'main.pea'},
    'dependencies': {}
}


# Template variable functions for cookiecutter-style substitution
def _template_now() -> str:
    from datetime import datetime
    return datetime.now().isoformat()


def _template_today() -> str:
    from datetime import date
    return date.today().isoformat()


def _template_random_hex(n: int = 8) -> str:
    import secrets
    return secrets.token_hex(n)


def _template_random_uuid() -> str:
    import uuid
    return str(uuid.uuid4())


def _template_slug(s: str) -> str:
    import re
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


# Template context with built-in functions
TEMPLATE_BUILTINS = {
    'now': _template_now,
    'today': _template_today,
    'random_hex': _template_random_hex,
    'random_uuid': _template_random_uuid,
    'slug': _template_slug,
    'upper': lambda s: s.upper(),
    'lower': lambda s: s.lower(),
    'capitalize': lambda s: s.capitalize(),
    'title': lambda s: s.title(),
}


TEMPLATES = {
    'default': 'print "Hello from PeaLang"\n',
    'webapp': '''let app = web.app()

function home(req) {
    return web.json({"message": "Hello from PeaLang webapp", "path": req["path"]})
}

app.get("/", home)
app.get("/health", function(req) { return web.json({"status": "ok"}) })

print "Starting PeaLang webapp on http://127.0.0.1:8080"
app.serve("127.0.0.1", 8080)
''',
    'api': '''let app = web.app()
app.enable_cors()

app.get("/health", function(req){ return web.health() })
app.get("/v1/items", function(req){ return web.envelope([{"id":1,"name":"example"}], {"count":1}) })
app.post("/v1/items", function(req){
  let body = req["json"] ?? {}
  return web.created({"id": 2, "item": body}, "/v1/items/2")
})
app.not_found(function(req){ return web.not_found("Route not found: " + req["path"]) })

print "API on http://127.0.0.1:8080"
app.serve("127.0.0.1", 8080)
''',
    'analysis': '''let data = [{"name": "Ada", "score": 91}, {"name": "Linus", "score": 84}, {"name": "Grace", "score": 97}]
print analysis.profile(data)
print analysis.describe(data, "score")
print "Top scores:"
for row in data { print row["name"] + ": " + row["score"] }
''',
    'library': '''function add(a, b) {
    return a + b
}
export add

function greet(name) {
    return "Hello, " + name
}
export greet

function version() {
    return "0.1.0"
}
export version
''',
    'interop': '''let result = interop.run("python", ["--version"])
print result
''',
    'automation': '''// Automation starter
print "cwd: " + interop.cwd()
let files = interop.walk(".")
print "files: " + str(len(files))
interop.write_text("report.txt", "ok")
print "done"
''',
    'etl': '''// ETL starter: load -> transform -> output
let raw = analysis.from_json(interop.read_text("data.json"))
print "rows: " + str(len(raw))
let clean = analysis.dropna(raw)
let prof = analysis.profile(clean)
interop.write_json("profile.json", prof)
print analysis.summary(clean)
''',
    'data': '''// Data pipeline starter: profile -> clean -> SQL -> report
let raw = [
    {"team": "a", "score": 91},
    {"team": "a", "score": 84},
    {"team": "b", "score": 77},
    {"team": "b", "score": null}
]
let clean = analysis.dropna(raw)
print analysis.summary(clean)
let totals = analysis.sql(clean, "SELECT team, COUNT(*) AS n, AVG(score) AS avg_score FROM data GROUP BY team ORDER BY team")
print totals
analysis.write_json_file("report.json", totals)
print "wrote report.json"
''',
    'polyglot': '''// Polyglot starter: Python bridge + Go/TypeScript client generation
let root = interop.call_python("math", "sqrt", 144)
print "python sqrt: " + str(root)
let go_client = interop.generate_go("http://127.0.0.1:8787")
print "go client bytes: " + str(len(go_client))
let ts_client = interop.generate_typescript("http://127.0.0.1:8787")
print "ts client bytes: " + str(len(ts_client))
if interop.go_available() {
    print "go: " + interop.go_version()
} else {
    print "go toolchain not installed"
}
''',
    'cli': '''// CLI tool starter
function main(args) {
    if len(args) == 0 {
        print "Usage: pea run main.pea <command>"
        return 1
    }
    match args[0] {
        "hello" => print "Hello, " + (args[1] ?? "World"),
        "version" => print "1.0.0",
        _ => print "Unknown command: " + args[0]
    }
    return 0
}
''',
}


def _render_template(content: str, context: dict) -> str:
    """Render template with {{variable}} substitution and {{func(...)}} calls."""
    import re

    # First pass: handle function calls {{func(args)}}
    def replace_func(match):
        func_name = match.group(1)
        args_str = match.group(2).strip()
        if func_name in TEMPLATE_BUILTINS:
            if args_str:
                try:
                    # Simple argument parsing
                    args = [a.strip().strip('"\'') for a in args_str.split(',')]
                    return str(TEMPLATE_BUILTINS[func_name](*args))
                except Exception:
                    return match.group(0)
            else:
                try:
                    return str(TEMPLATE_BUILTINS[func_name]())
                except Exception:
                    return match.group(0)
        return match.group(0)

    content = re.sub(r'\{\{\s*(\w+)\(([^)]*)\)\s*\}\}', replace_func, content)

    # Second pass: simple variable substitution {{variable}}
    def replace_var(match):
        var = match.group(1).strip()
        if var in context:
            return str(context[var])
        # Check for nested keys like project.name
        parts = var.split('.')
        val = context
        for p in parts:
            if isinstance(val, dict) and p in val:
                val = val[p]
            else:
                return match.group(0)
        return str(val)

    return re.sub(r'\{\{\s*([\w.]+)\s*\}\}', replace_var, content)


def load_manifest(start: str = '.'):
    p = Path(start).resolve()
    if p.is_file():
        p = p.parent
    while True:
        f = p / 'pea.json'
        if f.is_file():
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
            except Exception as ex:
                raise PeaError(f'Invalid pea.json: {ex}') from ex
            project = data.get('project', {})
            for key in ('name', 'version', 'entry'):
                if key not in project:
                    raise PeaError(f"pea.json project requires '{key}'")
            deps = data.get('dependencies', {})
            if not isinstance(deps, dict):
                raise PeaError('pea.json dependencies must be a dictionary')
            return f, data
        if p.parent == p:
            return None, None
        p = p.parent


def init_project(path: str = '.', name: str | None = None, template: str = 'default', variables: dict | None = None):
    root = Path(path).resolve()
    root.mkdir(parents=True, exist_ok=True)

    if template not in TEMPLATES:
        raise PeaError(f'Unknown template: {template}. Available: {", ".join(sorted(TEMPLATES))}')

    # Build template context
    proj_name = name or root.name
    context = {
        'project': {
            'name': proj_name,
            'version': '0.1.0',
            'description': f'{proj_name} - a PeaLang project',
            'author': os.getenv('USER') or os.getenv('USERNAME') or 'developer',
            'year': str(datetime.now().year),
        },
        'template': template,
        'vars': variables or {},
    }
    context.update(variables or {})

    if template == 'library':
        # Library projects use pea.toml manifest
        manifest = root / 'pea.toml'
        if manifest.exists():
            raise PeaError('pea.toml already exists')

        lib_name = proj_name.replace("-", "_")
        # Create pea.toml manifest for library
        manifest.write_text(
            '[project]\n'
            'name = "' + lib_name + '"\n'
            'version = "0.1.0"\n'
            'description = "' + context['project']['description'] + '"\n'
            'entry = "src/' + lib_name + '.pea"\n'
            '\n'
            '[library]\n'
            'exports = ["add", "greet", "version"]\n'
            '\n'
            '[dependencies]\n'
            '\n'
            '[permissions]\n'
            'allow = []\n',
            encoding="utf-8",
        )
        # Create src/<name>.pea from library template
        src_dir = root / 'src'
        src_dir.mkdir(exist_ok=True)
        lib_src = src_dir / (lib_name + '.pea')
        if not lib_src.exists():
            content = _render_template(TEMPLATES[template], context)
            lib_src.write_text(content, encoding='utf-8')
        # Create tests/test_<name>.pea
        tests_dir = root / 'tests'
        tests_dir.mkdir(exist_ok=True)
        test_file = tests_dir / ('test_' + lib_name + '.pea')
        test_file.write_text(
            '// Tests for ' + proj_name + '\n'
            'import "../src/' + lib_name + '.pea" as ' + lib_name + '\n'
            '\n'
            'test "add function" {\n'
            '    expect ' + lib_name + '.add(2, 3) == 5\n'
            '    expect ' + lib_name + '.add(-1, 1) == 0\n'
            '}\n'
            '\n'
            'test "greet function" {\n'
            '    expect ' + lib_name + '.greet("World") == "Hello, World"\n'
            '}\n'
            '\n'
            'test "version function" {\n'
            '    expect ' + lib_name + '.version() == "0.1.0"\n'
            '}\n',
            encoding='utf-8',
        )
        # Create README.md
        readme_lines = [
            '# ' + proj_name,
            '',
            'A PeaLang library.',
            '',
            '## Installation',
            '',
            'Add to your project\'s pea.toml:',
            '',
            '```toml',
            '[dependencies]',
            '"' + lib_name + '" = { path = "./path/to/' + lib_name + '" }',
            '```',
            '',
            '## Usage',
            '',
            '```pea',
            'import "' + lib_name + '" as ' + lib_name,
            '',
            'print ' + lib_name + '.add(2, 3)',
            'print ' + lib_name + '.greet("World")',
            '```',
        ]
        (root / 'README.md').write_text('\n'.join(readme_lines) + '\n', encoding='utf-8')
        # Create LICENSE
        license_lines = [
            'MIT License',
            '',
            'Copyright (c) ' + str(datetime.now().year) + ' ' + proj_name,
            '',
            'Permission is hereby granted, free of charge, to any person obtaining a copy',
            'of this software and associated documentation files (the "Software"), to deal',
            'in the Software without restriction, including without limitation the rights',
            'to use, copy, modify, merge, publish, distribute, sublicense, and/or sell',
            'copies of the Software, and to permit persons to whom the Software is',
            'furnished to do so, subject to the following conditions:',
            '',
            'The above copyright notice and this permission notice shall be included in all',
            'copies or substantial portions of the Software.',
        ]
        (root / 'LICENSE').write_text('\n'.join(license_lines) + '\n', encoding='utf-8')

        return str(manifest)

    # Non-library templates use pea.json
    manifest = root / 'pea.json'

    if manifest.exists():
        raise PeaError('pea.json already exists')

    # Prepare manifest
    data = json.loads(json.dumps(DEFAULT_MANIFEST))
    data['project']['name'] = proj_name
    data['project']['description'] = context['project']['description']
    data['project']['author'] = context['project']['author']
    manifest.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

    # Render main.pea
    main = root / 'main.pea'
    if not main.exists():
        content = _render_template(TEMPLATES[template], context)
        main.write_text(content, encoding='utf-8')

    (root / 'modules').mkdir(exist_ok=True)

    if template in ('webapp', 'api'):
        (root / 'static').mkdir(exist_ok=True)
        (root / 'tests').mkdir(exist_ok=True)
        # Generate a basic test file
        test_file = root / 'tests' / 'test_main.pea'
        test_file.write_text(f'''// Tests for {proj_name}
import "main.pea" as m

test "health check" {{
    // Add your tests here
    expect true
}}
''', encoding='utf-8')

    return str(manifest)


def add_dependency(name: str, path: str, project_dir: str = '.'):
    mf, data = load_manifest(project_dir)
    if not mf:
        raise PeaError('No pea.json found')

    dep_path = Path(path)
    if not dep_path.is_absolute():
        dep_path = (mf.parent / dep_path).resolve()

    if not dep_path.exists():
        raise PeaError(f'Dependency path not found: {path}')

    try:
        stored = str(dep_path.relative_to(mf.parent))
    except ValueError:
        stored = str(dep_path)

    data.setdefault('dependencies', {})[str(name)] = {'path': stored}
    mf.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return data['dependencies'][str(name)]


def remove_dependency(name: str, project_dir: str = '.'):
    mf, data = load_manifest(project_dir)
    if not mf:
        raise PeaError('No pea.json found')

    data.setdefault('dependencies', {}).pop(str(name), None)
    mf.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return True


def project_info(start: str = '.'):
    mf, data = load_manifest(start)
    if not mf:
        raise PeaError('No pea.json found')
    return {'root': str(mf.parent), 'manifest': str(mf), **data}


def resolve_module(spec, current_dir, project_root=None, dependencies=None):
    spec = str(spec)
    if spec.startswith('./') or spec.startswith('../') or '/' in spec or spec.endswith('.pea'):
        p = (Path(current_dir) / spec).resolve()
        if p.suffix != '.pea':
            p = p.with_suffix('.pea')
        return p

    root = Path(project_root or current_dir)
    local = (root / 'modules' / spec).with_suffix('.pea')
    if local.is_file():
        return local.resolve()

    dep = (dependencies or {}).get(spec)
    if dep:
        base = Path(dep.get('path', ''))
        if not base.is_absolute():
            base = (root / base).resolve()
        dm, dd = load_manifest(base)
        if dm:
            return (dm.parent / dd['project']['entry']).resolve()
        p = base
        if p.is_dir():
            p = p / 'main.pea'
        return p.resolve()

    return (Path(current_dir) / spec).with_suffix('.pea').resolve()


# --- Migration support ---

@dataclass
class MigrationStep:
    from_version: str
    to_version: str
    description: str
    migrate_fn: Callable[[dict], dict]  # takes manifest, returns new manifest


MIGRATIONS: list[MigrationStep] = []


def register_migration(step: MigrationStep):
    MIGRATIONS.append(step)
    MIGRATIONS.sort(key=lambda s: s.from_version)


def migrate_manifest(manifest: dict, target_version: str | None = None) -> dict:
    """Apply migrations to bring manifest up to date."""
    current = manifest.get('project', {}).get('version', '0.1.0')
    if target_version is None:
        target_version = max((s.to_version for s in MIGRATIONS), default=current)

    applied = []
    for step in MIGRATIONS:
        if step.from_version == current and (target_version is None or step.to_version <= target_version):
            manifest = step.migrate_fn(manifest)
            current = step.to_version
            applied.append(step.description)

    manifest['project']['version'] = current
    return manifest


def migrate_path(path: str, from_ver: str, to_ver: str, dry_run: bool = False) -> list[MigrationStep]:
    """Migrate a project from one version to another."""
    mf, data = load_manifest(path)
    if not mf:
        raise PeaError('No pea.json found')

    steps = []
    for step in MIGRATIONS:
        if step.from_version >= from_ver and step.to_version <= to_ver:
            steps.append(step)

    if dry_run:
        return steps

    for step in steps:
        data = step.migrate_fn(data)

    data['project']['version'] = to_ver
    mf.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return steps


# Built-in migrations

def _migration_010_to_020(manifest: dict) -> dict:
    """Add 'author' field to project if missing."""
    if 'author' not in manifest.get('project', {}):
        manifest.setdefault('project', {})['author'] = os.getenv('USER') or os.getenv('USERNAME') or 'developer'
    return manifest


def _migration_020_to_030(manifest: dict) -> dict:
    """Add 'description' field to project if missing."""
    if 'description' not in manifest.get('project', {}):
        name = manifest.get('project', {}).get('name', 'my-pea-project')
        manifest.setdefault('project', {})['description'] = f'{name} - a PeaLang project'
    return manifest


def _migration_030_to_040(manifest: dict) -> dict:
    """Move 'scripts' to 'project.scripts'."""
    if 'scripts' in manifest and 'project' in manifest:
        manifest['project']['scripts'] = manifest.pop('scripts')
    return manifest


# Register built-in migrations
register_migration(MigrationStep('0.1.0', '0.2.0', 'Add author field', _migration_010_to_020))
register_migration(MigrationStep('0.2.0', '0.3.0', 'Add description field', _migration_020_to_030))
register_migration(MigrationStep('0.3.0', '0.4.0', 'Move scripts to project.scripts', _migration_030_to_040))


# --- Lockfile integrity ---

def compute_lock_hash(deps: dict) -> str:
    import hashlib
    content = json.dumps(deps, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def write_lock(root: str = '.', deps: dict | None = None) -> tuple[str, str]:
    """Write pea.lock with dependency hashes."""
    mf, data = load_manifest(root)
    if not mf:
        raise PeaError('No pea.json found')

    if deps is None:
        deps = data.get('dependencies', {})

    lock_data = {
        'version': 1,
        'generated_at': datetime.now().isoformat(),
        'project_version': data['project']['version'],
        'dependencies': deps,
        'lock_hash': compute_lock_hash(deps),
    }

    lock_path = mf.parent / 'pea.lock'
    lock_path.write_text(json.dumps(lock_data, indent=2) + '\n', encoding='utf-8')
    return str(lock_path), lock_data['lock_hash']


def verify_lock(root: str = '.') -> bool:
    """Verify pea.lock matches current dependencies."""
    mf, data = load_manifest(root)
    if not mf:
        raise PeaError('No pea.json found')

    lock_path = mf.parent / 'pea.lock'
    if not lock_path.exists():
        raise PeaError('pea.lock not found')

    lock = json.loads(lock_path.read_text(encoding='utf-8'))
    current_hash = compute_lock_hash(data.get('dependencies', {}))

    if lock.get('lock_hash') != current_hash:
        raise PeaError(f'Lock hash mismatch: expected {lock["lock_hash"]}, got {current_hash}')

    return True


# --- pea upgrade support ---

def upgrade_project(root: str = '.', target_version: str | None = None, dry_run: bool = False) -> dict:
    """Upgrade a project to the latest or target version."""
    mf, data = load_manifest(root)
    if not mf:
        raise PeaError('No pea.json found')

    current = data['project']['version']
    steps = migrate_path(root, current, target_version or '999.999.999', dry_run=dry_run)

    if not steps:
        return {'current': current, 'target': target_version, 'applied': [], 'dry_run': dry_run}

    if not dry_run:
        migrate_path(root, current, target_version or '999.999.999', dry_run=False)
        # Also update lockfile
        write_lock(root)

    return {
        'current': current,
        'target': data['project']['version'],
        'applied': [s.description for s in steps],
        'dry_run': dry_run,
    }