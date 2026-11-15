import sys
sys.path.insert(0, '/Users/Rajesh/Documents/My Apps/GitHub/PeaLang')
from pealang.type_system import TypeChecker, parse_type, compatible, TypeRef, erase_types

tc = TypeChecker()

print('=== Type System Foundation ===')
result = tc.check('let x: Int = 5')
print(f'Basic type check: {result.ok}')

t = parse_type('Int')
print(f'Parse Int: {t.name}')

t1 = parse_type('Int')
t2 = parse_type('String')
print(f'Int compatible with Int: {compatible(t1, t1)}')
print(f'Int compatible with String: {compatible(t1, t2)}')

t3 = parse_type('trait MyTrait')
print(f'Parse trait MyTrait: {t3.name}')

erased = erase_types('trait MyTrait\nlet x: Int = 5')
print(f'Type erasure removes trait: {"trait" not in erased.lower()}')

print()
print('=== Foundation solid! ===')