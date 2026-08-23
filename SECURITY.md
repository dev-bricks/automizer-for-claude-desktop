# Security Policy / Sicherheitsrichtlinie

## Reporting a Vulnerability / Sicherheitslücke melden

If you discover a potential security vulnerability in `automizer-for-claude-desktop`, please report it responsibly rather than disclosing it publicly:

- **Primary Security Contact:** [security@ellmos.ai](mailto:security@ellmos.ai)
- **Maintainer Direct Contact:** [lukas@open-bricks.org](mailto:lukas@open-bricks.org)
- **Support Contact:** [support@lukasgeiger.com](mailto:support@lukasgeiger.com)
- **GitHub Security Advisories:** [dev-bricks/automizer-for-claude-desktop Security Advisories](https://github.com/dev-bricks/automizer-for-claude-desktop/security/advisories)

Please include a detailed description of the vulnerability, reproduction steps, affected operating system environments, and any potential exploit scenarios. We acknowledge reports promptly and coordinate fixes prior to public release.

---

## Supported Versions / Unterstützte Versionen

| Version | Status | Security Fixes |
|---|---|---|
| `1.0.x` | Active / Supported | Full patch and security updates |
| `< 1.0.0` | Deprecated / End of Life | None (please upgrade to latest release) |

---

## Local-First Security & Safety Architecture (EN)

`automizer-for-claude-desktop` is built with a strict local-first, zero-egress philosophy:

1. **Zero External Network Connections:** Automizer makes no outbound or inbound network requests. No telemetry, analytics, or metrics are collected or transmitted.
2. **Path-Based Process Discrimination:** To eliminate false positives, Automizer inspects the execution path of processes (e.g. verifying `*WindowsApps*` or package roots) rather than relying solely on process names (e.g. `claude.exe`), ensuring no conflict with CLI tooling.
3. **Atomic Writes & Automated Backups:** Before any modification to `scheduled-tasks.json`, an automatic timestamped backup is generated. Changes are validated post-write to prevent file corruption.
4. **Field Whitelisting:** Modifications are restricted to explicitly allowed configuration keys (`cronExpression`, `enabled`, `model`, `userSelectedFolders`, `permissionMode`, `disableJitter`). Unsafe keys like `filePath` cannot be modified via queue requests.
5. **Self-Protection Safeguard:** Requests that attempt to disable essential maintenance or supervisory tasks are rejected by default (customizable via `CDA_SELF_PROTECT_PREFIX`).
6. **Cross-Host Isolation:** In multi-host synchronized setups (such as OneDrive), pending requests tagged for foreign hosts are preserved and not consumed locally.
7. **Zero Elevation Requirement:** All operations execute within standard user privileges. Administrator/root elevation is neither required nor recommended.

---

## Local-First Sicherheits- und Schutzarchitektur (DE)

1. **Keine externen Netzwerkverbindungen (Zero-Egress):** Automizer führt keinerlei ausgehende oder eingehende Netzwerkverbindungen durch. Keine Telemetrie, keine Analyse- oder Trackingdaten.
2. **Pfadbasierte Prozessunterscheidung:** Zur Vermeidung von Fehlalarmen prüft Automizer den genauen Programmpfad (z. B. `*WindowsApps*`) statt nur den Prozessnamen (`claude.exe`), um Verwechslungen mit CLI-Werkzeugen auszuschließen.
3. **Atomare Schreibvorgänge & automatische Backups:** Vor jeder Änderung an `scheduled-tasks.json` wird ein zeitgestempeltes Backup erstellt. Nach dem Schreiben erfolgt eine sofortige Validierung.
4. **Strikte Positivliste erlaubter Felder (Field Whitelisting):** Nur explizit zulässige Konfigurationsschlüssel (`cronExpression`, `enabled`, `model`, `userSelectedFolders`, `permissionMode`, `disableJitter`) dürfen verändert werden.
5. **Selbstschutz vor Deaktivierung:** Anfragen zur Deaktivierung geschützter Wartungs- und Überwachungsaufgaben werden standardmäßig abgewiesen.
6. **Host-Isolierung in Multi-Device-Umgebungen:** In synchronisierten Umgebungen (wie OneDrive) bleiben fremde Host-Wünsche erhalten und werden nicht lokal verarbeitet.
7. **Keine Administratorrechte nötig:** Alle Operationen laufen im normalen Benutzermodus ohne erhöhte Rechte.
