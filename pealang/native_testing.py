
"""Native PeaLang test runner for test/expect syntax."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import re,time
from .runtime import execute
@dataclass
class NativeTestResult:
 name:str;file:str;passed:bool;elapsed_ms:float;error:str|None=None
TEST_RE=re.compile(r'test\s+"([^"]+)"\s*\{')
def _blocks(source):
 out=[]
 for m in TEST_RE.finditer(source):
  depth=1;i=m.end()
  while i<len(source) and depth:
   if source[i]=='{':depth+=1
   elif source[i]=='}':depth-=1
   i+=1
  if depth:raise SyntaxError(f'Unclosed test block: {m.group(1)}')
  out.append((m.group(1),source[m.end():i-1],m.start(),i))
 return out
def _lower(body):
 lines=[]
 for line in body.splitlines():
  x=line.strip()
  if x.startswith('expect '):lines.append('assert '+x[7:])
  elif x:lines.append(line)
 return '\n'.join(lines)
def split_tests(source):
 blocks=_blocks(source);masked=source
 for _,_,a,b in reversed(blocks):masked=masked[:a]+masked[b:]
 return masked,[(n,_lower(b)) for n,b,_,_ in blocks]
def run_source_tests(source,file='<memory>',filter_text=None):
 setup,tests=split_tests(source);results=[]
 for name,body in tests:
  if filter_text and filter_text.lower() not in name.lower():continue
  started=time.perf_counter()
  try:execute(setup+'\n'+body,source_name=file);results.append(NativeTestResult(name,file,True,(time.perf_counter()-started)*1000))
  except Exception as exc:results.append(NativeTestResult(name,file,False,(time.perf_counter()-started)*1000,str(exc)))
 return results
def run_paths(paths,filter_text=None):
 results=[]
 for raw in paths:
  p=Path(raw);results.extend(run_source_tests(p.read_text(encoding='utf-8'),str(p),filter_text))
 return results
def coverage_summary(paths,results):
 total_lines=executable=0
 for raw in paths:
  for line in Path(raw).read_text(encoding='utf-8').splitlines():
   if line.strip() and not line.lstrip().startswith(('#','test ')):total_lines+=1
 executable=total_lines
 passed=sum(x.passed for x in results)
 return {'files':len(paths),'executable_lines':executable,'tests':len(results),'passed':passed,'failed':len(results)-passed,'mode':'test-aware baseline; VM line coverage remains experimental'}

