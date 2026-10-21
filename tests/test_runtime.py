import tempfile,unittest
from pathlib import Path
from pealang import execute,PeaError
from pealang.tooling import format_source,check_source,generate_docs
from pealang.project import init_project,load_manifest,add_dependency,resolve_module
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


class DeveloperToolingTests(unittest.TestCase):
    def test_formatter_idempotent(self):
        source='let x=1\nif x==1{print "yes"}'
        once=format_source(source);self.assertEqual(once,format_source(once));self.assertIn('if x == 1 {',once)
    def test_checker_undefined(self):
        ds=check_source('print missng');self.assertTrue(any(d.code=='P101' and d.severity=='error' for d in ds))
    def test_checker_unused(self):
        ds=check_source('let unused=1');self.assertTrue(any(d.code=='P104' for d in ds))
    def test_docs_generator(self):
        doc=generate_docs('function add(a,b){return a+b}','math.pea');self.assertIn('add(a, b)',doc)


class WorkflowConcurrencyTests(unittest.TestCase):
    def runpea(self,source):
        out=[];execute(source,output=out.append);return out
    def test_assert_pass(self):execute('assert 2 + 2 == 4')
    def test_assert_fail_message(self):
        with self.assertRaisesRegex(PeaError,'math failed'):execute('assert false, "math failed"')
    def test_parallel_expressions(self):
        self.assertEqual(self.runpea('let r=parallel { 2+3 4*5 }\nprint r[0]\nprint r[1]'),['5','20'])
    def test_parallel_empty(self):self.assertEqual(self.runpea('let r=parallel {}\nprint len(r)'),['0'])
    def test_workflow_helpers(self):
        self.assertEqual(self.runpea('let a=workflow.step("load", 5)\nlet r=workflow.result("demo",[a])\nprint r.ok\nprint r.steps[0].value'),['true','5'])


class AIWorkflowTests(unittest.TestCase):
    def runpea(self,source,**kwargs):out=[];execute(source,output=out.append,**kwargs);return out
    def test_ai_mock_ask(self):self.assertEqual(self.runpea('ai.configure({"provider":"mock","model":"demo"})\nlet r=ai.ask("hello")\nprint r.provider\nprint r.text'),['mock','hello'])
    def test_ai_extract_mock(self):self.assertEqual(self.runpea('let r=ai.extract({"name":"Pea","n":3},{"name":"string","n":"number"})\nprint r.name+str(r.n)'),['Pea3'])
    def test_ai_validate_failure(self):
        with self.assertRaisesRegex(PeaError,"must be number"):execute('ai.validate({"n":"x"},{"n":"number"})')
    def test_ai_unknown_provider(self):
        with self.assertRaisesRegex(PeaError,'Unknown AI provider'):execute('ai.configure({"provider":"unknown"})\nai.ask("x")')
    def test_ai_credential_external(self):
        with self.assertRaisesRegex(PeaError,'credential environment variable'):execute('ai.configure({"provider":"openai-compatible","base_url":"http://127.0.0.1:1/v1","api_key_env":"PEALANG_TEST_MISSING_KEY"})\nai.ask("x")')
    def test_skill_registry(self):
        import tempfile,json
        with tempfile.TemporaryDirectory() as d:
            Path(d,'s.json').write_text(json.dumps({'name':'hello','prompt':'Hello {name}'}),encoding='utf-8')
            self.assertEqual(self.runpea('skill.load("s.json")\nprint skill.render("hello",{"name":"Rajesh"})',base_dir=d),['Hello Rajesh'])


class ProjectModelTests(unittest.TestCase):
    def test_init_manifest(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            init_project(d,'demo');mf,data=load_manifest(d);self.assertEqual(data['project']['name'],'demo');self.assertTrue(Path(d,'main.pea').is_file())
    def test_local_module_resolution(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            init_project(d,'demo');Path(d,'modules','math.pea').write_text('function double(x){return x*2}',encoding='utf-8');mf,data=load_manifest(d);out=[];execute('import "math"\nprint double(5)',output=out.append,base_dir=d,project_root=d,dependencies=data['dependencies']);self.assertEqual(out,['10'])
    def test_path_dependency(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            app=Path(d,'app');lib=Path(d,'lib');init_project(app,'app');init_project(lib,'lib');Path(lib,'main.pea').write_text('function triple(x){return x*3}',encoding='utf-8');add_dependency('mylib',str(lib),app);mf,data=load_manifest(app);out=[];execute('import "mylib"\nprint triple(4)',output=out.append,base_dir=app,project_root=app,dependencies=data['dependencies']);self.assertEqual(out,['12'])
    def test_manifest_validation(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            Path(d,'pea.json').write_text('{"project":{"name":"x"}}',encoding='utf-8')
            with self.assertRaises(PeaError):load_manifest(d)


class AgentToolTests(unittest.TestCase):
    def runpea(self,source):out=[];execute(source,output=out.append);return out
    def test_agent_mock_run(self):
        self.assertEqual(self.runpea('ai.configure({"provider":"mock"})\nlet a=agent.define("helper","Help",[])\nlet r=agent.run(a,"hello")\nprint r.agent\nprint r.provider'),['helper','mock'])
    def test_registered_tool_call(self):
        self.assertEqual(self.runpea('function double(x){return x*2}\ntool.register("double",double)\nlet a=agent.define("calc","",["double"])\nprint agent.tool(a,"double",[6])'),['12'])
    def test_tool_denied(self):
        with self.assertRaisesRegex(PeaError,'not permitted'):execute('function double(x){return x*2}\ntool.register("double",double)\nlet a=agent.define("calc","",[])\nagent.tool(a,"double",[6])')
    def test_tool_unknown(self):
        with self.assertRaisesRegex(PeaError,'not registered'):execute('let a=agent.define("x","",["missing"])\nagent.tool(a,"missing",[])')
    def test_tool_metadata(self):
        self.assertEqual(self.runpea('function ping(){return "pong"}\ntool.register("ping",ping,"Health check","safe")\nlet d=tool.describe("ping")\nprint d.permission'),['safe'])


class LanguageMaturityTests(unittest.TestCase):
    def runpea(self,source):out=[];execute(source,output=out.append);return out
    def test_default_arguments(self):self.assertEqual(self.runpea('function greet(name,word="Hello"){return word+" "+name}\nprint greet("Rajesh")\nprint greet("Rajesh","Hi")'),['Hello Rajesh','Hi Rajesh'])
    def test_try_catch(self):self.assertEqual(self.runpea('try { throw "boom" } catch err { print err.message }'),['boom'])
    def test_try_finally(self):self.assertEqual(self.runpea('try { print "work" } finally { print "done" }'),['work','done'])
    def test_catch_runtime_error(self):self.assertEqual(self.runpea('try { print missing } catch err { print "caught" }'),['caught'])
    def test_throw_uncaught(self):
        with self.assertRaisesRegex(PeaError,'stop'):execute('throw "stop"')


class ModuleNamespaceTests(unittest.TestCase):
    def runpea(self,source,**kwargs):out=[];execute(source,output=out.append,**kwargs);return out
    def test_alias_namespace_export(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            Path(d,'math.pea').write_text('function square(x){return x*x}\nfunction hidden(){return 9}\nexport square',encoding='utf-8')
            self.assertEqual(self.runpea('import "math.pea" as math\nprint math.square(6)',base_dir=d),['36'])
    def test_unexported_hidden(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            Path(d,'m.pea').write_text('function hidden(){return 9}',encoding='utf-8')
            with self.assertRaisesRegex(PeaError,"Property 'hidden' not found"):execute('import "m.pea" as m\nprint m.hidden()',base_dir=d)
    def test_legacy_import_compat(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            Path(d,'m.pea').write_text('function old(){return 7}',encoding='utf-8')
            self.assertEqual(self.runpea('import "m.pea"\nprint old()',base_dir=d),['7'])
    def test_export_outside_module(self):
        with self.assertRaisesRegex(PeaError,'only valid inside'):execute('let x=1\nexport x')

if __name__=='__main__':unittest.main()

