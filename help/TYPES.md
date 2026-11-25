# Type help

Use optional annotations, generics such as `function first<T>(items: List<T>) -> T?`, protocol bounds such as `function show<T: Printable>(value: T)`, and `Result<T,E>`, `Option<T>`, `Future<T>`. Static analysis scopes type parameters, infers type arguments at call sites, checks bounds, and compares nested generic arguments. Runtime annotations remain erased.
