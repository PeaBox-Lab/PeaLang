
# AUDIT-CLOSURE: intentional interface contract; concrete backends must override the methods documented in docs/project/INTERFACE_COMPLETENESS_0991.md.



"""PeaLang v0.79 enterprise integration and connector reliability controls."""
from __future__ import annotations
from dataclasses import dataclass,field,asdict
from enum import Enum
from pathlib import Path
from typing import Any,Callable
import os,random,time,uuid

class IntegrationError(RuntimeError): pass
class IntegrationAuthenticationError(IntegrationError): pass
class IntegrationTimeoutError(IntegrationError): pass
class IntegrationRateLimitError(IntegrationError): pass
class IntegrationUnavailableError(IntegrationError): pass
class CircuitOpenError(IntegrationUnavailableError): pass

class CredentialProvider:
    def get(self,name:str)->str|None: raise NotImplementedError

class EnvironmentCredentialProvider(CredentialProvider):
    def __init__(self,prefix="PEALANG_"): self.prefix=prefix
    def get(self,name): return os.getenv(self.prefix+str(name).upper().replace('-','_'))

class MappingCredentialProvider(CredentialProvider):
    def __init__(self,values=None): self.values=dict(values or {})
    def get(self,name): return self.values.get(name)

class ChainedCredentialProvider(CredentialProvider):
    def __init__(self,*providers): self.providers=providers
    def get(self,name):
        for provider in self.providers:
            value=provider.get(name)
            if value is not None:return value
        return None

@dataclass(frozen=True)
class RetryPolicy:
    max_attempts:int=3
    initial_delay:float=.25
    multiplier:float=2.0
    maximum_delay:float=30.0
    jitter:float=.1
    retryable_exceptions:tuple[type[BaseException],...]=(IntegrationTimeoutError,IntegrationRateLimitError,IntegrationUnavailableError)
    def delay(self,attempt,rng:Callable[[],float]=random.random):
        base=min(self.maximum_delay,self.initial_delay*(self.multiplier**max(0,attempt-1)))
        return max(0.0,base*(1+self.jitter*((rng()*2)-1)))

class CircuitState(str,Enum): CLOSED="closed"; OPEN="open"; HALF_OPEN="half_open"

class CircuitBreaker:
    def __init__(self,failure_threshold=5,recovery_seconds=30.0,clock:Callable[[],float]=time.monotonic):
        self.failure_threshold=max(1,int(failure_threshold));self.recovery_seconds=max(0.0,float(recovery_seconds));self.clock=clock;self.failures=0;self.opened_at=None;self.state=CircuitState.CLOSED
    def allow(self):
        if self.state==CircuitState.OPEN:
            if self.clock()-(self.opened_at or 0)>=self.recovery_seconds:self.state=CircuitState.HALF_OPEN;return True
            return False
        return True
    def success(self): self.failures=0;self.opened_at=None;self.state=CircuitState.CLOSED
    def failure(self):
        self.failures+=1
        if self.state==CircuitState.HALF_OPEN or self.failures>=self.failure_threshold:self.state=CircuitState.OPEN;self.opened_at=self.clock()
    def snapshot(self):return {"state":self.state.value,"failures":self.failures,"failure_threshold":self.failure_threshold,"recovery_seconds":self.recovery_seconds}

@dataclass(frozen=True)
class IntegrationProfile:
    name:str="default"
    timeout_seconds:float=30.0
    verify_tls:bool=True
    proxy_url:str|None=None
    correlation_header:str="X-Correlation-ID"
    retry:RetryPolicy=field(default_factory=RetryPolicy)

@dataclass
class IntegrationResult:
    value:Any
    attempts:int
    correlation_id:str
    elapsed_seconds:float

class ReliableExecutor:
    def __init__(self,profile=IntegrationProfile(),breaker=None,sleep:Callable[[float],None]=time.sleep,clock:Callable[[],float]=time.monotonic):
        self.profile=profile;self.breaker=breaker or CircuitBreaker(clock=clock);self.sleep=sleep;self.clock=clock
    def execute(self,operation:Callable[...,Any],*args,correlation_id=None,**kwargs):
        if not self.breaker.allow():raise CircuitOpenError("connector circuit is open")
        cid=correlation_id or str(uuid.uuid4());start=self.clock();last=None
        for attempt in range(1,max(1,self.profile.retry.max_attempts)+1):
            try:
                value=operation(*args,**kwargs);self.breaker.success();return IntegrationResult(value,attempt,cid,self.clock()-start)
            except self.profile.retry.retryable_exceptions as exc:
                last=exc;self.breaker.failure()
                if attempt>=self.profile.retry.max_attempts or self.breaker.state==CircuitState.OPEN:break
                self.sleep(self.profile.retry.delay(attempt))
        if last is not None:raise last
        raise IntegrationError("operation failed without an exception")

@dataclass(frozen=True)
class HealthReport:
    name:str
    healthy:bool
    latency_ms:float
    detail:str=""

class ConnectorHealthCheck:
    def __init__(self,name,probe:Callable[[],Any],clock:Callable[[],float]=time.monotonic):self.name=name;self.probe=probe;self.clock=clock
    def run(self):
        started=self.clock()
        try:self.probe();return HealthReport(self.name,True,(self.clock()-started)*1000,"ok")
        except Exception as exc:return HealthReport(self.name,False,(self.clock()-started)*1000,f"{exc.__class__.__name__}: {exc}")




