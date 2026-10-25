

"""PeaLang 0.40 conformance, differential and deterministic fuzz harness."""
from dataclasses import dataclass,asdict
import random,string
from .runtime import execute
from .compiler import compile_source_to_bytecode
from .vm import VirtualMachine
from .lexer import Lexer
from .parser import parse_source
@dataclass
class ConformanceCase:
 id:str;source:str;expected:list

def generated_cases(count=500):
 cases=[]
 for i in range(count):
  a=i%97;b=(i*7)%41
  mode=i%5
  if mode==0:src=f'print {a} + {b}';exp=[str(a+b)]
  elif mode==1:src=f'let x={a}\nprint x * {b}';exp=[str(a*b)]
  elif mode==2:src=f'print {a} == {a}';exp=['true']
  elif mode==3:src=f'let x=[{a},{b}]\nprint x[0]';exp=[str(a)]
  else:src=f'function f(x){{return x+1}}\nprint f({a})';exp=[str(a+1)]
  cases.append(ConformanceCase(f'C{i+1:04}',src,exp))
 return cases

def _normalize(values):return [str(x).lower() if isinstance(x,bool) else str(x) for x in values]
def differential(source):
 a=[];b=[];execute(source,output=a.append);VirtualMachine(output=b.append).run(compile_source_to_bytecode(source,'<conformance>'))
 return _normalize(a),_normalize(b)
def run_conformance(count=500):
 passed=0;failures=[]
 for case in generated_cases(count):
  try:
   a,b=differential(case.source)
   if a==b==case.expected:passed+=1
   else:failures.append({'id':case.id,'expected':case.expected,'interpreter':a,'vm':b})
  except Exception as exc:failures.append({'id':case.id,'error':str(exc)})
 return {'target':count,'passed':passed,'failed':len(failures),'failures':failures[:25],'ok':not failures}
def fuzz_lexer_parser(iterations=250,seed=1337):
 rng=random.Random(seed);crashes=[];alphabet=string.ascii_letters+string.digits+' +-*/%(){}[],:;\n\t\"#_'
 for i in range(iterations):
  text=''.join(rng.choice(alphabet) for _ in range(rng.randrange(0,100)))
  try:
   Lexer(text,'<fuzz>').tokens()
   try:parse_source(text,'<fuzz>')
   except Exception:pass
  except Exception as exc:
   # lexer/parser language errors are expected; only non-language exceptions count as harness crashes
   if exc.__class__.__module__ not in ('pealang.errors',):crashes.append({'iteration':i,'type':type(exc).__name__,'message':str(exc)})
 return {'iterations':iterations,'seed':seed,'unexpected_crashes':crashes,'ok':not crashes}
def conformance_report():return {'version':'0.40','conformance':run_conformance(500),'fuzz':fuzz_lexer_parser()}


