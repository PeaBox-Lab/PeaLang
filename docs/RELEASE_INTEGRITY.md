



# Release Integrity Policy

Every release from 0.29 onward compares its clean source inventory against the previous release. Unintentional file removal blocks packaging.

The release manifest records file counts, additions, removals, tests, and artifact hashes. Build caches, `__pycache__`, `.pytest_cache`, egg-info, and build directories are excluded from source inventory because they are generated artifacts.

A release is accepted only after the full test suite and Python compilation pass and source ZIP/wheel artifacts are produced.




