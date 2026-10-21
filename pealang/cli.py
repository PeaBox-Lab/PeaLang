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
        allow='--allow-process' in argv
        if allow:argv.remove('--allow-process')
        if len(argv)!=1:print('Usage: pea [init|project|add|remove|start|run|fmt|check|test|docs|repl] ...',file=sys.stderr);return 2
        return run_file(argv[0],allow)
    except (PeaError,OSError) as e:print(f'Error: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
