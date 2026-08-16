# Security Policy

## Reporting a Vulnerability

If you discover a potential security vulnerability in `automizer-for-claude-desktop`, please report it responsibly by contacting the maintainers via GitHub Issues or private security advisory.

Please do **not** disclose security vulnerabilities publicly until they have been addressed.

---

## Local-First Security & Safety Architecture

`automizer-for-claude-desktop` is built with a strict local-first, zero-egress philosophy:

1. **Zero External Network Connections:** Automizer makes no outbound or inbound network requests. No telemetry, analytics, or metrics are collected or transmitted.
2. **Path-Based Process Discrimination:** To eliminate false positives, Automizer inspects the execution path of processes (e.g. verifying `*WindowsApps*` or package roots) rather than relying solely on process names (e.g. `claude.exe`), ensuring no conflict with CLI tooling.
3. **Atomic Writes & Automated Backups:** Before any modification to `scheduled-tasks.json`, an automatic timestamped backup is generated. Changes are validated post-write to prevent file corruption.
4. **Field Whitelisting:** Modifications are restricted to explicitly allowed configuration keys (`cronExpression`, `enabled`, `model`, `userSelectedFolders`, `permissionMode`, `disableJitter`). Unsafe keys like `filePath` cannot be modified via queue requests.
5. **Self-Protection Safeguard:** Requests that attempt to disable essential maintenance or supervisory tasks are rejected by default.
6. **Cross-Host Isolation:** In multi-host synchronized setups (such as OneDrive), pending requests tagged for foreign hosts are preserved and not consumed locally.
7. **Zero Elevation Requirement:** All operations execute within standard user privileges. Administrator/root elevation is neither required nor recommended.
