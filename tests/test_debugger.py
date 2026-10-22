
from pealang.debugger import DebugSession

def test_step_and_variables():
 s=DebugSession('let x = 2\nx += 3\nprint x',output=lambda x:None);e=s.step();assert e['line']==1 and s.variables()['x']==2;s.step();assert s.variables()['x']==5

def test_breakpoint_and_continue():
 s=DebugSession('let x = 1\nx += 1',output=lambda x:None);s.add_breakpoint(2);e=s.continue_run();assert e['reason']=='breakpoint' and e['line']==2;assert s.step()['reason']=='step'

def test_stack(): assert DebugSession('print 1').stack()[0]['name']=='<module>'
