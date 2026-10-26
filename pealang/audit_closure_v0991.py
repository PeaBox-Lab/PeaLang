"""Repository-level audit closure checks for the PeaLang 1.0 line."""
from pathlib import Path
import json,re
SDK_FILES=("browser-sdk/package.json","typescript-sdk/package.json","react-sdk/package.json")
REQUIRED_DOCS=("docs/project/COMPONENT_STATUS_1_0.md","docs/project/INTERFACE_COMPLETENESS_0991.md","docs/KNOWN_LIMITATIONS_1_0.md","docs/project/FINAL_RELEASE_GATE_099.md")
def audit_repository(root):
 root=Path(root); failures=[]
 for rel in REQUIRED_DOCS:
  if not (root/rel).is_file(): failures.append(f"missing:{rel}")
 for rel in SDK_FILES:
  p=root/rel
  if p.is_file() and json.loads(p.read_text()).get("version")!="0.99.4": failures.append(f"version:{rel}")
 c=(root/"CHANGELOG.md").read_text()
 if c.count("# Changelog")!=1: failures.append("changelog-root-count")
 if c.count("## 0.35.0 - 2026-10-23")!=1: failures.append("changelog-035-count")
 classified=(root/"docs/project/INTERFACE_COMPLETENESS_0991.md").read_text()
 sites=[]
 for p in (root/"pealang").glob("*.py"):
  if p.name == "audit_closure_v0991.py": continue
  for n,line in enumerate(p.read_text(errors="replace").splitlines(),1):
   if "NotImplementedError" in line: sites.append(f"{p.relative_to(root)}:{n}")
 if len(sites)!=23: failures.append(f"interface-site-count:{len(sites)}")
 if "All 23" not in classified: failures.append("interface-classification")
 return {"passed":not failures,"failures":failures,"interface_sites":len(sites)}
