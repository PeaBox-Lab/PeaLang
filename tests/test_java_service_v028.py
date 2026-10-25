

from pealang.runtime_service import RuntimeService

def test_health():assert RuntimeService().health()['status']=='UP'
def test_ready():assert RuntimeService().readiness()['status']=='READY'
def test_compile_cache():
 s=RuntimeService();a=s.compile('print 1');b=s.compile('print 1');assert a.ok and a.result['cache_key']==b.result['cache_key'] and len(s.cache)==1
def test_load_invoke():
 s=RuntimeService();r=s.load('math','function add(a,b){return a+b}\nexport add','math.pea');assert r.ok;call=s.invoke('math','add',[2,5]);assert call.ok and call.result==7
def test_unknown_module():assert not RuntimeService().invoke('missing','x').ok
def test_bad_semantics():assert not RuntimeService().compile('function f()->Int {\n return "bad"\n}').ok
def test_bad_operation():assert RuntimeService().handle({'operation':'x'})['error']['code']=='BAD_REQUEST'


