import unittest
from pealang import execute, PeaError
class RuntimeTests(unittest.TestCase):
    def runpea(self,s):
        out=[]; execute(s,output=out.append); return out
    def test_math(self): self.assertEqual(self.runpea('print 2 + 3 * 4'),['14'])
    def test_function(self): self.assertEqual(self.runpea('function add(a,b){return a+b}\nprint add(2,5)'),['7'])
    def test_loop(self): self.assertEqual(self.runpea('for x in range(1,4){print x}'),['1','2','3'])
    def test_list_dict(self): self.assertEqual(self.runpea('let x=[4,5]\nlet d={"a":9}\nprint x[1]+d["a"]'),['14'])
    def test_const(self):
        with self.assertRaises(PeaError): execute('const x=1\nx=2')
if __name__=='__main__':unittest.main()
