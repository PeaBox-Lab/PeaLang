



from pealang.connector_conformance import *
def test_sql_dialects_and_binding():
 assert validate_parameter_binding('select * from t where a=? and b=?',[1,2],SQLDialect.SQLITE)['valid']
 assert not validate_parameter_binding('select * from t where a=?',[1,2],SQLDialect.SQLITE)['valid']
def test_transaction_probe():
 class DB:
  def __init__(self):self.rows=[];self.pending=[]
  def begin(self):self.pending=[]
  def execute(self,q,p):self.pending.append(p)
  def commit(self):self.rows+=self.pending;self.pending=[]
  def rollback(self):self.pending=[]
  def query(self,q):return self.rows
 assert TransactionProbe().run(DB())=={'commit_visible':True,'rollback_hidden':True}
def test_stream_checkpoint_replay_and_dedupe():
 m=StreamRecoveryModel();a=m.append('a',1);b=m.append('b',2);m.checkpoint(0);assert m.replay()==(b,) and m.deduplicate([a,a,b])==(a,b)
def test_object_store_edges():
 pages={None:([1,2],'next'),'next':([3],None)};assert ObjectStoreEdgeCases.collect_pages(lambda token:pages[token])==[1,2,3]
 data=b'abcdef';assert ObjectStoreEdgeCases.validate_range(data,1,4,lambda a,b:data[a:b])
 aborted=[];r=ObjectStoreEdgeCases.multipart_upload([b'a',b'b'],lambda n,p:(_ for _ in ()).throw(ValueError()) if n==2 else n,lambda done:aborted.append(done));assert r['status']=='aborted' and aborted==[(1,)]
def test_suite_and_certification_gate():
 p=ConnectorProfile('demo','1',frozenset({Capability.SQL}));s=ConformanceSuite().add(ConformanceCase('sql.basic',Capability.SQL,lambda c:True));report=s.run(p,object());assert report.passed and certification_gate(report)['gate']=='PASS'
 failed=ConformanceSuite().add(ConformanceCase('stream.basic',Capability.STREAMING,lambda c:True)).run(p,object());assert certification_gate(failed)['gate']=='FAIL'




