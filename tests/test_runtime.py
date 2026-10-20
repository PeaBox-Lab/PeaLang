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

class StandardLibraryTests(unittest.TestCase):
    def runpea(self,source,**kwargs):
        out=[];execute(source,output=out.append,**kwargs);return out
    def test_json_namespace(self):
        self.assertEqual(self.runpea('let x=json.parse("{{\\"a\\": 7}}")\nprint x.a\nprint json.stringify(x,0)'),['7','{"a": 7}'])
    def test_path_namespace(self):
        self.assertEqual(self.runpea('print path.extension(path.join("data","staff.csv"))'),['.csv'])
    def test_regex_namespace(self):
        self.assertEqual(self.runpea('print regex.match("^[A-Z]+$","PEA")\nprint regex.replace("[0-9]+","#","A12")'),['true','A#'])
    def test_env_namespace(self):
        import os
        os.environ['PEALANG_TEST']='ready'
        self.assertEqual(self.runpea('print env.get("PEALANG_TEST")\nprint env.has("PEALANG_MISSING")'),['ready','false'])
    def test_file_json_csv(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            j=Path(d,'data.json');c=Path(d,'data.csv')
            source=f'json.write("{j}",{{"name":"Rajesh"}})\nlet obj=json.read("{j}")\ncsv.write("{c}",[{{"name":obj.name,"score":9}}])\nlet rows=csv.read("{c}")\nprint rows[0].name+":"+rows[0].score'
            self.assertEqual(self.runpea(source),['Rajesh:9'])
    def test_datetime(self):
        self.assertEqual(self.runpea('print datetime.format(datetime.parse("2026-10-20T00:00:00"),"%Y-%m-%d")'),['2026-10-20'])
    def test_process_disabled_by_default(self):
        with self.assertRaisesRegex(PeaError,'Process execution is disabled'):
            execute('process.run("python",["--version"])')
    def test_process_opt_in(self):
        out=[];execute('let r=process.run("python",["--version"])\nprint r.ok',output=out.append,allow_process=True)
        self.assertEqual(out,['true'])
    def test_http_local_server(self):
        import http.server,threading
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                body=b'{"service":"pea"}';self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            def log_message(self,*args):pass
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            url=f'http://127.0.0.1:{server.server_port}/';self.assertEqual(self.runpea(f'let r=http.get("{url}")\nprint r.status\nprint http.json(r).service'),['200','pea'])
        finally:server.shutdown();server.server_close()

if __name__=='__main__':unittest.main()

