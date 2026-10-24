"""Portable PeaLang bytecode model and .peac serialization."""
from __future__ import annotations
from dataclasses import dataclass,field,asdict
from enum import Enum
import json
class Op(str,Enum):
 CONST='CONST';NULL='NULL';TRUE='TRUE';FALSE='FALSE';LOAD='LOAD';STORE='STORE';POP='POP';PRINT='PRINT'
 ADD='ADD';SUB='SUB';MUL='MUL';DIV='DIV';MOD='MOD';NEG='NEG';NOT='NOT';EQ='EQ';NE='NE';LT='LT';LE='LE';GT='GT';GE='GE'
 LIST='LIST';DICT='DICT';GET_INDEX='GET_INDEX';GET_PROPERTY='GET_PROPERTY';SET_INDEX='SET_INDEX';SET_PROPERTY='SET_PROPERTY';CALL='CALL';AWAIT='AWAIT';RETURN='RETURN'
 JUMP='JUMP';JUMP_IF_FALSE='JUMP_IF_FALSE';RAISE='RAISE';PUSH_HANDLER='PUSH_HANDLER';POP_HANDLER='POP_HANDLER';IMPORT='IMPORT';ITER='ITER';ITER_NEXT='ITER_NEXT';FUNCTION='FUNCTION';EXPORT='EXPORT';HALT='HALT'
@dataclass
class Instruction:
 op:str;arg:object=None;line:int=1
@dataclass
class CodeObject:
 name:str='<module>';params:list[str]=field(default_factory=list);instructions:list[Instruction]=field(default_factory=list);source_name:str='<input>';defaults:dict=field(default_factory=dict)
@dataclass
class BytecodeModule:
 version:str='1';constants:list[object]=field(default_factory=list);code:CodeObject=field(default_factory=CodeObject);functions:dict[str,CodeObject]=field(default_factory=dict);source_name:str='<input>'
 def to_dict(self):
  def code(c):return {'name':c.name,'params':c.params,'source_name':c.source_name,'defaults':c.defaults,'instructions':[asdict(i) for i in c.instructions]}
  return {'format':'PEAC','version':self.version,'constants':self.constants,'source_name':self.source_name,'code':code(self.code),'functions':{k:code(v) for k,v in self.functions.items()}}
 @classmethod
 def from_dict(cls,d):
  if d.get('format')!='PEAC':raise ValueError('Not a PeaLang bytecode artifact')
  def code(x):return CodeObject(x['name'],x.get('params',[]),[Instruction(**i) for i in x['instructions']],x.get('source_name','<input>'),x.get('defaults',{}))
  return cls(d['version'],d.get('constants',[]),code(d['code']),{k:code(v) for k,v in d.get('functions',{}).items()},d.get('source_name','<input>'))
 def dumps(self):return json.dumps(self.to_dict(),indent=2,ensure_ascii=False)
 @classmethod
 def loads(cls,text):return cls.from_dict(json.loads(text))
 def save(self,path):open(path,'w',encoding='utf-8').write(self.dumps())
 @classmethod
 def load(cls,path):return cls.loads(open(path,encoding='utf-8').read())

