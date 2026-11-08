import json, subprocess, sys


def test_cli_eval_and_info():
    r = subprocess.run([sys.executable, "-m", "pealang.cli", "eval", "-e", "print 2+2"], capture_output=True, text=True, cwd=r"C:\Users\Rajesh\Documents\My Apps\GitHub\PeaLang")
    assert r.returncode == 0
    assert r.stdout.strip() == "4"
    r = subprocess.run([sys.executable, "-m", "pealang.cli", "info"], capture_output=True, text=True, cwd=r"C:\Users\Rajesh\Documents\My Apps\GitHub\PeaLang")
    assert r.returncode == 0
    info = json.loads(r.stdout)
    assert "version" in info and "commands" in info
