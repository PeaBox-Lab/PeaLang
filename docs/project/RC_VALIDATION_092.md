



# PeaLang 0.92 Release Candidate Validation II

0.92 adds no feature family. It deepens certification after the 0.90 freeze.

## Gates
- Evidence must be current, with an explicit maximum age.
- Upgrade drills must prove upgrade, rollback, re-upgrade and identical integrity digests.
- API, diagnostic and bytecode observations across repeated builds must show no drift.
- Security failures, performance regressions and memory growth are evaluated as trends, not one-off snapshots.
- Required ecosystem integrations must have explicit certification evidence.
- Failure-injection drills must demonstrate recovery, integrity and recovery-time compliance.
- Waivers require an owner, reason and unexpired deadline.

As in 0.91, validators consume real evidence. Unit tests prove the validation logic, not unexecuted operating-system, database or cloud certification runs.




