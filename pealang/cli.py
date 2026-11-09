import argparse,sys,json

from pathlib import Path

from .runtime import execute,Interpreter,PeaError

from .tooling import format_file,check_source,discover_pea,generate_docs

from .project import load_manifest,init_project,add_dependency,remove_dependency,project_info

from . import __version__

def repl():

    print(f'PeaLang {__version__} - type :help for help or exit to quit');vm=Interpreter();buf=''

    while True:

        try:line=input('... ' if buf else 'pea> ')

        except (EOFError,KeyboardInterrupt):print();break

        if line.strip() in ('exit','quit') and not buf:break

        if line.strip()==':help' and not buf:print(':help  :vars  :clear  exit');continue

        if line.strip()==':clear' and not buf:vm=Interpreter();print('State cleared.');continue

        if line.strip()==':vars' and not buf:print(', '.join(sorted(k for k in vm.global_env.values if not k.startswith('_'))));continue

        buf+=line+'\n'

        if buf.count('{')>buf.count('}'):continue

        try:execute(buf,interpreter=vm,source_name='<repl>')

        except PeaError as e:print(f'Error: {e}',file=sys.stderr)

        buf=''

def run_file(path,allow_process=False):

    p=Path(path).resolve();mf,data=load_manifest(p)

    kwargs={}

    if mf:kwargs={'project_root':mf.parent,'dependencies':data.get('dependencies',{})}

    try:execute(p.read_text(encoding='utf-8'),source_name=str(p),base_dir=p.parent,allow_process=allow_process,**kwargs)

    except (PeaError,OSError) as e:print(f'Error: {e}',file=sys.stderr);return 1

    return 0

def main(argv=None):

    argv=list(sys.argv[1:] if argv is None else argv)

    if not argv:return repl()

    if argv[0] in ('--version','-V'):print(f'PeaLang {__version__}');return 0

    c=argv[0]

    try:

        if c=='stdlib':

            from .stdlib import stdlib_manifest

            print(json.dumps(stdlib_manifest(),indent=2));return 0

        if c=='spec':

            from .specification import verify_spec

            report=verify_spec();print(json.dumps(report,indent=2));return 0 if report['ok'] else 1

        if c=='features':

            from .compatibility import FEATURES

            for name,f in sorted(FEATURES.items()):print(f'{name}: {f.stability.value} (since {f.since})')

            return 0

        if c=='keygen-ed25519':

            from .ed25519_signing import generate_ed25519_keypair

            private=argv[1] if len(argv)>1 else 'pea-ed25519.key';public=argv[2] if len(argv)>2 else private+'.pub';kid,_,_=generate_ed25519_keypair(private,public);print(kid);return 0

        if c=='sign-ed25519':

            from .ed25519_signing import sign_ed25519

            p,_=sign_ed25519(argv[1],argv[2]);print(p);return 0

        if c=='verify-ed25519':

            from .ed25519_signing import verify_ed25519

            verify_ed25519(argv[1],argv[2],argv[3]);print('Ed25519 signature: valid');return 0

        if c=='keygen':

            from .signing import generate_key

            path=argv[1] if len(argv)>1 else 'pea-signing.key';print(generate_key(path));return 0

        if c=='sign':

            from .signing import sign_package

            p,_=sign_package(argv[1],argv[2]);print(p);return 0

        if c=='verify':

            from .signing import verify_package

            verify_package(argv[1],argv[2],argv[3]);print('Signature: valid');return 0

        if c=='trust':

            from .signing import TrustStore

            store=TrustStore(argv[1]);kid=store.trust_key(argv[2],argv[3] if len(argv)>3 else None);print(kid);return 0

        if c=='profile':

            from .compiler import compile_source_to_bytecode

            from .vm import VirtualMachine

            from .observability import Profiler,Coverage,Instrumentation

            path=Path(argv[1]);prof=Profiler().start();cov=Coverage();vm=VirtualMachine(instrumentation=Instrumentation(prof,cov));vm.run(compile_source_to_bytecode(path.read_text(encoding='utf-8'),str(path)));prof.stop();print(json.dumps({'profile':prof.report(),'coverage':cov.report()},indent=2));return 0

        if c=='benchmark':

            from .benchmark import benchmark_source

            path=Path(argv[1]);print(json.dumps(benchmark_source(path.read_text(encoding='utf-8'),20,str(path)),indent=2));return 0

        if c=='serve':

            from .runtime_http import serve

            host='127.0.0.1';port=8787

            for x in argv[1:]:

                if x.startswith('--host='):host=x.split('=',1)[1]

                if x.startswith('--port='):port=int(x.split('=',1)[1])

            print(f'PeaLang runtime service on http://{host}:{port}');return serve(host,port)

        if c=='pkg-init':

            from .package_manager import init_manifest

            print(init_manifest(argv[1] if len(argv)>1 else '.'));return 0

        if c in ('lock','install','audit','build'):

            from .package_manager import write_lock,install,audit,build_package

            root=argv[1] if len(argv)>1 else '.'

            if c=='lock':p,_=write_lock(root);print(p);return 0

            if c=='install':print('Installed: '+', '.join(install(root)));return 0

            if c=='audit':

                issues=audit(root)

                if issues:

                    for x in issues:print('AUDIT '+x)

                    return 1

                print('Audit: clean');return 0

            if c=='build':p,h=build_package(root);print(f'{p}\nsha256 {h}');return 0

        if c=='compile':

            from .compiler import compile_source_to_bytecode

            p=argparse.ArgumentParser(prog='pea compile');p.add_argument('file');p.add_argument('-o','--output');a=p.parse_args(argv[1:])

            src=Path(a.file);out=Path(a.output) if a.output else src.with_suffix('.peac');compile_source_to_bytecode(src.read_text(encoding='utf-8'),str(src)).save(out);print(out);return 0

        if c=='dis':

            from .bytecode import BytecodeModule

            from .disassembler import disassemble

            p=argparse.ArgumentParser(prog='pea dis');p.add_argument('file');a=p.parse_args(argv[1:]);print(disassemble(BytecodeModule.load(a.file)),end='');return 0

        if c=='vm':

            from .bytecode import BytecodeModule

            from .compiler import compile_source_to_bytecode

            from .vm import VirtualMachine

            p=argparse.ArgumentParser(prog='pea vm');p.add_argument('file');p.add_argument('--max-instructions',type=int,default=100000);a=p.parse_args(argv[1:]);path=Path(a.file);m=BytecodeModule.load(path) if path.suffix=='.peac' else compile_source_to_bytecode(path.read_text(encoding='utf-8'),str(path));VirtualMachine(print,a.max_instructions).run(m);return 0

        if c=='semantic':

            from .type_system import SemanticAnalyzer

            files=discover_pea(argv[1:] or ['.']);errors=warnings=0

            for f in files:

                result=SemanticAnalyzer().analyze(Path(f).read_text(encoding='utf-8'),str(f))

                for d in result.diagnostics:print(f'{f}:{d}')

                errors+=sum(x.severity=='error' for x in result.diagnostics);warnings+=sum(x.severity=='warning' for x in result.diagnostics)

            print(f'Semantic analysis: {len(files)} file(s), {errors} error(s), {warnings} warning(s)')

            return 1 if errors else 0

        if c=='typecheck-project':

            from .type_system import analyze_project

            files=discover_pea(argv[1:] or ['.']);report=analyze_project(files);print(json.dumps({'files':report['files'],'function_contracts':len(report['functions']),'record_contracts':len(report['records']),'diagnostics':len(report['diagnostics'])},indent=2));return 1 if report['diagnostics'] else 0

        if c=='typecheck':

            from .type_system import TypeChecker

            files=discover_pea(argv[1:] or ['.']);errors=0

            for f in files:

                result=TypeChecker().check(Path(f).read_text(encoding='utf-8'),str(f))

                for d in result.diagnostics:print(f'{f}:{d}')

                errors+=sum(x.severity=='error' for x in result.diagnostics)

            print(f'Typecheck: {len(files)} file(s), {errors} error(s)')

            return 1 if errors else 0

        if c=='readiness':

            from .readiness import default_report

            report=default_report().to_dict();print(json.dumps(report,indent=2));return 0 if report['ok'] else 1

        if c=='conformance':

            from .conformance import conformance_report

            report=conformance_report();print(json.dumps(report,indent=2));return 0 if report['conformance']['ok'] and report['fuzz']['ok'] else 1

        if c=='wasm-build':

            from .compiler import compile_source_to_bytecode

            from .wasm import compile_peac_to_wasm

            ip=Path(argv[1]);op=Path(argv[2] if len(argv)>2 else ip.with_suffix('.wasm'));compile_peac_to_wasm(compile_source_to_bytecode(ip.read_text(encoding='utf-8'),str(ip))).save(op);print(op);return 0

        if c=='wasm-inspect':

            from .wasm import inspect_wasm

            print(json.dumps(inspect_wasm(argv[1])['manifest'],indent=2));return 0

        if c=='test':

            import time

            from .native_testing import run_paths,coverage_summary

            args=argv[1:];flt=None;coverage='--coverage' in args;watch='--watch' in args

            clean=[];i=0

            while i<len(args):

                if args[i]=='--filter' and i+1<len(args):flt=args[i+1];i+=2;continue

                if args[i].startswith('--filter='):flt=args[i].split('=',1)[1];i+=1;continue

                if args[i] not in ('--coverage','--watch'):clean.append(args[i])

                i+=1

            files=discover_pea(clean or ['tests','.']);results=run_paths(files,flt or getattr(a,'filter_k',None))

            for r in results:print(('PASS' if r.passed else 'FAIL')+f' {r.name} ({r.elapsed_ms:.1f} ms)'+((' - '+r.error) if r.error else ''))

            if coverage:print(json.dumps(coverage_summary(files,results),indent=2))

            if watch:print('Watch mode baseline enabled; rerun pea test --watch after changes in environments without filesystem events.')

            print(f'Tests: {sum(r.passed for r in results)} passed, {sum(not r.passed for r in results)} failed');return 1 if any(not r.passed for r in results) else 0

        if c=='migrate':

            from .migration import migrate_path

            p=argparse.ArgumentParser(prog='pea migrate');p.add_argument('--from',dest='src',required=True);p.add_argument('--to',dest='dst',required=True);p.add_argument('path',nargs='?',default='.');p.add_argument('--check',action='store_true');a=p.parse_args(argv[1:]);changes=migrate_path(a.path,a.src,a.dst,not a.check);print(json.dumps([x.__dict__ for x in changes],indent=2));return 0

        if c=='repl':return repl()

        if c in ('init','new'):
            prog = 'pea new' if c=='new' else 'pea init'
            p=argparse.ArgumentParser(prog=prog);p.add_argument('path',nargs='?',default='.');p.add_argument('--name');p.add_argument('--template',default='default');a=p.parse_args(argv[1:]);print(init_project(a.path,a.name,a.template));return 0
        if c=='serve-web':
            p=argparse.ArgumentParser(prog='pea serve-web');p.add_argument('file');p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8080);a=p.parse_args(argv[1:])
            from .interpreter import Interpreter
            from .parser import parse_source
            from pathlib import Path as _P
            src=_P(a.file).read_text(encoding='utf-8'); vm=Interpreter(); vm.run(parse_source(src,str(_P(a.file).resolve())),str(_P(a.file).resolve()))
            app=vm.global_env.values.get('app') or vm.global_env.values.get('application')
            if app is None:
                print('No `app` variable found after running file',file=sys.stderr); return 1
            if not hasattr(app,'serve'):
                print('`app` does not support serve()',file=sys.stderr); return 1
            print(f'Serving {a.file} on http://{a.host}:{a.port}'); app.serve(a.host,a.port); return 0

        if c=='quickstart':
            from .ux import quickstart
            print(quickstart()); return 0

        if c=='doctor':

            from .ux import doctor

            print(json.dumps(doctor(),indent=2));return 0

        if c=='templates':

            from .project import TEMPLATES

            print('\\n'.join(sorted(TEMPLATES)));return 0
        if c=='eval':
            p=argparse.ArgumentParser(prog='pea eval');p.add_argument('code',nargs='?');p.add_argument('-e','--expr');p.add_argument('-f','--file');a=p.parse_args(argv[1:])
            src=a.expr or a.code
            if a.file: src=Path(a.file).read_text(encoding='utf-8')
            if not src:print('Usage: pea eval -e "print 1+1" | pea eval -f file.pea',file=sys.stderr);return 2
            execute(src,source_name=a.file or '<eval>');return 0
        if c in ('version','-v'):
            if '--json' in argv[1:]: print(json.dumps({'version':__version__},indent=2))
            else: print(f'PeaLang {__version__}')
            return 0
        if c=='info':
            from .stdlib import stdlib_manifest
            sm=stdlib_manifest();mods=sm.get('modules',sm)
            info={'version':__version__,'stdlib':list(mods.keys()) if isinstance(mods,dict) else mods,'commands':['run','eval','repl','check','lint','fmt','test','compile','vm','dis','init','new','serve-web','doctor','templates','info','project','serve','stdlib','typecheck','docs','analyze','web-openapi','openapi','hash','tree','env','quickstart']}
            print(json.dumps(info,indent=2));return 0

        if c=='project':print(json.dumps(project_info(argv[1] if len(argv)>1 else '.'),indent=2));return 0

        if c=='add':

            p=argparse.ArgumentParser(prog='pea add');p.add_argument('name');p.add_argument('path');p.add_argument('--project',default='.');a=p.parse_args(argv[1:]);print(json.dumps(add_dependency(a.name,a.path,a.project),indent=2));return 0

        if c=='remove':

            p=argparse.ArgumentParser(prog='pea remove');p.add_argument('name');p.add_argument('--project',default='.');a=p.parse_args(argv[1:]);remove_dependency(a.name,a.project);return 0

        if c=='start':

            mf,data=load_manifest(argv[1] if len(argv)>1 else '.')

            if not mf:raise PeaError('No pea.json found')

            return run_file(mf.parent/data['project']['entry'])

        if c=='vm-dap':

            from .vm_dap import serve;return serve()

        if c=='dap':

            from .dap import serve;return serve()

        if c=='debug':

            from .debugger import DebugSession

            path=Path(argv[1]);d=DebugSession(path.read_text(encoding='utf-8'),str(path),output=print,base_dir=path.parent)

            for x in argv[2:]:

                if x.startswith('--break='):d.add_breakpoint(int(x.split('=',1)[1]))

            print(json.dumps(d.start(),indent=2,default=str));return 0

        if c=='analyze':
            p=argparse.ArgumentParser(prog='pea analyze');p.add_argument('path');p.add_argument('--json',action='store_true');p.add_argument('--head',type=int,default=None);a=p.parse_args(argv[1:])
            from .analysis import profile as _profile, from_csv_text, from_json_text, head as _head
            txt=Path(a.path).read_text(encoding='utf-8')
            try: data=from_json_text(txt)
            except Exception: data=from_csv_text(txt)
            if a.head is not None: data=_head(data,a.head)
            result=_profile(data)
            print(json.dumps(result,indent=2,default=str) if a.json else json.dumps(result,indent=2,default=str));return 0

        if c in ('web-openapi','openapi'):
            p=argparse.ArgumentParser(prog='pea web-openapi');p.add_argument('file');p.add_argument('--title',default='PeaLang App');p.add_argument('--version',dest='ver',default='1.0.0');a=p.parse_args(argv[1:])
            from .interpreter import Interpreter
            from .parser import parse_source
            from .web import PeaWebApp
            src=Path(a.file).read_text(encoding='utf-8'); vm=Interpreter(base_dir=Path(a.file).resolve().parent)
            _orig=PeaWebApp.serve
            try:
                PeaWebApp.serve=lambda self,*aa,**kk: None
                vm.run(parse_source(src,str(Path(a.file).resolve())),str(Path(a.file).resolve()))
            finally:
                PeaWebApp.serve=_orig
            app=vm.global_env.values.get('app') or vm.global_env.values.get('application')
            if app is None or not hasattr(app,'openapi'):
                print('No web app found (define `app = web.app()`)',file=sys.stderr); return 1
            print(json.dumps(app.openapi(a.title,a.ver),indent=2,default=str)); return 0

        if c=='hash':
            p=argparse.ArgumentParser(prog='pea hash');p.add_argument('file');p.add_argument('--algo',default='sha256');a=p.parse_args(argv[1:])
            import hashlib
            h=hashlib.new(a.algo)
            with open(a.file,'rb') as f:
                for chunk in iter(lambda:f.read(65536),b''): h.update(chunk)
            print(h.hexdigest()); return 0

        if c=='env':
            p=argparse.ArgumentParser(prog='pea env');p.add_argument('name',nargs='?');p.add_argument('--keys',action='store_true');a=p.parse_args(argv[1:])
            import os
            if a.keys:
                for k in sorted(os.environ.keys()): print(k)
                return 0
            if not a.name:
                print('Usage: pea env <NAME> | pea env --keys', file=sys.stderr); return 2
            v=os.environ.get(a.name)
            if v is None: return 1
            print(v); return 0

        if c=='tree':
            p=argparse.ArgumentParser(prog='pea tree');p.add_argument('path',nargs='?',default='.');a=p.parse_args(argv[1:])
            files=sorted(str(f) for f in discover_pea([a.path]))
            for f in files: print(f)
            print(f'{len(files)} .pea file(s)'); return 0

        if c=='run':

            p=argparse.ArgumentParser(prog='pea run');p.add_argument('file');p.add_argument('--allow-process',action='store_true');a=p.parse_args(argv[1:]);return run_file(a.file,a.allow_process)

        if c=='fmt':

            p=argparse.ArgumentParser(prog='pea fmt');p.add_argument('paths',nargs='+');p.add_argument('--check',action='store_true');a=p.parse_args(argv[1:]);files=discover_pea(a.paths);changed=0

            for f in files:

                ok=format_file(f,check=a.check)

                if a.check and not ok:print(f);changed+=1

                elif not a.check:print(f'formatted {f}')

            return 1 if a.check and changed else 0

        if c in ('check','lint'):

            p=argparse.ArgumentParser(prog=f'pea {c}');p.add_argument('paths',nargs='+');p.add_argument('--json',action='store_true');a=p.parse_args(argv[1:]);errors=warnings=0;items=[]

            for f in discover_pea(a.paths):

                for d in check_source(f.read_text(encoding='utf-8'),str(f)):
                    if a.json: items.append({'file':str(f),'severity':d.severity,'message':getattr(d,'message',str(d)),'line':getattr(d,'line',None),'column':getattr(d,'col',getattr(d,'column',None))})
                    else: print(d.render(str(f)))
                    errors+=d.severity=='error';warnings+=d.severity!='error'

            if a.json: print(json.dumps({'ok':errors==0,'errors':errors,'warnings':warnings,'items':items},indent=2))
            elif c=='lint':print(f'Lint: {errors} error(s), {warnings} warning(s)')

            return 1 if errors else 0

        if c=='wasm-build':

            from .compiler import compile_source_to_bytecode

            from .wasm import compile_peac_to_wasm

            ip=Path(argv[1]);op=Path(argv[2] if len(argv)>2 else ip.with_suffix('.wasm'));compile_peac_to_wasm(compile_source_to_bytecode(ip.read_text(encoding='utf-8'),str(ip))).save(op);print(op);return 0

        if c=='wasm-inspect':

            from .wasm import inspect_wasm

            print(json.dumps(inspect_wasm(argv[1])['manifest'],indent=2));return 0

        if c=='test':

            p=argparse.ArgumentParser(prog='pea test');p.add_argument('paths',nargs='*',default=['pea_tests']);a=p.parse_args(argv[1:]);files=discover_pea(a.paths);failed=0

            for f in files:

                out=[]

                try:

                    execute(f.read_text(encoding='utf-8'),output=out.append,source_name=str(f),base_dir=f.parent)

                    expected=f.with_suffix('.out')

                    if expected.exists() and out!=expected.read_text(encoding='utf-8').splitlines():failed+=1;print(f'FAIL {f}: output mismatch');continue

                    print(f'PASS {f}')

                except Exception as e:failed+=1;print(f'FAIL {f}: {e}')

            print(f'{len(files)-failed} passed, {failed} failed');return 1 if failed else 0

        if c=='docs':

            p=argparse.ArgumentParser(prog='pea docs');p.add_argument('path');p.add_argument('-o','--output');a=p.parse_args(argv[1:]);doc=generate_docs(Path(a.path).read_text(encoding='utf-8'),a.path)

            if a.output:Path(a.output).write_text(doc,encoding='utf-8');print(a.output)

            else:print(doc,end='')

            return 0

        if len(argv)==1 and argv[0].endswith('.peac'):

            from .bytecode import BytecodeModule

            from .vm import VirtualMachine

            VirtualMachine(print).run(BytecodeModule.load(argv[0]));return 0

        allow='--allow-process' in argv

        if allow:argv.remove('--allow-process')

        if len(argv)!=1:print('Usage: pea [run|eval|repl|check|lint|fmt|test|compile|vm|dis|init|new|serve-web|doctor|quickstart|templates|info|project|docs|analyze|web-openapi|hash|tree|env|typecheck|stdlib] ...',file=sys.stderr);return 2

        return run_file(argv[0],allow)

    except (PeaError,OSError) as e:print(f'Error: {e}',file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())

