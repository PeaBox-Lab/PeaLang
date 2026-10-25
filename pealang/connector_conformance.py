"""PeaLang 0.85 data and connector conformance framework."""
from __future__ import annotations
from dataclasses import asdict,dataclass,field
from enum import Enum
import hashlib,json
from typing import Any,Callable,Iterable,Mapping

class Capability(str,Enum):
 SQL='sql';PARAMETERS='parameters';TRANSACTIONS='transactions';STREAMING='streaming';CHECKPOINTS='checkpoints';REPLAY='replay';OBJECT_STORAGE='object_storage';PAGINATION='pagination';RANGE_READ='range_read';MULTIPART='multipart'
@dataclass(frozen=True)
class ConnectorProfile:
 name:str;version:str;capabilities:frozenset[Capability];metadata:Mapping[str,Any]=field(default_factory=dict)
 def supports(self,*items):return all(x in self.capabilities for x in items)
@dataclass(frozen=True)
class ConformanceCase:
 case_id:str;capability:Capability;runner:Callable[[Any],Any];required:bool=True;description:str=''
@dataclass(frozen=True)
class CaseResult:
 case_id:str;capability:str;status:str;detail:str=''
@dataclass(frozen=True)
class CertificationReport:
 connector:str;version:str;results:tuple[CaseResult,...]
 @property
 def passed(self):return all(x.status in ('PASS','SKIP') for x in self.results)
 def to_dict(self):return {'schema':1,'connector':self.connector,'version':self.version,'passed':self.passed,'results':[asdict(x) for x in self.results]}
class ConformanceSuite:
 def __init__(self,cases=()):self.cases=list(cases)
 def add(self,case):
  if any(x.case_id==case.case_id for x in self.cases):raise ValueError(f'duplicate case: {case.case_id}')
  self.cases.append(case);return self
 def run(self,profile,connector):
  output=[]
  for case in sorted(self.cases,key=lambda x:x.case_id):
   if case.capability not in profile.capabilities:
    output.append(CaseResult(case.case_id,case.capability.value,'FAIL' if case.required else 'SKIP','capability not declared'));continue
   try:
    value=case.runner(connector)
    if value is False:raise AssertionError('case returned false')
    output.append(CaseResult(case.case_id,case.capability.value,'PASS'))
   except Exception as exc:output.append(CaseResult(case.case_id,case.capability.value,'FAIL',f'{exc.__class__.__name__}: {exc}'))
  return CertificationReport(profile.name,profile.version,tuple(output))
class SQLDialect(str,Enum):SQLITE='sqlite';POSTGRESQL='postgresql';MYSQL='mysql';MSSQL='mssql';ORACLE='oracle'
@dataclass(frozen=True)
class SQLDialectContract:
 dialect:SQLDialect;placeholder:str;quote_open:str;quote_close:str;supports_returning:bool;supports_savepoints:bool
SQL_DIALECTS={
 SQLDialect.SQLITE:SQLDialectContract(SQLDialect.SQLITE,'?','"','"',True,True),
 SQLDialect.POSTGRESQL:SQLDialectContract(SQLDialect.POSTGRESQL,'%s','"','"',True,True),
 SQLDialect.MYSQL:SQLDialectContract(SQLDialect.MYSQL,'%s','`','`',False,True),
 SQLDialect.MSSQL:SQLDialectContract(SQLDialect.MSSQL,'?','[',']',True,True),
 SQLDialect.ORACLE:SQLDialectContract(SQLDialect.ORACLE,':1','"','"',True,True)}
def validate_parameter_binding(sql,parameters,dialect):
 c=SQL_DIALECTS[SQLDialect(dialect)];count=sql.count(c.placeholder) if c.placeholder not in (':1',) else sum(sql.count(f':{i}') for i in range(1,len(parameters)+1))
 return {'valid':count==len(parameters),'expected':count,'actual':len(parameters),'dialect':c.dialect.value}
class TransactionProbe:
 def run(self,connector):
  connector.begin()
  try:
   connector.execute('INSERT conformance',{'value':'commit'});connector.commit()
   connector.begin();connector.execute('INSERT conformance',{'value':'rollback'});connector.rollback()
  except Exception:
   connector.rollback();raise
  rows=connector.query('SELECT conformance')
  return {'commit_visible':any(x.get('value')=='commit' for x in rows),'rollback_hidden':not any(x.get('value')=='rollback' for x in rows)}
@dataclass(frozen=True)
class StreamEvent:offset:int;key:str;payload:Any
class StreamRecoveryModel:
 def __init__(self):self._events=[];self._checkpoint=-1
 def append(self,key,payload):
  event=StreamEvent(len(self._events),key,payload);self._events.append(event);return event
 def checkpoint(self,offset):
  if offset<self._checkpoint:raise ValueError('checkpoint cannot move backwards')
  self._checkpoint=offset
 def replay(self):return tuple(x for x in self._events if x.offset>self._checkpoint)
 def deduplicate(self,events):
  seen=set();out=[]
  for e in events:
   identity=(e.offset,e.key)
   if identity not in seen:seen.add(identity);out.append(e)
  return tuple(out)
class ObjectStoreEdgeCases:
 @staticmethod
 def collect_pages(fetch,token=None,max_pages=1000):
  items=[];seen=set()
  for _ in range(max_pages):
   page,next_token=fetch(token);items.extend(page)
   if next_token is None:return items
   if next_token in seen:raise RuntimeError('pagination token cycle')
   seen.add(next_token);token=next_token
  raise RuntimeError('pagination limit exceeded')
 @staticmethod
 def validate_range(data,start,end,read):
  if start<0 or end<start or end>len(data):raise ValueError('invalid range')
  return read(start,end)==data[start:end]
 @staticmethod
 def multipart_upload(parts,upload,abort):
  completed=[]
  try:
   for number,payload in enumerate(parts,1):completed.append(upload(number,payload))
   return {'status':'completed','parts':completed}
  except Exception:
   abort(tuple(completed));return {'status':'aborted','parts':completed}
def certification_gate(report,required_pass_rate=1.0):
 required=[x for x in report.results if x.status!='SKIP'];passed=sum(x.status=='PASS' for x in required);rate=passed/max(1,len(required));return {'gate':'PASS' if rate>=required_pass_rate and report.passed else 'FAIL','pass_rate':rate,'failed':[x.case_id for x in required if x.status!='PASS'],'report_digest':hashlib.sha256(json.dumps(report.to_dict(),sort_keys=True,separators=(',',':')).encode()).hexdigest()}
