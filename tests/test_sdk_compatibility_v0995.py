import json
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_sdk_versions_and_peer_dependency():
 for f in ("typescript-sdk/package.json","react-sdk/package.json","browser-sdk/package.json"): assert json.loads((ROOT/f).read_text())["version"]=="0.99.6"
 assert json.loads((ROOT/"react-sdk/package.json").read_text())["peerDependencies"]["@pealang/client"]=="^0.99.6"
def test_modern_ts_configs():
 for f in ("typescript-sdk/tsconfig.json","react-sdk/tsconfig.json"):
  d=json.loads((ROOT/f).read_text());c=d["compilerOptions"];assert c["moduleResolution"]=="NodeNext" and c["rootDir"]=="src"
def test_required_workflows_present():
 for f in ("os-python-matrix.yml","security-scanners.yml","java-node-matrix.yml"): assert (ROOT/".github/workflows"/f).is_file()
