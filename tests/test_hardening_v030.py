from pathlib import Path
from pealang import compile_source_to_bytecode,VirtualMachine,Profiler,Coverage,Instrumentation,MemoryObserver,benchmark_source
from pealang.release_integrity import compare

def test_profiler_counts():
 p=Profiler().start();c=Coverage();VirtualMachine(output=lambda x:None,instrumentation=Instrumentation(p,c)).run(compile_source_to_bytecode('let x=1\nprint x','a.pea'));p.stop();r=p.report();assert r['instructions']>=4 and r['opcodes']['PRINT']==1
def test_coverage_lines():
 c=Coverage();VirtualMachine(output=lambda x:None,instrumentation=Instrumentation(coverage=c)).run(compile_source_to_bytecode('let x=1\nprint x','a.pea'));assert 1 in c.report()['a.pea'] and 2 in c.report()['a.pea']
def test_observer_events():
 o=MemoryObserver();VirtualMachine(output=lambda x:None,instrumentation=Instrumentation(observers=[o])).run(compile_source_to_bytecode('print 1'));assert o.events and o.events[0].name=='vm.instruction'
def test_benchmark():
 r=benchmark_source('let x=1\nprint x',3);assert r['iterations']==3 and r['min_ms']>=0 and r['max_ms']>=r['min_ms']
def test_release_compare(tmp_path):
 a=tmp_path/'a';b=tmp_path/'b';a.mkdir();b.mkdir();(a/'x').write_text('1');(b/'x').write_text('2');(b/'y').write_text('3');r=compare(a,b);assert r['added']==['y'] and r['removed']==[] and r['modified']==['x']
def test_differential_arithmetic():
 from pealang import execute
 src='function add(a,b){return a+b}\nprint add(2,5)';a=[];b=[];execute(src,output=a.append);VirtualMachine(output=b.append).run(compile_source_to_bytecode(src));assert [int(x) for x in a]==b

