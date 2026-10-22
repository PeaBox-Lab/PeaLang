from pealang.debugger import DebugSession

def test_conditional_breakpoint_true():
 d=DebugSession('let x = 2\nprint x',source_name='demo.pea',output=lambda x:None)
 d.add_breakpoint(2,'x == 2')
 e=d.start();assert e['reason']=='breakpoint' and e['line']==2

def test_conditional_breakpoint_false():
 d=DebugSession('let x = 2\nprint x',source_name='demo.pea',output=lambda x:None)
 d.add_breakpoint(2,'x == 3')
 assert d.start()['reason']=='end'

def test_hit_condition_parser():
 d=DebugSession('print 1',output=lambda x:None)
 assert d._hit_matches('3',3) and d._hit_matches('>=2',4) and d._hit_matches('%2',4)

def test_function_frame_capture():
 src='function add(a) {\n let b = 2\n return a + b\n}\nlet result = add(3)\n'
 d=DebugSession(src,source_name='frames.pea',output=lambda x:None);d.add_breakpoint(2)
 e=d.start();assert e['reason']=='breakpoint'
 stack=d.stack();assert stack[0]['name']=='add';assert d.variables('locals',stack[0]['id'])['a']==3

def test_exception_breakpoint():
 d=DebugSession('throw "boom"',source_name='bad.pea',output=lambda x:None);d.set_exception_breakpoints(['all'])
 e=d.start();assert e['reason']=='exception' and 'boom' in e['text']
