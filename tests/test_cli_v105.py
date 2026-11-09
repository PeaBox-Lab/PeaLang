import subprocess, sys, tempfile, os

def test_cli_eval_file():
    with tempfile.NamedTemporaryFile('w', suffix='.pea', delete=False, encoding='utf-8') as f:
        f.write('print 6*7\n')
        name = f.name
    try:
        r = subprocess.run([sys.executable, '-m', 'pealang.cli', 'eval', '-f', name], capture_output=True, text=True, cwd=r"C:\Users\Rajesh\Documents\My Apps\GitHub\PeaLang")
        assert r.returncode == 0
        assert r.stdout.strip() == '42'
    finally:
        os.unlink(name)
