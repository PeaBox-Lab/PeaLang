
from pealang.debugger import DebugSession
def test_breakpoint():
 d=DebugSession('let x = 1\nx += 2',output=lambda x:None);d.add_breakpoint(1);e=d.start();assert e['reason']=='breakpoint';assert d.continue_run()['reason']=='end';assert d.variables()['x']==3
def test_evaluate():
 d=DebugSession('let x = 4',output=lambda x:None);d.start();assert d.evaluate('x + 1')==5
