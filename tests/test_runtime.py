import tempfile,unittest
from pathlib import Path
from pealang import execute,PeaError
class RuntimeTests(unittest.TestCase):
    def runpea(self,s,**kw):out=[];execute(s,output=out.append,**kw);return out
    def test_math(self):self.assertEqual(self.runpea('print 2 + 3 * 4'),['14'])
    def test_function(self):self.assertEqual(self.runpea('function add(a,b){return a+b}\nprint add(2,5)'),['7'])
    def test_loop(self):self.assertEqual(self.runpea('for x in range(1,4){print x}'),['1','2','3'])
    def test_list_dict(self):self.assertEqual(self.runpea('let x=[4,5]\nlet d={"a":9}\nprint x[1]+d["a"]'),['14'])
    def test_const(self):
        with self.assertRaises(PeaError):execute('const x=1\nx=2')
    def test_break_continue(self):self.assertEqual(self.runpea('for x in range(0,6){if x==1{continue}\nif x==4{break}\nprint x}'),['0','2','3'])
    def test_interpolation(self):self.assertEqual(self.runpea('let name="Pea"\nprint "Hello {name}, {2+3}!"'),['Hello Pea, 5!'])
    def test_property_and_assignment(self):self.assertEqual(self.runpea('let p={"name":"Rajesh"}\np.name="Pea"\nlet a=[1,2]\na[1]=9\nprint p.name+str(a[1])'),['Pea9'])
    def test_compound_index_assignment(self):self.assertEqual(self.runpea('let a=[4]\na[0]+=3\nprint a[0]'),['7'])
    def test_import(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,'util.pea').write_text('function twice(x){return x*2}',encoding='utf-8')
            self.assertEqual(self.runpea('import "util.pea"\nprint twice(5)',base_dir=d),['10'])
    def test_diagnostic_position(self):
        with self.assertRaisesRegex(PeaError,r'<input>:1:7:') : execute('print missing')
    def test_break_outside_loop(self):
        with self.assertRaises(PeaError):execute('break')
    def test_continue_outside_loop(self):
        with self.assertRaises(PeaError):execute('continue')
    def test_while_continue(self):
        self.assertEqual(self.runpea('let x=0\nwhile x<4{x+=1\nif x==2{continue}\nprint x}'),['1','3','4'])
    def test_interpolation_literal_braces(self):
        self.assertEqual(self.runpea('print \"{{Pea}} {1+1}\"'),['{Pea} 2'])
    def test_missing_property(self):
        with self.assertRaisesRegex(PeaError,"Property 'city' not found"):
            execute('let p={\"name\":\"Pea\"}\nprint p.city')
    def test_import_runs_once(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,'one.pea').write_text('print \"loaded\"',encoding='utf-8')
            self.assertEqual(self.runpea('import \"one.pea\"\nimport \"one.pea\"',base_dir=d),['loaded'])
    def test_missing_import(self):
        with self.assertRaisesRegex(PeaError,'Module not found'):
            execute('import \"missing.pea\"')
if __name__=='__main__':unittest.main()
