import argparse,sys
from pathlib import Path
from .runtime import execute,Interpreter,PeaError
from . import __version__
def repl():
    print(f'PeaLang {__version__} - type exit to quit');vm=Interpreter();buf=''
    while True:
        try:line=input('... ' if buf else 'pea> ')
        except (EOFError,KeyboardInterrupt):print();break
        if line.strip() in ('exit','quit') and not buf:break
        buf+=line+'\n'
        if buf.count('{')>buf.count('}'):continue
        try:execute(buf,interpreter=vm,source_name='<repl>')
        except PeaError as e:print(f'Error: {e}',file=sys.stderr)
        buf=''
def main(argv=None):
    p=argparse.ArgumentParser(prog='pea',description='PeaLang interpreter');p.add_argument('file',nargs='?');p.add_argument('--version',action='version',version=f'PeaLang {__version__}')
    a=p.parse_args(argv)
    if not a.file:return repl()
    path=Path(a.file)
    try:execute(path.read_text(encoding='utf-8'),source_name=str(path),base_dir=path.parent)
    except (PeaError,OSError) as e:print(f'Error: {e}',file=sys.stderr);return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
