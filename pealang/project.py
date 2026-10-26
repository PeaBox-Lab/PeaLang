



from __future__ import annotations
import json, re
from pathlib import Path
from .errors import PeaError
DEFAULT_MANIFEST={'project':{'name':'my-pea-project','version':'0.1.0','entry':'main.pea'},'dependencies':{}}
def load_manifest(start='.'):
    p=Path(start).resolve()
    if p.is_file():p=p.parent
    while True:
        f=p/'pea.json'
        if f.is_file():
            try:data=json.loads(f.read_text(encoding='utf-8'))
            except Exception as ex:raise PeaError(f'Invalid pea.json: {ex}') from ex
            project=data.get('project',{})
            for key in ('name','version','entry'):
                if key not in project:raise PeaError(f"pea.json project requires '{key}'")
            deps=data.get('dependencies',{})
            if not isinstance(deps,dict):raise PeaError('pea.json dependencies must be a dictionary')
            return f,data
        if p.parent==p:return None,None
        p=p.parent
def init_project(path='.',name=None):
    root=Path(path).resolve();root.mkdir(parents=True,exist_ok=True);manifest=root/'pea.json'
    if manifest.exists():raise PeaError('pea.json already exists')
    data=json.loads(json.dumps(DEFAULT_MANIFEST));data['project']['name']=name or root.name
    manifest.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    main=root/'main.pea'
    if not main.exists():main.write_text('print "Hello from {project.name}"\n'.replace('{project.name}',data['project']['name']),encoding='utf-8')
    (root/'modules').mkdir(exist_ok=True);return str(manifest)
def add_dependency(name,path,project_dir='.'):
    mf,data=load_manifest(project_dir)
    if not mf:raise PeaError('No pea.json found')
    dep_path=Path(path)
    if not dep_path.is_absolute():dep_path=(mf.parent/dep_path).resolve()
    if not dep_path.exists():raise PeaError(f'Dependency path not found: {path}')
    try:stored=str(dep_path.relative_to(mf.parent))
    except ValueError:stored=str(dep_path)
    data.setdefault('dependencies',{})[str(name)]={'path':stored}
    mf.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');return data['dependencies'][str(name)]
def remove_dependency(name,project_dir='.'):
    mf,data=load_manifest(project_dir)
    if not mf:raise PeaError('No pea.json found')
    data.setdefault('dependencies',{}).pop(str(name),None);mf.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');return True
def project_info(start='.'):
    mf,data=load_manifest(start)
    if not mf:raise PeaError('No pea.json found')
    return {'root':str(mf.parent),'manifest':str(mf),**data}
def resolve_module(spec,current_dir,project_root=None,dependencies=None):
    spec=str(spec)
    if spec.startswith('./') or spec.startswith('../') or '/' in spec or spec.endswith('.pea'):
        p=(Path(current_dir)/spec).resolve()
        if p.suffix!='.pea':p=p.with_suffix('.pea')
        return p
    root=Path(project_root or current_dir)
    local=(root/'modules'/spec).with_suffix('.pea')
    if local.is_file():return local.resolve()
    dep=(dependencies or {}).get(spec)
    if dep:
        base=Path(dep.get('path',''))
        if not base.is_absolute():base=(root/base).resolve()
        dm,dd=load_manifest(base)
        if dm:
            return (dm.parent/dd['project']['entry']).resolve()
        p=base
        if p.is_dir():p=p/'main.pea'
        return p.resolve()
    return (Path(current_dir)/spec).with_suffix('.pea').resolve()




