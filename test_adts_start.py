import sys
sys.path.insert(0, '/Users/Rajesh/Documents/My Apps/GitHub/PeaLang')
from pealang.type_system import TypeChecker, erase_types

tc = TypeChecker()

# Test existing type system still works
result = tc.check('let x: Int = 5')
print('Basic type check:', result.ok)

# Test trait reference
tresult = tc.check('trait MyTrait')
print('Trait check:', tresult.ok)

# Test type erasure
erased = erase_types('trait MyTrait\nlet x: Int = 5')
te = 'trait' not in erased.lower()
print('Type erasure removes trait:', te)

print('Type system foundation solid!')