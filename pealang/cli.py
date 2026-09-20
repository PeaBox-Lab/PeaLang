import argparse, sys
from pathlib import Path
from .runtime import execute, Interpreter, PeaError

def repl():
    print('PeaLang 0.1.0 - type exit to quit')
    vm=Interpreter(); buf=''
    while True:
        try: line=input('... ' if buf else 'pea> ')
        except (EOFError,KeyboardInterrupt): print(); break
        if line.strip() in ('exit','quit') and not buf: break
        buf += line+'\n'
        if buf.count('{')>buf.count('}'): continue
        try: execute(buf,interpreter=vm)
        except PeaError as e: print(f'Error: {e}',file=sys.stderr)
        except Exception as e: print(f'Runtime error: {e}',file=sys.stderr)
        buf=''

def main():
    p=argparse.ArgumentParser(prog='pealang',description='PeaLang interpreter')
    p.add_argument('file',nargs='?'); p.add_argument('--version',action='version',version='PeaLang 0.1.0')
    a=p.parse_args()
    if not a.file:return repl()
    try: execute(Path(a.file).read_text(encoding='utf-8'))
    except (PeaError,OSError) as e: print(f'Error: {e}',file=sys.stderr); return 1
    return 0
if __name__=='__main__': raise SystemExit(main())
