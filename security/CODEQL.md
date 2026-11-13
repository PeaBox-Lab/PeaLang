# CodeQL configuration

PeaLang uses GitHub's **default setup** for code scanning. Default setup analyses
the repository on push, pull request and a weekly schedule, and its results
appear under Security > Code scanning.

Default setup was enabled on 2026-10-27 with the `default` query suite.

## Why the workflow does not run CodeQL

`.github/workflows/security-scanners.yml` used to run an advanced-setup job
(`github/codeql-action/init` + `analyze` with `queries: security-extended`).
GitHub rejects SARIF uploads from advanced configurations while default setup is
enabled, so every run failed at the analyze step with:

```
Code Scanning could not process the submitted SARIF file:
CodeQL analyses from advanced configurations cannot be processed when the default setup is enabled
```

The job was removed so the workflow stays green; the `dependency-audit` job
remains and still runs `pip-audit` on every push, pull request and schedule.

## Switching to the advanced configuration

Only do this if you need `security-extended` or a custom query pack and you want
the configuration versioned in this repository.

1. Disable default setup: Settings > Code security > Code scanning > CodeQL
   analysis > Disable.
2. Restore the `codeql` job in `.github/workflows/security-scanners.yml`:

   ```yaml
   codeql:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v4
       - uses: github/codeql-action/init@v3
         with:
           languages: python
           queries: security-extended
       - uses: github/codeql-action/analyze@v3
   ```

3. Push to `master` and confirm the analyze step uploads results.

Never enable default setup and an advanced workflow at the same time; that is
the combination that fails.
