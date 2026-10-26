



# Native Testing and Migration 0.38

Native test files can use:
```pea
test "bonus is correct" {
    expect calculate_bonus(employee) == 10000
}
```
Commands: `pea test`, `pea test --filter "bonus"`, `pea test --coverage`, `pea test --watch`, and `pea migrate --from 0.37 --to 0.38 .`. The 0.38 coverage report is an explicit test-aware baseline, not a claim of full VM line instrumentation. Migration defaults to compatibility-preserving advisory transformations.




