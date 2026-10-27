# Security Policy

## Supported Versions

PeaLang is under active development. Security fixes are provided for the latest stable release.

| Version | Supported |
| ------- | --------- |
| Latest stable release | Yes |
| Older releases | No |
| Historical pre-release versions | No |

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub Issues, Discussions, or pull requests.

If you discover a potential security vulnerability in PeaLang, please report it privately to the maintainers.

When reporting a vulnerability, please include:

- A clear description of the vulnerability
- The affected PeaLang version
- The affected file, module, or component
- Steps required to reproduce the issue
- A proof of concept, if available
- Potential security impact
- Any suggested mitigation or fix

Please allow reasonable time for investigation and remediation before publicly disclosing the vulnerability.

## Security Response

Reports will be reviewed and prioritized according to severity and potential impact.

Where appropriate, a fix will be developed, tested, and released as a security update.

Security-related releases may include:

- Source code fixes
- Regression tests
- Dependency updates
- Updated release notes
- Security advisories
- Updated SBOM or provenance information when applicable

## Scope

Security reports may include vulnerabilities involving:

- PeaLang interpreter or runtime
- Parsers and compilers
- Package and module handling
- File system operations
- Network functionality
- Data connectors
- Plugin or extension mechanisms
- Code execution
- Sandboxing or isolation
- Authentication or authorization functionality
- Dependency and supply-chain security

## Responsible Disclosure

Please provide maintainers with sufficient time to investigate and address a vulnerability before publishing technical details.

Good-faith security research and responsible disclosure are appreciated.

## Security Best Practices

Users should:

- Use the latest stable PeaLang release
- Keep dependencies updated
- Verify downloaded release artifacts where checksums or signatures are provided
- Avoid running untrusted PeaLang programs with elevated privileges
- Review third-party plugins and extensions before use
- Never commit credentials, API keys, tokens, or private keys to PeaLang projects
