


from pealang import split_tests,run_source_tests,coverage_summary,migrate_text,migrate_path
def test_split_expect():
 setup,tests=split_tests('let x=2\ntest "ok" {\n expect x == 2\n}')
 assert 'let x=2' in setup and 'assert x == 2' in tests[0][1]
def test_native_pass():assert run_source_tests('test "math" { expect 2 + 2 == 4 }')[0].passed
def test_native_fail():assert not run_source_tests('test "math" { expect 2 + 2 == 5 }')[0].passed
def test_filter():assert len(run_source_tests('test "one" { expect true }\ntest "two" { expect true }',filter_text='two'))==1
def test_coverage_summary(tmp_path):
 p=tmp_path/'a.pea';p.write_text('test "x" { expect true }');r=run_source_tests(p.read_text(),str(p));c=coverage_summary([p],r);assert c['tests']==1 and c['passed']==1
def test_migrate_advisory():
 out,notes=migrate_text('print 1','0.34','0.38');assert out=='print 1' and notes
def test_migrate_path_preserves_source(tmp_path):
 p=tmp_path/'x.pea';p.write_text('print 1');x=migrate_path(p,'0.37','0.38');assert p.read_text()=='print 1' and len(x)==1



