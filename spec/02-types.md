# Types

Core type names are `Any`, `Never`, `Null`, `Bool`, `Int`, `Float`, `Number`, `String`, `List<T>`, `Map<K,V>`, `Set<T>`, `Tuple<T...>`, `Result<T,E>`, `Option<T>`, `Future<T>`, and `Function`. Type annotations are optional. `T?` denotes nullable `T`; `A | B` denotes a union. Records are structural data declarations.

Generic function declarations may declare type parameters and protocol bounds, for example `function show<T: Printable>(value: T) -> String`. Static analysis scopes those type parameters, preserves generic contracts, infers bindings at call sites, and checks declared bounds. Generic-aware compatibility compares nested type arguments recursively while legacy broad compatibility remains available through `compatible()`. Runtime execution still erases annotations and generic parameter lists.
