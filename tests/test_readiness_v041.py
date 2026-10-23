from pealang import default_report,ReadinessReport,compare_benchmark
def test_candidate_pilots_present():assert len(default_report().pilots)==2
def test_three_host_targets():assert len(default_report().stable_hosts)==3
def test_default_gate_not_falsely_passed():
 r=default_report();assert not r.ok() and not r.gates()['two_validated_pilots']
def test_security_pack_prepared_not_completed():
 r=default_report();assert r.security_review['prepared'] and not r.security_review['external_review_completed']
def test_migration_report_prepared():assert default_report().migration['prepared']
def test_performance_gate_pass():assert compare_benchmark({'median_ms':10},{'median_ms':10.5},10)['ok']
def test_performance_gate_fail():assert not compare_benchmark({'median_ms':10},{'median_ms':12},10)['ok']
def test_gate_can_pass_with_evidence():
 r=default_report();r.pilots[0]['status']='validated';r.pilots[1]['status']='validated';assert r.ok()

