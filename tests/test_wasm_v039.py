

import pytest
from pealang import WasmPolicy,compile_peac_to_wasm,inspect_wasm,browser_loader_source
from pealang.compiler import compile_source_to_bytecode
def artifact():return compile_peac_to_wasm(compile_source_to_bytecode('print 1'))
def test_magic():assert artifact().to_bytes()[:8]==b'\x00asm\x01\x00\x00\x00'
def test_roundtrip():
 x=inspect_wasm(artifact().to_bytes());assert x['manifest']['format']=='PEAWASM' and x['peac']['format']=='PEAC'
def test_security_defaults():
 p=WasmPolicy();assert not p.allow_network and not p.allow_filesystem
def test_abi():assert inspect_wasm(artifact().to_bytes())['manifest']['abi']=='pea-browser-abi-1'
def test_policy():assert inspect_wasm(compile_peac_to_wasm(compile_source_to_bytecode('print 1'),WasmPolicy(max_fuel=10)).to_bytes())['manifest']['policy']['max_fuel']==10
def test_loader():assert 'WebAssembly.instantiate' in browser_loader_source()
def test_save(tmp_path):
 p=tmp_path/'a.wasm';artifact().save(p);assert p.read_bytes().startswith(b'\x00asm')
def test_invalid():
 with pytest.raises(ValueError):inspect_wasm(b'bad')


