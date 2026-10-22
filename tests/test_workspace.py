
from pealang.workspace import WorkspaceIndex

def test_cross_file_index(tmp_path):
 (tmp_path/'a.pea').write_text('function double(x) { return x * 2 }\nexport double\n')
 (tmp_path/'b.pea').write_text('let value = 3\n')
 i=WorkspaceIndex(tmp_path).build();assert i.definition('double',True)['exported'];assert i.definition('value')['kind']=='variable'

def test_index_errors(tmp_path):
 (tmp_path/'bad.pea').write_text('let =');i=WorkspaceIndex(tmp_path).build();assert len(i.errors)==1
