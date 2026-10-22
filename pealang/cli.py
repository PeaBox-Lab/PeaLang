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
        if c=='typecheck':
            from .type_system import TypeChecker
            files=discover_pea(argv[1:] or ['.']);errors=0
            for f in files:
                result=TypeChecker().check(Path(f).read_text(encoding='utf-8'),str(f))
                for d in result.diagnostics:print(f'{f}:{d}')
                errors+=sum(x.severity=='error' for x in result.diagnostics)
            print(f'Typecheck: {len(files)} file(s), {errors} error(s)')
            return 1 if errors else 0
        if c=='repl':return repl()
        if c=='init':
            p=argparse.ArgumentParser(prog='pea init');p.add_argument('path',nargs='?',default='.');p.add_argument('--name');a=p.parse_args(argv[1:]);print(init_project(a.path,a.name));return 0
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
        if c=='run':
            p=argparse.ArgumentParser(prog='pea run');p.add_argument('file');p.add_argument('--allow-process',action='store_true');a=p.parse_args(argv[1:]);return run_file(a.file,a.allow_process)
        if c=='fmt':
            p=argparse.ArgumentParser(prog='pea fmt');p.add_argument('paths',nargs='+');p.add_argument('--check',action='store_true');a=p.parse_args(argv[1:]);files=discover_pea(a.paths);changed=0
            for f in files:
                ok=format_file(f,check=a.check)
                if a.check and not ok:print(f);changed+=1
                elif not a.check:print(f'formatted {f}')
            return 1 if a.check and changed else 0
        if c=='check':
            p=argparse.ArgumentParser(prog='pea check');p.add_argument('paths',nargs='+');a=p.parse_args(argv[1:]);errors=0
            for f in discover_pea(a.paths):
                for d in check_source(f.read_text(encoding='utf-8'),str(f)):print(d.render(str(f)));errors+=d.severity=='error'
            return 1 if errors else 0
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
        if len(argv)!=1:print('Usage: pea [compile|dis|vm|typecheck|init|project|add|remove|start|run|fmt|check|test|docs|repl] ...',file=sys.stderr);return 2
        return run_file(argv[0],allow)
    except (PeaError,OSError) as e:print(f'Error: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
