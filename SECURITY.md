# Security Policy

AutoCompiler is currently a pre-1.0 research/development project. Security claims must follow the same rule as the rest of the repository: evidence first, no manufactured readiness.

## Supported state

There is no stable release line with a long-term security-support promise yet.

| Surface | Status |
| --- | --- |
| Current `main` | Actively developed and reviewed |
| Tagged experiments / historical branches | No security-maintenance guarantee |
| Generated automations | Supported only within the capabilities and providers explicitly verified by their manifest/evidence |

Do not infer security support from an old version number, branch name, generated map, or capability declaration.

## Reporting a vulnerability

Do not publish credentials, tokens, private paths, personal data, exploit payloads, or other sensitive proof in a public issue.

Preferred path:

1. Use GitHub's private vulnerability-reporting / Security Advisory flow for this repository when that option is available.
2. Include the affected file or component, reproduction conditions, observed impact, and the smallest safe proof needed to reproduce it.
3. State whether the issue can cross any of these boundaries:
   - `Plan → Authorize → Apply → Verify`;
   - filesystem/path authorization;
   - provider provenance/checksum verification;
   - capability trust/promotion;
   - generated-artifact independence;
   - secret/token handling;
   - local bridge or browser/UI boundaries.

If private reporting is unavailable, open a minimal public issue requesting a private security contact **without** including exploit details or secrets.

## Security invariants

Security-sensitive changes must preserve these repository invariants:

- planning and inspection are read-only;
- protected mutation requires explicit authorization;
- detected resources are not automatically trusted/usable;
- acquired providers require provenance and verification before promotion;
- derived Spider/context state is not capability trust;
- cached evidence cannot grant authorization;
- user-owned paths/resources must not be silently overwritten or removed;
- generated artifacts must not silently gain broader permissions than the authorized plan.

## Secrets

Never commit API keys, access tokens, passwords, OAuth refresh tokens, private keys, cookies, or local secret-store exports.

The existing `vault_provider.py` is an **Obsidian content-vault provider**, not an operating-system secrets manager. Native secret storage remains a separate capability gap until implemented and verified.

## Response expectations

Because the project is pre-1.0, no fixed response-time SLA is promised. Confirmed vulnerabilities should be tracked to a minimal fix, regression proof, and any required evidence/documentation update before being treated as closed.
