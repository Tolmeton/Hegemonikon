# Security Policy

## Reporting a vulnerability

Please report security concerns **privately**, not through public issues or pull requests.

Use GitHub's private vulnerability reporting:

1. Go to the **Security** tab of this repository.
2. Click **Report a vulnerability**.
3. Describe the issue, with steps or a source that lets it be reproduced or located.

If private reporting is unavailable, open a minimal public issue that says only *"security report — please open a private channel"* (no details), and wait for a private channel before sharing specifics.

## Scope

The published part of this repository (`kernel/`) is **documentation and theory**, not executable software — so the usual class of code vulnerabilities mostly does not apply. What is still in scope and worth reporting:

- Accidentally published secrets, credentials, tokens, or private local paths.
- Malicious or injected content in any published file.
- Links or references that point somewhere harmful.

## Response

This is a single-maintainer project. Reports are handled on a best-effort basis, with priority given to anything involving leaked private state, which is treated as the most serious class of issue.
