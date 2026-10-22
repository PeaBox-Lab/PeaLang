from pealang.help_system import render_help
from pealang import __version__

def test_version(): assert __version__ == '0.17.0'
def test_general_help(): assert 'PeaLang Help' in render_help()
def test_topic_help(): assert 'REPL commands' in render_help('repl')
def test_alias_help(): assert render_help('function') == render_help('functions')
def test_unknown_help(): assert 'Unknown help topic' in render_help('missing')

def test_cli_help(capsys):
    from pealang.cli import main
    assert main(['help','repl']) == 0
    assert 'REPL commands' in capsys.readouterr().out
