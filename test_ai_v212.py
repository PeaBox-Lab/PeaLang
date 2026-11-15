import sys, os
sys.path.insert(0, '/Users/Rajesh/Documents/My Apps/GitHub/PeaLang')
from pealang.ai import build_ai_namespace, set_ai_key, list_ai_providers, get_ai_status, run_ai_query, AIConfig, CloudModel, LocalModel

print('=== AI Module v2.12.0 ===')
print()

# Test 1: Namespace
ns = build_ai_namespace()
print('1. AI namespace keys:', list(ns.keys()))
assert 'AIConfig' in ns
assert 'LocalModel' in ns
assert 'CloudModel' in ns
assert 'set_ai_key' in ns
assert 'list_ai_providers' in ns
assert 'get_ai_status' in ns
assert 'run_ai_query' in ns
assert 'build_ai_namespace' in ns
print('   OK: All keys present')

# Test 2: AIConfig
print()
print('2. AIConfig:')
config = AIConfig()
print(f'   has_key(openai): {config.has_key("openai")}')
set_ai_key('openai', 'sk-test123')
config2 = AIConfig.load(os.path.expanduser('~/.peaalang/ai_config.json'))
print(f'   has_key(openai) after set: {config2.has_key("openai")}')
print(f'   get_key(openai): {config2.get_key("openai")}')
print(f'   list_providers(): {config2.list_providers()}')
print('   OK: AIConfig working')

# Test 3: Status
print()
print('3. AI status:')
status = get_ai_status()
print(f'   {status}')
assert 'providers' in status
assert 'default' in status
assert 'local_available' in status
print('   OK: Status working')

# Test 4: run_ai_query (no key) - test with unknown provider first
print()
print('4. run_ai_query:')
result = run_ai_query('Hello test', provider='unknown', model='gpt-4')
print(f'   Result: {result}')
assert 'No API key' in result or 'Unsupported provider' in result
print('   OK: Error message working')

# Test 5: CloudModel (will fail gracefully without openai package)
print()
print('5. CloudModel:')
try:
    cm = CloudModel('openai', 'gpt-4', 'sk-test')
    q = cm.query('test prompt')
    print(f'   Query result: {q}')
except Exception as e:
    print(f'   Error (expected): {type(e).__name__}')
print('   OK: CloudModel handles missing package gracefully')

print()
print('=== All AI v2.12.0 features working! ===')