# Workflow Help
`workflow.step(name, value)` stores a name, value and `ok=true`. `workflow.result(name, steps)` returns a workflow dictionary with overall status. These helpers provide structure only; they do not persist state, schedule jobs or resume failed workflows.
