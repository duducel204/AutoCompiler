# E-030 — Real external provider acquisition

This experiment replaces the controlled local provider with a genuine third-party release: jq 1.8.2.

Why jq: it is free/open-source (MIT), publishes standalone Windows and Linux binaries, has no runtime dependency, and publishes release checksums. The acquisition is pinned to version 1.8.2 and platform-specific SHA-256 values.

Flow:

```text
json.query capability required
→ jq absent from AutoCompiler-owned provider directory
→ read-only plan
→ unauthorized apply blocked
→ HTTPS download from official jqlang/jq GitHub release
→ SHA-256 verification
→ executable verification with jq --version
→ ownership + consumer registration
→ independent generated automation uses jq
→ result verified
→ rollback/remove deletes AutoCompiler-owned provider
```

This test performs real network acquisition in the canonical Windows and Ubuntu Trust Gate. It deliberately installs into a temporary user-scoped directory and does not modify PATH, package managers, registry, system directories, or require administrator privileges.

Pinned release evidence:
- provider: jq
- version: 1.8.2
- license: MIT
- source: official jqlang/jq GitHub release
- Windows x64 SHA-256: a6fc67fedaf9128a3309a1e2ebb8b986aeccf70122ee46d2cb4849e423f0c627
- Linux x64 SHA-256: b1c22172dd303f3be49e935aa56aa48a8b7a46e0bc838b4997d3bb451495870f
- scope: user/temp
- admin: no
- rollback: delete AutoCompiler-owned provider
- verification: checksum + jq --version
