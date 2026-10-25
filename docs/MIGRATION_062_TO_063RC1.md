


# Migration from 0.62 to 0.63 RC1

1. Back up model registry and monitoring databases.
2. Verify existing model bundles and checksums.
3. Install the RC wheel in an isolated environment.
4. Run API compatibility and migration checks.
5. Run database, cloud, SFTP, SharePoint, Redis and serving smoke tests.
6. Validate rollback to 0.62 before promotion.

No automatic destructive schema migration is introduced in RC1.



