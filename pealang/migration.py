"""Version-to-version source migration framework."""
from pathlib import Path
from dataclasses import dataclass
@dataclass
class MigrationChange:path:str;changed:bool;notes:list[str]
def migrate_text(text,from_version,to_version):
 notes=[];out=text
 if from_version<'0.35' and to_version>='0.35':notes.append('Review legacy standard library aliases and prefer std.* namespace')
 if from_version<'0.38' and to_version>='0.38':notes.append('Native test syntax is available; existing source remains compatible')
 return out,notes
def migrate_path(path,from_version,to_version,write=True):
 root=Path(path);files=[root] if root.is_file() else sorted(root.rglob('*.pea'));changes=[]
 for p in files:
  old=p.read_text(encoding='utf-8');new,notes=migrate_text(old,from_version,to_version)
  changed=new!=old
  if write and changed:p.write_text(new,encoding='utf-8')
  changes.append(MigrationChange(str(p),changed,notes))
 return changes

