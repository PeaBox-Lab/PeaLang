


from __future__ import annotations
import json
from pathlib import Path
from .errors import PeaError
class SkillRegistry:
    def __init__(self,base_dir=None):self.base_dir=Path(base_dir or '.').resolve();self.skills={}
    def load(self,path):
        p=(self.base_dir/str(path)).resolve();data=json.loads(p.read_text(encoding='utf-8'))
        for key in ('name','prompt'):
            if key not in data:raise PeaError(f"Skill file requires '{key}'")
        self.skills[str(data['name'])]=data;return data
    def list(self):return sorted(self.skills)
    def get(self,name):
        if str(name) not in self.skills:raise PeaError(f"Skill '{name}' is not loaded")
        return self.skills[str(name)]
    def render(self,name,values=None):
        skill=self.get(name);text=str(skill['prompt']);values=dict(values or {})
        for k,v in values.items():text=text.replace('{'+str(k)+'}',str(v))
        return text



