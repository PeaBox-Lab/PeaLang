import argparse,sys,json

from pathlib import Path

from .runtime import execute,Interpreter,PeaError

from .tooling import format_file,check_source,discover_pea,generate_docs

from .project import load_manifest,init_project,add_dependency,remove_dependency,project_info

from . import __version__
from .package_manager import load_pea_toml

def _print_error(e):
    frames = getattr(e, "frames", None)
    if frames:
        print(f"Error: {e}", file=sys.stderr)
        print("Traceback (most recent call last):", file=sys.stderr)
        for frame in frames:
            src = frame.get("source", "<input>")
            line = frame.get("line", 0)
            name = frame.get("name", "<anonymous>")
            print(f"  File \"{src}\", line {line}, in {name}", file=sys.stderr)
    else:
        print(f"Error: {e}", file=sys.stderr)


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

        except PeaError as e:_print_error(e)

        buf=''

def run_file(path,allow_process=False):

    p=Path(path).resolve();mf,data=load_manifest(p)

    kwargs={}

    if mf:kwargs={'project_root':mf.parent,'dependencies':data.get('dependencies',{})}

    try:execute(p.read_text(encoding='utf-8'),source_name=str(p),base_dir=p.parent,allow_process=allow_process,**kwargs)

    except (PeaError,OSError) as e:_print_error(e);return 1

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
            import json as _json
            from pathlib import Path as _Path

            path=_Path(argv[1]);iterations=20;baseline_path=None;save_baseline_path=None
            i=2
            while i+1<len(argv):
                if argv[i]=='--iterations':iterations=int(argv[i+1]);i+=2;continue
                if argv[i]=='--baseline':baseline_path=argv[i+1];i+=2;continue
                if argv[i]=='--save-baseline':save_baseline_path=argv[i+1];i+=2;continue
                break

            if not path.exists():
                print(f'benchmark source not found: {path}');return 1

            result=benchmark_source(path.read_text(encoding='utf-8'),iterations,str(path))

            if save_baseline_path is not None:
                with open(str(save_baseline_path),'w',encoding='utf-8') as bf:_json.dump(result,bf,indent=2)
                print(f'saved baseline to {save_baseline_path}');return 0

            if baseline_path is not None and _Path(baseline_path).exists():
                with open(str(baseline_path),encoding='utf-8') as bf:baseline=_json.load(bf)
                baseline_median=float(baseline.get('median_ms') or baseline.get('mean_ms') or 0)
                current_median=float(result.get('median_ms') or result.get('mean_ms') or 0)
                regression_pct=0.0 if baseline_median==0 else ((current_median-baseline_median)/baseline_median)*100
                ok=regression_pct<=10.0
                print(_json.dumps({'baseline_median_ms':baseline_median,'current_median_ms':current_median,'regression_pct':regression_pct,'threshold_pct':10.0,'ok':ok},indent=2))
                return 0 if ok else 1

            print(json.dumps(result,indent=2));return 0

        if c=='serve':

            from .runtime_http import serve

            host='127.0.0.1';port=8787

            for x in argv[1:]:

                if x.startswith('--host='):host=x.split('=',1)[1]

                if x.startswith('--port='):port=int(x.split('=',1)[1])

            print(f'PeaLang runtime service on http://{host}:{port}');return serve(host,port)

        if c=='sdk':

            from .host_bindings import HOST_SDK_NAMES, build_host_sdk_namespace

            sub=argv[1] if len(argv)>1 else None

            if sub=='list':

                print("Available host SDKs: "+", ".join(sorted(HOST_SDK_NAMES.keys())))

                return 0

            if sub=='generate':

                lang=argv[2] if len(argv)>2 else None

                target=argv[3] if len(argv)>3 else f"{lang}-sdk"

                if lang not in HOST_SDK_NAMES:

                    print(f"Unknown SDK language: {lang} (available: {', '.join(sorted(HOST_SDK_NAMES.keys()))})")

                    return 1

                out=HOST_SDK_NAMES[lang](target)

                print(f"Generated {lang} SDK at {out['root']}:")

                for f in out['files']:

                    print(f"  {f}")

                return 0

            print(f"Usage: pea sdk list|generate <lang> <dir>|codegen <source.pea> <lang> <dir>\nAvailable SDKs: {', '.join(sorted(HOST_SDK_NAMES.keys()))}")

            return 1

        if c=='sdk-codegen':

            from .host_bindings import generate_sdk_from_source

            source_path=argv[1] if len(argv)>1 else None

            lang=argv[2] if len(argv)>2 else None

            target=argv[3] if len(argv)>3 else f"{lang}-sdk"

            if not source_path or not lang:

                print("Usage: pea sdk-codegen <source.pea> <lang> <dir>")

                return 1

            src_path=Path(source_path)

            if not src_path.exists():

                print(f"source not found: {src_path}")

                return 1

            source=src_path.read_text(encoding="utf-8")

            out=generate_sdk_from_source(source, lang, target)

            if "error" in out:

                print(out["error"])

                return 1

            print(f"Generated {lang} SDK from {src_path} at {out['root']}:")

            for f in out['files']:

                print(f"  {f}")

            return 0

        if c=='pkg-init':

            from .package_manager import init_manifest

            print(init_manifest(argv[1] if len(argv)>1 else '.'));return 0

        if c in ('lock','install','uninstall','audit','quality','build','deps','update','outdated','clean'):

            from .package_manager import write_lock,install,uninstall,audit,build_package,install_remote,quality_check,check_lock,list_dependencies,outdated,dependency_tree,clean

            # Find root: first non-flag argument after argv[0]
            rootnext=[a for a in argv[1:] if not a.startswith('-')]
            root=rootnext[0] if rootnext else '.'

            if c=='lock':
                if '--check' in argv:
                    result=check_lock(root)
                    print(json.dumps(result,indent=2));return 0 if result['ok'] else 1
                p,_=write_lock(root);print(p);return 0

            if c=='deps':
                if '--tree' in argv[1:]:
                    result=dependency_tree(root)
                    print(json.dumps(result,indent=2));return 0
                print(json.dumps(list_dependencies(root),indent=2));return 0

            if c=='install':
                name=argv[1] if len(argv)>1 else None
                version=argv[2] if len(argv)>2 else None
                if not name:
                    print('Usage: pea install <name> [@version]');return 1
                result=install_remote(name, version, token=None)
                print(f'Installed: {name}')
                return 0

            if c=='uninstall':
                name=argv[1] if len(argv)>1 else None
                proj=argv[2] if len(argv)>2 else '.'
                if not name:
                    print('Usage: pea uninstall <name> [path]');return 1
                result=uninstall(name, proj)
                print(json.dumps(result,indent=2))
                return 0 if result['removed'] else 1

            if c=='quality':
                from .package_manager import quality_check
                root=argv[1] if len(argv)>1 else '.'
                result=quality_check(root)
                print(json.dumps(result,indent=2))
                return 0 if result['ok'] else 1

            if c=='audit':
                # Package audit for pea.toml projects; repo closure audit otherwise.
                if '--write-interface-doc' in argv[1:] or not (Path(root)/'pea.toml').exists():
                    p=argparse.ArgumentParser(prog='pea audit')
                    p.add_argument('path',nargs='?',default='.')
                    p.add_argument('--json',action='store_true')
                    p.add_argument('--write-interface-doc',action='store_true')
                    a=p.parse_args(argv[1:])
                    from .audit_closure_v0991 import audit_repository, write_interface_markdown
                    if a.write_interface_doc:
                        out=write_interface_markdown(a.path)
                        if not a.json: print(out)
                    report=audit_repository(a.path)
                    print(json.dumps(report,indent=2));return 0 if report.get('passed') else 1
                issues=audit(root)
                if issues:
                    for x in issues:print('AUDIT '+x)
                    return 1
                print('Audit: clean');return 0

            if c=='update':
                from .package_manager import update
                args=[a for a in argv[1:] if not a.startswith('-')]
                root=args[0] if args else '.'
                result=update(root)
                print(json.dumps(result,indent=2));return 0 if result['ok'] else 1

            if c=='outdated':
                from .package_manager import outdated
                root=argv[1] if len(argv)>1 and not argv[1].startswith('-') else '.'
                result=outdated(root)
                print(json.dumps(result,indent=2));return 0 if result['ok'] else 1

            if c=='clean':
                args=[a for a in argv[1:] if not a.startswith('-')]
                root=args[0] if args else '.'
                result=clean(root, '--all' in argv[1:])
                print(json.dumps(result,indent=2));return 0

            if c=='build':
                p=argparse.ArgumentParser(prog='pea build')
                p.add_argument('root',nargs='?',default='.')
                p.add_argument('-o','--output')
                p.add_argument('--library',action='store_true',help='Build a library package (.pelib)')
                a=p.parse_args(argv[1:])
                root_path=a.root
                if a.library:
                    from .package_manager import build_library
                    out,h=build_library(root_path,a.output)
                    print(f'{out}\nsha256 {h}')
                else:
                    out,h=build_package(root_path,a.output)
                    print(f'{out}\nsha256 {h}')
                return 0

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
            from .native_testing import run_paths,coverage_summary,to_junit_xml
            p=argparse.ArgumentParser(prog='pea test')
            p.add_argument('paths',nargs='*',default=['tests','.'])
            p.add_argument('--filter',help='Filter tests by name pattern')
            p.add_argument('--coverage',action='store_true',help='Show coverage summary')
            p.add_argument('--watch',action='store_true',help='Watch mode (re-run on file changes)')
            p.add_argument('--junit',help='Output JUnit XML to file')
            p.add_argument('--json',action='store_true',help='Output results as JSON')
            p.add_argument('--legacy',action='store_true',help='Run legacy tests (execute .pea files and compare output to .out files)')
            a=p.parse_args(argv[1:])
            if a.legacy:
                # Legacy test mode: run .pea files and compare output to .out files
                files=discover_pea(a.paths)
                failed=0
                results=[]
                for f in files:
                    src=f.read_text(encoding='utf-8')
                    out_file=f.with_suffix('.out')
                    expected=out_file.read_text(encoding='utf-8').splitlines() if out_file.exists() else None
                    out=[]
                    try:
                        execute(src,output=out.append,source_name=str(f),base_dir=f.parent)
                    except Exception as e:
                        out=[f'ERROR: {e}']
                    passed = expected is None or out==expected
                    results.append({'name': f.name, 'file': str(f), 'passed': passed, 'elapsed_ms': 0, 'error': None if passed else 'output mismatch', 'line': 0, 'describe': 'legacy'})
                    if not passed:
                        failed+=1
                        print(f'FAIL {f}: output mismatch')
                        print('Expected:',expected)
                        print('Got:',out)
                    else:
                        print(f'PASS {f}')
                print(f'{len(files)-failed} passed, {failed} failed')
                if a.junit:
                    from .native_testing import to_junit_xml
                    from pealang.native_testing import NativeTestResult
                    native_results = [NativeTestResult(r['name'], r['file'], r['passed'], r['elapsed_ms'], r['error'], r['line'], r['describe']) for r in results]
                    xml=to_junit_xml(native_results)
                    Path(a.junit).write_text(xml,encoding='utf-8')
                    print(f'JUnit XML written to {a.junit}')
                return 1 if failed else 0
            # Native test mode
            files=discover_pea(a.paths);results=run_paths(files,a.filter)
            if a.json:
                print(json.dumps([{
                    'name':r.name,'file':r.file,'passed':r.passed,
                    'elapsed_ms':r.elapsed_ms,'error':r.error,'line':r.line,'describe':r.describe
                } for r in results],indent=2))
            else:
                for r in results:print(('PASS' if r.passed else 'FAIL')+f' {r.name} ({r.elapsed_ms:.1f} ms)'+((' - '+r.error) if r.error else ''))
            if a.coverage:print(json.dumps(coverage_summary(files,results),indent=2))
            if a.junit:
                xml=to_junit_xml(results)
                Path(a.junit).write_text(xml,encoding='utf-8')
                print(f'JUnit XML written to {a.junit}')
            if a.watch:print('Watch mode baseline enabled; rerun pea test --watch after changes in environments without filesystem events.')
            print(f'Tests: {sum(r.passed for r in results)} passed, {sum(not r.passed for r in results)} failed');return 1 if any(not r.passed for r in results) else 0

        if c=='migrate':

            from .migration import migrate_path

            p=argparse.ArgumentParser(prog='pea migrate');p.add_argument('--from',dest='src',required=True);p.add_argument('--to',dest='dst',required=True);p.add_argument('path',nargs='?',default='.');p.add_argument('--check',action='store_true');a=p.parse_args(argv[1:]);changes=migrate_path(a.path,a.src,a.dst,not a.check);print(json.dumps([x.__dict__ for x in changes],indent=2));return 0

        if c=='upgrade':
            from .project import upgrade_project
            p=argparse.ArgumentParser(prog='pea upgrade')
            p.add_argument('path',nargs='?',default='.')
            p.add_argument('--target')
            p.add_argument('--dry-run',action='store_true')
            p.add_argument('--check-lock',action='store_true')
            a=p.parse_args(argv[1:])
            result=upgrade_project(a.path,a.target,a.dry_run)
            if a.check_lock:
                from .project import verify_lock
                try:
                    verify_lock(a.path)
                    result['lock_verified'] = True
                except Exception as e:
                    result['lock_verified'] = False
                    result['lock_error'] = str(e)
            print(json.dumps(result,indent=2))
            return 0 if result.get('applied') or result.get('current') == result.get('target') else 1

        if c=='repl':return repl()

        if c in ('init','new'):
            prog = 'pea new' if c=='new' else 'pea init'
            p=argparse.ArgumentParser(prog=prog)
            p.add_argument('path',nargs='?',default='.')
            p.add_argument('--name')
            p.add_argument('--template',default='default')
            p.add_argument('--var', action='append', default=[], help='Template variables: --var key=value')
            a=p.parse_args(argv[1:])
            vars_dict = {}
            for v in a.var:
                if '=' in v:
                    k, val = v.split('=', 1)
                    vars_dict[k] = val
            print(init_project(a.path, a.name, a.template, vars_dict if vars_dict else None))
            return 0
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
        if c=='scaffold':
            p=argparse.ArgumentParser(prog='pea scaffold',description='Generate a backend or full-stack project skeleton')
            p.add_argument('target',help='framework (fastapi|flask|express|gin|django) or "fullstack"')
            p.add_argument('path',help='output directory')
            p.add_argument('--port',type=int,default=8000)
            p.add_argument('--frontend',default='react')
            p.add_argument('--backend',default='fastapi',help='backend framework for fullstack scaffolds')
            a=p.parse_args(argv[1:])
            from .frameworks import write_scaffold
            fw=a.target.lower();kind='fullstack' if fw=='fullstack' else 'backend'
            framework=fw if kind=='backend' else a.backend.lower()
            name=Path(a.path).resolve().name or 'service'
            out=write_scaffold(name,kind=kind,target_dir=a.path,framework=framework,port=a.port,frontend=a.frontend)
            print(json.dumps(out,indent=2));return 0 if 'error' not in out else 1

        if c=='doctor':

            from .ux import doctor
            p=argparse.ArgumentParser(prog='pea doctor');p.add_argument('path',nargs='?',default='.');a=p.parse_args(argv[1:])
            print(json.dumps(doctor(a.path),indent=2));return 0

        if c in ('health','project-health','check-project'):
            p=argparse.ArgumentParser(prog='pea health')
            p.add_argument('path',nargs='?',default='.')
            p.add_argument('--json',action='store_true')
            p.add_argument('--max-files',type=int,default=50)
            a=p.parse_args(argv[1:])
            from .devx import project_check
            report=project_check(a.path,max_files=a.max_files)
            if a.json:
                print(json.dumps(report,indent=2))
            else:
                totals=report.get('totals',{})
                print(f"Project: {report.get('project','')}")
                print(f"Files: {totals.get('files',0)}  Errors: {totals.get('errors',0)}  Warnings: {totals.get('warnings',0)}  OK: {totals.get('ok',False)}")
                for f in report.get('files',[]):
                    if f.get('diagnostic_count',0) or not f.get('ok',True):
                        print(f"  - {f.get('file')}: health={f.get('health')} errors={f.get('counts',{}).get('error',0)} warnings={f.get('counts',{}).get('warning',0)}")
            return 0 if report.get('totals',{}).get('ok',True) else 1

        if c=='diagnose':
            p=argparse.ArgumentParser(prog='pea diagnose')
            p.add_argument('file')
            p.add_argument('--json',action='store_true')
            a=p.parse_args(argv[1:])
            from .devx import diagnose_source
            try:
                src=Path(a.file).read_text(encoding='utf-8')
                report=diagnose_source(src, str(a.file))
            except Exception as e:
                report={'source':str(a.file),'ok':False,'health':0,'counts':{'error':1,'warning':0,'info':0},'diagnostics':[{'code':'READ','message':str(e),'line':0,'column':0,'severity':'error','origin':'read'}]}
            if a.json:
                print(json.dumps(report,indent=2))
            else:
                counts=report.get('counts',{})
                print(f"Source: {report.get('source','')}")
                print(f"Health: {report.get('health',0)}  Errors: {counts.get('error',0)}  Warnings: {counts.get('warning',0)}  OK: {report.get('ok',False)}")
                for d in report.get('diagnostics',[]):
                    loc=f"{d.get('line',0)}:{d.get('column',0)}" if d.get('line') else ''
                    print(f"  - [{d.get('severity')}] {d.get('code','')} {loc} {d.get('message','')}".rstrip())
            return 0 if report.get('ok',False) else 1

        if c=='help':
            p=argparse.ArgumentParser(prog='pea help');p.add_argument('topic',nargs='?');a=p.parse_args(argv[1:])
            from .help import help as pea_help
            print(pea_help(a.topic));return 0

        if c=='templates':

            from .project import TEMPLATES

            print('\n'.join(sorted(TEMPLATES)));return 0
        if c=='eval':
            p=argparse.ArgumentParser(prog='pea eval');p.add_argument('code',nargs='?');p.add_argument('-e','--expr');p.add_argument('-f','--file');a=p.parse_args(argv[1:])
            src=a.expr or a.code
            if a.file: src=Path(a.file).read_text(encoding='utf-8')
            if not src:print('Usage: pea eval -e "print 1+1" | pea eval -f file.pea',file=sys.stderr);return 2
            execute(src,source_name=a.file or '<eval>');return 0
        if c in ('version','-v'):
            if '--json' in argv[1:]:
                print(json.dumps({'version':__version__},indent=2))
            elif c=='-v' or (len(argv)>1 and argv[1]=='-v'):
                print(f'PeaLang {__version__}')
            elif len(argv)>1:
                # Version for a specific project/library
                path=argv[1]
                root=Path(path).resolve()
                mf,data=load_pea_toml(root)
                name=data['project']['name'];version=data['project']['version']
                print(f'Project "{name}" version: {version}')
            else:
                print(f'PeaLang {__version__}')
            return 0
        if c=='info':
            if len(argv)>1:
                # Package info from registry
                import urllib.request, urllib.error, json as _json

                name=argv[1]
                registry='http://127.0.0.1:8788'

                i=2
                while i+1<len(argv):
                    if argv[i]=='--registry':registry=argv[i+1];i+=2;continue
                    i+=1

                url=f'{registry}/api/v1/packages/{name}'
                try:
                    with urllib.request.urlopen(url) as resp:
                        info=_json.loads(resp.read().decode())
                        print(f'Package: {info["name"]}')
                        for v in info.get('versions',[]):
                            print(f'  {v["version"]} (sha256={v["sha256"][:16]}..., published={v.get("published","?")})')
                except urllib.error.HTTPError as e:
                    if e.code==404:
                        print(f'Package {name} not found')
                    else:
                        print(f'Info failed: {e.code} {e.read().decode()}')
                    return 1
                except Exception as e:
                    print(f'Info failed: {e}');return 1

                return 0
            else:
                from .stdlib import stdlib_manifest
                sm=stdlib_manifest();mods=sm.get('modules',sm)
                info={'version':__version__,'stdlib':list(mods.keys()) if isinstance(mods,dict) else mods,'commands':['run','eval','repl','check','lint','fmt','test','compile','vm','dis','init','new','serve-web','doctor','health','diagnose','help','templates','info','project','serve','stdlib','typecheck','typecheck-project','docs','analyze','web-openapi','openapi','openapi-contract','hash','tree','env','quickstart','scaffold','readiness','audit']}
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

        if c=='openapi-contract':
            p=argparse.ArgumentParser(prog='pea openapi-contract')
            p.add_argument('file',help='service contract JSON file')
            p.add_argument('--out')
            p.add_argument('--title')
            p.add_argument('--version',dest='ver')
            p.add_argument('--no-errors',action='store_true')
            a=p.parse_args(argv[1:])
            from .frameworks import service_contract_to_openapi
            contract=json.loads(Path(a.file).read_text(encoding='utf-8'))
            spec=service_contract_to_openapi(contract, title=a.title, version=a.ver, include_error_responses=not a.no_errors)
            out=json.dumps(spec, indent=2, sort_keys=True)
            if a.out:
                Path(a.out).write_text(out+'\n', encoding='utf-8')
                print(a.out)
            else:
                print(out)
            return 0 if 'error' not in spec else 1

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

        

        if c=='docs':

            p=argparse.ArgumentParser(prog='pea docs');p.add_argument('path');p.add_argument('-o','--output');a=p.parse_args(argv[1:]);doc=generate_docs(Path(a.path).read_text(encoding='utf-8'),a.path)

            if a.output:Path(a.output).write_text(doc,encoding='utf-8');print(a.output)

            else:print(doc,end='')

            return 0

        if c=='registry':

            from .registry_server import serve

            sub=argv[1] if len(argv)>1 else None

            if sub=='serve':

                host='127.0.0.1';port=8788;storage='./registry-storage';name='pealang'

                private_key_path=None;public_key_path=None

                i=2

                while i+1<len(argv):

                    if argv[i]=='--host':host=argv[i+1];i+=2;continue

                    if argv[i]=='--port':port=int(argv[i+1]);i+=2;continue

                    if argv[i]=='--storage':storage=argv[i+1];i+=2;continue

                    if argv[i]=='--name':name=argv[i+1];i+=2;continue

                    if argv[i]=='--private-key':private_key_path=argv[i+1];i+=2;continue

                    if argv[i]=='--public-key':public_key_path=argv[i+1];i+=2;continue

                    i+=1

                serve(host=host,port=port,storage_dir=storage,registry_name=name,

                      private_key_path=private_key_path,

                      public_key_path=public_key_path)

                return 0

            if sub=='register-publisher':

                token=argv[2] if len(argv)>2 else None

                publisher=argv[3] if len(argv)>3 else None

                if not token or not publisher:

                    print('Usage: pea registry register-publisher <token> <publisher-id>');return 1

                from .registry_server import RegistryServer

                srv=RegistryServer('./registry-storage')

                srv.register_publisher(token,publisher)

                print(f'Registered publisher {publisher}')

                return 0

            print('Usage: pea registry serve [--host HOST] [--port PORT] [--storage DIR] [--name NAME]');return 1

        if c=='ext':

            from .extension_registry import ExtensionRegistry

            sub=argv[1] if len(argv)>1 else None

            if sub=='list':

                from .interpreter import Interpreter

                interp=Interpreter()

                ns=interp.extension_registry.list_all()

                print('Extension functions:')

                for name in ns['functions']:

                    print(f'  {name}')

                print('Extension types:')

                for name in ns['types']:

                    print(f'  {name}')

                print('Extension operators:')

                for name in ns['operators']:

                    print(f'  {name}')

                print('Extension namespaces:')

                for name in ns['namespaces']:

                    print(f'  {name}')

                print('Loaded modules:')

                for name in ns['loaded_modules']:

                    print(f'  {name}')

                return 0

            if sub=='load':

                mod_name=argv[2] if len(argv)>2 else None

                if not mod_name:

                    print('Usage: pea ext load <module_name>');return 1

                from .interpreter import Interpreter

                interp=Interpreter()

                try:

                    mod=__import__(mod_name)

                    interp.extension_registry.register_module(mod_name,mod)

                    # Register functions in global env

                    for name,fn in interp.extension_registry.functions.items():

                        if fn.func is not None:

                            interp.global_env.define(name,fn.func,True)

                    print(f'Loaded extension module: {mod_name}')

                except ImportError as e:

                    print(f'Failed to load extension module: {e}');return 1

                return 0

            if sub=='info':

                name=argv[2] if len(argv)>2 else None

                if not name:

                    print('Usage: pea ext info <name>');return 1

                from .interpreter import Interpreter

                interp=Interpreter()

                ext_func=interp.extension_registry.get_function(name)

                ext_type=interp.extension_registry.get_type(name)

                ext_op=interp.extension_registry.get_operator(name)

                ext_ns=interp.extension_registry.get_namespace(name)

                if ext_func:

                    print(f'Function: {ext_func.name}')

                    print(f'  Arg count: {ext_func.arg_count}')

                    print(f'  Doc: {ext_func.doc}')

                elif ext_type:

                    print(f'Type: {ext_type.name}')

                    print(f'  Methods: {", ".join(ext_type.methods.keys())}')

                    print(f'  Doc: {ext_type.doc}')

                elif ext_op:

                    print(f'Operator: {ext_op.symbol}')

                    print(f'  Precedence: {ext_op.precedence}')

                    print(f'  Doc: {ext_op.doc}')

                elif ext_ns:

                    print(f'Namespace: {ext_ns.name}')

                    print(f'  Symbols: {", ".join(ext_ns.symbols.keys())}')

                else:

                    print(f'Extension not found: {name}');return 1

                return 0

            if sub=='type':

                from .interpreter import Interpreter

                name=argv[2] if len(argv)>2 else None

                if not name:

                    print('Usage: pea ext type <name>');return 1

                interp=Interpreter()

                ts=interp.extension_type_system

                if ts is None:

                    print(f'Extension type system not available');return 1

                if ts.has_type(name):

                    type_ref=ts.get_type_ref(name)

                    methods=ts.list_types()

                    if name in methods:

                        ext_type=interp.extension_registry.get_type(name)

                        print(f'Type: {name}')

                        print(f'  Methods: {", ".join(sorted(ext_type.methods.keys()))}')

                        print(f'  Doc: {ext_type.doc}')

                    else:

                        print(f'Type: {name}')

                        print(f'  No extension type registered')

                else:

                    print(f'Extension type not found: {name}');return 1

                return 0

            if sub=='deprecate':

                from .extension_lifecycle import ExtensionLifecycleManager

                name=argv[2] if len(argv)>2 else None
                version=argv[3] if len(argv)>3 else None

                if not name or not version:

                    print('Usage: pea ext deprecate <name> <version> [--message <msg>] [--replacement <name>] [--migration-guide <path>] [--removal-version <ver>] [--removal-date <date>]');return 1

                # Parse optional args
                message=""
                replacement=None
                migration_guide=None
                removal_version=None
                removal_date=None

                i=4
                while i+1<len(argv):

                    if argv[i]=='--message':message=argv[i+1];i+=2;continue

                    if argv[i]=='--replacement':replacement=argv[i+1];i+=2;continue

                    if argv[i]=='--migration-guide':migration_guide=argv[i+1];i+=2;continue

                    if argv[i]=='--removal-version':removal_version=argv[i+1];i+=2;continue

                    if argv[i]=='--removal-date':removal_date=int(argv[i+1]);i+=2;continue

                    i+=1

                lm=ExtensionLifecycleManager()

                dep=lm.deprecate(name, version, message=message, replacement=replacement, migration_guide=migration_guide, removal_version=removal_version, removal_date=removal_date)

                print(f'Deprecated {name}@{version}')

                if dep.message:

                    print(f'  Message: {dep.message}')

                if dep.replacement:

                    print(f'  Replacement: {dep.replacement}')

                if dep.migration_guide:

                    print(f'  Migration guide: {dep.migration_guide}')

                if dep.removal_version:

                    print(f'  Removal version: {dep.removal_version}')

                return 0

            if sub=='lifecycle':

                from .extension_lifecycle import ExtensionLifecycleManager

                name=argv[2] if len(argv)>2 else None

                if not name:

                    print('Usage: pea ext lifecycle <name>');return 1

                lm=ExtensionLifecycleManager()

                deps=[d for d in lm.list_deprecated() if d.name==name]

                print(f'Extension: {name}')

                versions=lm.versions.get(name,[])

                if versions:

                    print(f'  Versions: {", ".join(v.version for v in versions)}')

                if deps:

                    print('  Deprecated versions:')

                    for d in deps:

                        print(f'    {d.deprecated_version} - {d.message or "(no message)"}')

                        if d.replacement:

                            print(f'      Replacement: {d.replacement}')

                        if d.migration_guide:

                            print(f'      Migration guide: {d.migration_guide}')

                        if d.removal_version:

                            print(f'      Removal version: {d.removal_version}')

                else:

                    print('  No deprecated versions')

                return 0

            if sub=='migrate':

                from .extension_lifecycle import ExtensionLifecycleManager

                name=argv[2] if len(argv)>2 else None

                from_version=argv[3] if len(argv)>3 else None

                to_version=argv[4] if len(argv)>4 else None

                if not name or not from_version or not to_version:

                    print('Usage: pea ext migrate <name> <from_version> <to_version>');return 1

                lm=ExtensionLifecycleManager()

                result=lm.check_compatibility(name, from_version, to_version)

                print(f'Compatibility: {name} {from_version} -> {to_version}')

                print(f'  Compatible: {result["compatible"]}')

                if result.get('from_deprecated'):

                    print(f'  Warning: {from_version} is deprecated')

                if result.get('to_deprecated'):

                    print(f'  Warning: {to_version} is deprecated')

                if result.get('major_changed'):

                    print(f'  Warning: Major version change detected')

                if result.get('migration_guide'):

                    print(f'  Migration guide: {result["migration_guide"]}')

                if result.get('replacement'):

                    print(f'  Replacement: {result["replacement"]}')

                return 0

            print('Usage: pea ext list|load <module>|info <name>|deprecate <name> <version>|lifecycle <name>|migrate <name> <from> <to>');return 1

        if c=='lib':

            from .package_manager import build_library, quality_check
            import urllib.request, urllib.error, json as _json

            sub=argv[1] if len(argv)>1 else None

            if sub=='new':
                p=argparse.ArgumentParser(prog='pea lib new')
                p.add_argument('name')
                p.add_argument('--template',default='library')
                a=p.parse_args(argv[2:])
                out=init_project(a.name,a.name,a.template,{})
                print(out);return 0

            if sub=='build':
                p=argparse.ArgumentParser(prog='pea lib build')
                p.add_argument('path',nargs='?',default='.')
                p.add_argument('-o','--output')
                a=p.parse_args(argv[2:])
                out,h=build_library(a.path,a.output)
                print(f'{out}\nsha256 {h}');return 0

            if sub=='quality':
                path=argv[2] if len(argv)>2 else '.'
                result=quality_check(path)
                print(json.dumps(result,indent=2));return 0 if result['ok'] else 1

            if sub=='publish':
                path=None
                registry='http://127.0.0.1:8788'
                token=None
                dry_run=False
                i=2
                while i<len(argv):
                    arg=argv[i]
                    if arg=='--registry' and i+1<len(argv):registry=argv[i+1];i+=2;continue
                    if arg=='--token' and i+1<len(argv):token=argv[i+1];i+=2;continue
                    if arg=='--dry-run':dry_run=True;i+=1;continue
                    if path is None:path=arg
                    i+=1
                if not path:
                    print('Usage: pea lib publish <path> [--registry URL] [--token TOKEN] [--dry-run]');return 1
                root=Path(path).resolve()
                mf,data=load_pea_toml(root)
                name=data['project']['name'];version=data['project']['version']
                out,h=build_library(root)
                if dry_run:
                    print(f'Dry-run: built library at {out} sha256={h}')
                    return 0
                package_bytes=Path(out).read_bytes()
                if not token:
                    token_file=Path.home()/'.pealang'/'registry_tokens.json'
                    if token_file.exists():
                        try:
                            tokens=_json.loads(token_file.read_text())
                            token=tokens.get(registry)
                        except Exception:
                            token=None
                if not token:
                    print('Error: No registry token. Use --token or pea login first.');return 1
                url=f'{registry}/api/v1/packages/{name}/{version}'
                req=urllib.request.Request(url,data=package_bytes,method='PUT')
                req.add_header('Authorization','Bearer '+token)
                req.add_header('Content-Type','application/octet-stream')
                try:
                    with urllib.request.urlopen(req) as resp:
                        if resp.status==201:
                            result=_json.loads(resp.read().decode())
                            print(f'Published {result["name"]} {result["version"]} (sha256={result["sha256"]})')
                        else:
                            print(f'Upload failed: HTTP {resp.status}');return 1
                except urllib.error.HTTPError as e:
                    body=e.read().decode() if e.fp else ''
                    print(f'Upload failed: HTTP {e.code} {body}');return 1
                except Exception as e:
                    print(f'Upload failed: {e}');return 1
                return 0

            print('Usage: pea lib new <name> | pea lib build <path> [-o output] | pea lib quality <path> | pea lib publish <path> [--registry URL] [--token TOKEN]');return 1

        if c=='publish':

            from .package_manager import build_library
            import urllib.request, urllib.error, json as _json

            path=None
            registry='http://127.0.0.1:8788'
            token=None
            dry_run=False

            i=1
            while i<len(argv):
                arg=argv[i]
                if arg=='--registry' and i+1<len(argv):registry=argv[i+1];i+=2;continue
                if arg=='--token' and i+1<len(argv):token=argv[i+1];i+=2;continue
                if arg=='--dry-run':dry_run=True;i+=1;continue
                if path is None:path=arg
                i+=1

            if not path:
                print('Usage: pea publish <path> [--registry URL] [--token TOKEN] [--dry-run]');return 1

            root=Path(path).resolve()
            mf,data=load_pea_toml(root)
            name=data['project']['name'];version=data['project']['version']

            # Build the library package
            out,h=build_library(root)
            package_bytes=Path(out).read_bytes()
            if dry_run:
                print(f'Dry-run: built library at {out} sha256={h}')
                return 0

            # Get token from stored tokens if not provided
            if not token:
                token_file=Path.home()/'.pealang'/'registry_tokens.json'
                if token_file.exists():
                    try:
                        tokens=_json.loads(token_file.read_text())
                        token=tokens.get(registry)
                    except Exception:
                        token=None

            if not token:
                print('Error: No registry token. Use --token or pea login first.');return 1

            # Upload to registry
            url=f'{registry}/api/v1/packages/{name}/{version}'
            req=urllib.request.Request(url,data=package_bytes,method='PUT')
            req.add_header('Authorization','Bearer '+token)
            req.add_header('Content-Type','application/octet-stream')

            try:
                with urllib.request.urlopen(req) as resp:
                    if resp.status==201:
                        result=_json.loads(resp.read().decode())
                        print(f'Published {result["name"]} {result["version"]} (sha256={result["sha256"]})')
                    else:
                        print(f'Upload failed: HTTP {resp.status}');return 1
            except urllib.error.HTTPError as e:
                body=e.read().decode() if e.fp else ''
                print(f'Upload failed: HTTP {e.code} {body}');return 1
            except Exception as e:
                print(f'Upload failed: {e}');return 1

            return 0

        if c=='search':

            import urllib.request, json as _json

            query=argv[1] if len(argv)>1 else None
            registry='http://127.0.0.1:8788'

            i=2
            while i+1<len(argv):
                if argv[i]=='--registry':registry=argv[i+1];i+=2;continue
                i+=1

            if not query:
                print('Usage: pea search <query> [--registry URL]');return 1

            url=f'{registry}/api/v1/packages'
            try:
                with urllib.request.urlopen(url) as resp:
                    data=_json.loads(resp.read().decode())
                    pkgs=data.get('packages',{})
                    matches={k:v for k,v in pkgs.items() if query.lower() in k.lower()}
                    if not matches:
                        print(f'No packages matching "{query}"')
                    else:
                        for name,versions in sorted(matches.items()):
                            for v in versions:
                                print(f'{name} {v["version"]} (sha256={v["sha256"][:12]}...)')
            except Exception as e:
                print(f'Search failed: {e}');return 1

            return 0

        if c=='browse':

            import urllib.request, json as _json

            registry='http://127.0.0.1:8788'

            i=1
            while i+1<len(argv):
                if argv[i]=='--registry':registry=argv[i+1];i+=2;continue
                i+=1

            url=f'{registry}/api/v1/packages'
            try:
                with urllib.request.urlopen(url) as resp:
                    data=_json.loads(resp.read().decode())
                    pkgs=data.get('packages',{})
                    if not pkgs:
                        print('No packages available')
                    else:
                        for name,versions in sorted(pkgs.items()):
                            latest=versions[0] if versions else {}
                            print(f'{name} {latest.get("version","?")} (sha256={latest.get("sha256","?")[:12]}...)')
            except Exception as e:
                print(f'Browse failed: {e}');return 1

            return 0

        if c=='login':

            import json as _json

            token=argv[1] if len(argv)>1 else None
            registry='http://127.0.0.1:8788'

            i=2
            while i+1<len(argv):
                if argv[i]=='--registry':registry=argv[i+1];i+=2;continue
                i+=1

            if not token:
                print('Usage: pea login <token> [--registry URL]');return 1

            token_dir=Path.home()/'.pealang'
            token_dir.mkdir(parents=True,exist_ok=True)
            token_file=token_dir/'registry_tokens.json'

            tokens={}
            if token_file.exists():
                try:
                    tokens=_json.loads(token_file.read_text())
                except Exception:
                    tokens={}

            tokens[registry]=token
            token_file.write_text(_json.dumps(tokens,indent=2))
            print(f'Logged in to {registry}')

            return 0

        if c=='logout':

            import json as _json

            registry='http://127.0.0.1:8788'

            i=1
            while i+1<len(argv):
                if argv[i]=='--registry':registry=argv[i+1];i+=2;continue
                i+=1

            token_file=Path.home()/'.pealang'/'registry_tokens.json'

            if token_file.exists():
                try:
                    tokens=_json.loads(token_file.read_text())
                except Exception:
                    tokens={}
                if registry in tokens:
                    del tokens[registry]
                    token_file.write_text(_json.dumps(tokens,indent=2))
                    print(f'Logged out from {registry}')
                else:
                    print(f'Not logged in to {registry}')
            else:
                print(f'Not logged in to {registry}')

            return 0

        if c=='portal':

            from .dev_portal import serve

            host='127.0.0.1';port=8789;storage='./portal-storage'

            i=1

            while i+1<len(argv):

                if argv[i]=='--host':host=argv[i+1];i+=2;continue

                if argv[i]=='--port':port=int(argv[i+1]);i+=2;continue

                if argv[i]=='--storage':storage=argv[i+1];i+=2;continue

                i+=1

            serve(host=host,port=port,storage_dir=storage)

            serve(host=host,port=port,storage_dir=storage)

            return 0

        if c=='market':

            from .marketplace import create_marketplace
            import json as _json

            sub=argv[1] if len(argv)>1 else None

            if sub=='list':

                tag=argv[2] if len(argv)>2 else None
                author=argv[3] if len(argv)>3 else None
                sort=argv[4] if len(argv)>4 else 'downloads'

                mp=create_marketplace()
                libs=mp.list_libraries(tag=tag, author=author, sort_by=sort)

                for lib in libs:
                    print(f'{lib.name} {lib.version} - {lib.description[:60]}')
                    print(f'  Author: {lib.author} | Downloads: {lib.downloads} | Rating: {lib.rating:.1f} ({lib.rating_count})')
                    print(f'  Tags: {", ".join(lib.tags)}')
                    print()

                return 0

            if sub=='search':

                query=argv[2] if len(argv)>2 else None

                if not query:

                    print('Usage: pea market search <query>');return 1

                mp=create_marketplace()
                results=mp.search_libraries(query)

                if not results:
                    print(f'No libraries matching "{query}"')
                else:
                    for lib in results:
                        print(f'{lib.name} {lib.version} - {lib.description[:60]}')
                        print(f'  Author: {lib.author} | Downloads: {lib.downloads} | Rating: {lib.rating:.1f}')

                return 0

            if sub=='rate':

                name=argv[2] if len(argv)>2 else None
                version=argv[3] if len(argv)>3 else None
                rating=argv[4] if len(argv)>4 else None
                reviewer=argv[5] if len(argv)>5 else 'anonymous'
                comment=argv[6] if len(argv)>6 else ''

                if not name or not version or not rating:

                    print('Usage: pea market rate <name> <version> <rating> [reviewer] [comment]');return 1

                try:

                    rating_int=int(rating)

                except ValueError:

                    print(f'Invalid rating: {rating}');return 1

                mp=create_marketplace()

                try:

                    r=mp.rate_library(name, version, rating_int, reviewer, comment)

                    print(f'Rated {name} {version}: {r.rating}/5 by {r.reviewer}')

                except ValueError as e:

                    print(f'Error: {e}');return 1

                return 0

            if sub=='info':

                name=argv[2] if len(argv)>2 else None

                if not name:

                    print('Usage: pea market info <name>');return 1

                mp=create_marketplace()

                lib=mp.get_library(name)

                if not lib:

                    print(f'Library {name} not found');return 1

                print(f'{lib.name} {lib.version}')
                print(f'  Author: {lib.author}')
                print(f'  Description: {lib.description}')
                print(f'  Downloads: {lib.downloads}')
                print(f'  Rating: {lib.rating:.1f} ({lib.rating_count} ratings)')
                print(f'  Tags: {", ".join(lib.tags)}')
                if lib.license: print(f'  License: {lib.license}')
                if lib.homepage: print(f'  Homepage: {lib.homepage}')
                if lib.repository: print(f'  Repository: {lib.repository}')

                return 0

            if sub=='register':

                name=argv[2] if len(argv)>2 else None
                version=argv[3] if len(argv)>3 else None
                description=argv[4] if len(argv)>4 else None
                author=argv[5] if len(argv)>5 else None
                tags=argv[6].split(',') if len(argv)>6 else []

                if not name or not version or not description or not author:
                    print('Usage: pea market register <name> <version> <description> <author> [tags]');return 1

                mp=create_marketplace()
                lib=mp.register_library(name, version, description, author, tags)
                print(f'Registered {lib.name} {lib.version}')
                return 0

            if sub=='download':
                name=argv[2] if len(argv)>2 else None
                if not name:
                    print('Usage: pea market download <name>');return 1
                mp=create_marketplace()
                mp.download_library(name)
                print(f'Recorded download for {name}')
                return 0

            print('Usage: pea market list|search|rate|info|register|download');return 1

        if len(argv)==1 and argv[0].endswith('.peac'):

            from .bytecode import BytecodeModule

            from .vm import VirtualMachine

            VirtualMachine(print).run(BytecodeModule.load(argv[0]));return 0

        allow='--allow-process' in argv

        if allow:argv.remove('--allow-process')

        if len(argv)!=1:print('Usage: pea [run|eval|repl|check|lint|fmt|test|compile|vm|dis|init|new|serve-web|doctor|health|help|quickstart|scaffold|templates|info|project|docs|registry|publish|search|browse|login|logout|ext|portal|market|analyze|web-openapi|hash|tree|env|typecheck|typecheck-project|readiness|audit|stdlib] ...',file=sys.stderr);return 2

        return run_file(argv[0],allow)

    except (PeaError,OSError) as e:_print_error(e);return 1

if __name__=='__main__':raise SystemExit(main())

