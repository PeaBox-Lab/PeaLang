

# Modules

A module has a source identity and explicitly exported symbols. Imports resolve relative to the importing module or through package resolution. Non-exported symbols MUST NOT be visible through an imported namespace. Module implementations SHOULD cache an immutable source/package identity.


