from pealang.data import DataFrame
from pealang.model_interop import TensorBridge,QueryPolicy,QueryPlan,GovernedQueryPlanner

def test_tensor_dataframe_roundtrip_without_optional_dependencies():
    frame=DataFrame([{"a":1,"b":2},{"a":3,"b":4}]); tensor=TensorBridge.from_dataframe(frame,["a","b"])
    assert tensor==[[1.0,2.0],[3.0,4.0]]
    assert TensorBridge.to_dataframe(tensor,["a","b"]).to_dicts()==frame.to_dicts()

def test_governed_planner_enforces_dataset_operation_and_limit():
    policy=QueryPolicy(("employees",),("select","filter","limit"),100)
    planner=GovernedQueryPlanner(policy)
    good=planner.propose("show top 25 employees",dataset="employees"); assert not good.diagnostics and good.operations[-1]["count"]==25
    bad=planner.validate(QueryPlan("payroll",[{"operation":"delete"},{"operation":"limit","count":500}],"bad"))
    assert "dataset is not allowed" in bad.diagnostics and "operation is not allowed: delete" in bad.diagnostics and "limit exceeds policy" in bad.diagnostics

def test_model_proposal_still_goes_through_policy():
    planner=GovernedQueryPlanner(QueryPolicy(("employees",),maximum_limit=10),lambda _: {"dataset":"secret","operations":[{"operation":"limit","count":99}]})
    plan=planner.propose("anything"); assert plan.diagnostics==["dataset is not allowed","limit exceeds policy"]