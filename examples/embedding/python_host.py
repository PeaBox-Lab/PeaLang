from pealang import PeaRuntime, RuntimeOptions
runtime=PeaRuntime(RuntimeOptions(max_execution_ms=500,max_instructions=10_000))
rules=runtime.load_file('bonus_rules.pea')
print(rules.call('calculate_bonus',{'rating':4,'salary':100000}))
