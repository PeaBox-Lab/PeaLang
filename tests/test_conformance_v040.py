from pealang.conformance import generated_cases,differential,run_conformance,fuzz_lexer_parser
def test_500_case_corpus_generated():assert len(generated_cases(500))==500
def test_differential_simple():assert differential('print 2+3')==(['5'],['5'])
def test_generated_gate():
 r=run_conformance(500);assert r['passed']==500 and r['failed']==0
def test_fuzz_deterministic():
 r=fuzz_lexer_parser(100,1337);assert r['iterations']==100 and r['ok']
def test_ids_unique():
 c=generated_cases();assert len({x.id for x in c})==500
