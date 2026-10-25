
import pytest
from pealang.integration_hardening import *

def test_credentials_chain(monkeypatch):
    monkeypatch.setenv('PEALANG_TOKEN','env');chain=ChainedCredentialProvider(MappingCredentialProvider({'other':'x'}),EnvironmentCredentialProvider())
    assert chain.get('token')=='env' and chain.get('other')=='x' and chain.get('missing') is None

def test_retry_then_success_with_correlation():
    calls=[]
    def op():
        calls.append(1)
        if len(calls)<3:raise IntegrationTimeoutError('temporary')
        return 42
    profile=IntegrationProfile(retry=RetryPolicy(max_attempts=3,initial_delay=0,jitter=0))
    result=ReliableExecutor(profile,sleep=lambda _:None).execute(op,correlation_id='cid')
    assert result.value==42 and result.attempts==3 and result.correlation_id=='cid'

def test_circuit_breaker_opens_and_recovers():
    now=[0.0];breaker=CircuitBreaker(2,10,clock=lambda:now[0]);profile=IntegrationProfile(retry=RetryPolicy(max_attempts=1,initial_delay=0))
    executor=ReliableExecutor(profile,breaker,sleep=lambda _:None,clock=lambda:now[0])
    for _ in range(2):
        with pytest.raises(IntegrationUnavailableError):executor.execute(lambda:(_ for _ in ()).throw(IntegrationUnavailableError('down')))
    with pytest.raises(CircuitOpenError):executor.execute(lambda:1)
    now[0]=11;assert executor.execute(lambda:1).value==1 and breaker.state==CircuitState.CLOSED

def test_health_report():
    assert ConnectorHealthCheck('ok',lambda:True).run().healthy
    report=ConnectorHealthCheck('bad',lambda:(_ for _ in ()).throw(ValueError('bad'))).run();assert not report.healthy and 'ValueError' in report.detail

