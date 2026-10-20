"""Backward-compatible public runtime facade."""
from .errors import PeaError, SourceSpan
from .lexer import Lexer, Token
from .parser import Parser, parse_source
from .interpreter import Interpreter

def compile_source(source, source_name='<input>'):
    return parse_source(source, source_name)

def execute(source, output=None, interpreter=None, source_name='<input>', base_dir=None, allow_process=False):
    vm=interpreter or Interpreter(output=output,base_dir=base_dir,allow_process=allow_process)
    return vm.run(compile_source(source,source_name),source_name)
