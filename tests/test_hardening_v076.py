
from pealang.agent_governance import AgentPolicy
from pealang.hardening import SecurityProbe,AdversarialAgentSuite,PublicAPIGate,ReleaseHardeningGate,ReleaseThresholds

def test_adversarial_policy_suite():
    suite=AdversarialAgentSuite(AgentPolicy(denied=['delete'],approval_required=['deploy'],max_calls=2))
    results=suite.run([SecurityProbe('safe','read',expect_allowed=True),SecurityProbe('deny','delete'),SecurityProbe('approval','deploy'),SecurityProbe('budget','read',call_index=2)])
    summary=suite.summary(results);assert summary['gate']=='PASS' and summary['passed']==4

def test_public_api_gate_catches_unexpected_removal():
    gate=PublicAPIGate();assert gate.compare(['a','b'],['a','b','c'])['gate']=='PASS';assert gate.compare(['a','b'],['a'])['gate']=='FAIL';assert gate.compare(['a','b'],['a'],['b'])['gate']=='PASS'

def test_release_hardening_gate():
    report=ReleaseHardeningGate().evaluate(500,{'total':4,'passed':4},{'unexpected_removals':[]},{'unexpected_missing':[]},ReleaseThresholds(minimum_tests=455))
    assert report['gate']=='PASS' and all(report['checks'].values())

