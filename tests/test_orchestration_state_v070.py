

from datetime import datetime, timezone
import pytest
from pealang.orchestration import DAG
from pealang.orchestration_state import DurableDAGRunner, RetryPolicy, Schedule, SQLiteStateStore

def test_retry_and_dependencies():
    dag=DAG("etl"); calls={"n":0}
    @dag.task("extract")
    def extract():
        calls["n"]+=1
        if calls["n"]<2: raise ValueError("temporary")
        return 4
    @dag.task("load",depends_on=("extract",))
    def load(dependencies): return dependencies["extract"]+1
    store=SQLiteStateStore(); r=DurableDAGRunner(store,sleep=lambda _:None).run(dag,logical_date="2026-10-24T00:00:00Z",retry=RetryPolicy(max_attempts=2))
    assert r.results=={"extract":4,"load":5}; assert r.attempts["extract"]==2

def test_idempotent_rerun_skips_success():
    dag=DAG("once"); calls=[]
    @dag.task("a")
    def a(): calls.append(1); return {"ok":True}
    runner=DurableDAGRunner(SQLiteStateStore())
    runner.run(dag,logical_date="d"); second=runner.run(dag,logical_date="d")
    assert len(calls)==1 and second.states["a"]=="skipped" and second.results["a"]=={"ok":True}

def test_schedule_and_backfill():
    dag=DAG("hourly")
    @dag.task("x")
    def x(): return 1
    start=datetime(2026,1,1,tzinfo=timezone.utc); end=datetime(2026,1,1,2,tzinfo=timezone.utc)
    runs=DurableDAGRunner(SQLiteStateStore()).backfill(dag,start,end,Schedule(3600))
    assert len(runs)==3

def test_schedule_rejects_bad_interval():
    with pytest.raises(ValueError): Schedule(0).occurrences(datetime.now(timezone.utc),datetime.now(timezone.utc))


