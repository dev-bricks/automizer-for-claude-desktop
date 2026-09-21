# TODO.md — Active work

**Version:** 1.0.4  
**Updated:** 2026-09-21  
**Reason:** Standardization, gate readiness, PEP 639 license inventory, and Plan-D parity  
**Purpose:** Track open items and verify release gate invariants.

## STATUS

| Category | Status | Evidence / next gate |
|---|---|---|
| Core Merger & Applier | DONE | Atomic file writes, automated backup rotations (`*.backup-*`), JSON validation before swap (`INV-ACD-01`, `INV-ACD-03`); verified by automated pytest test suite (100% green). |
| Queueing Interface | DONE | Single-task and batch queueing via `tools/queue_request.py`, strict validation, timestamp-preserving queue files (`INV-ACD-05`). |
| Path Resolution | DONE | Automatic discovery of Claude Desktop SQLite/JSON storage across standard Windows local user data paths. |
| Windowless Background Runner | DONE | VBS wrapper (`run_apply_pending_hidden.vbs`) and PowerShell setup script (`install_merger_task.ps1`) for transparent scheduled execution. |
| Path Neutrality & Hygiene | DONE | Neutral environment patterns, hardened `.gitignore`, zero personal paths, zero hardcoded credentials or secrets. |
| AI Discoverability & Metadata | DONE | Machine-readable `llms.txt`, PEP 621 metadata & classifiers, PEP 639 SPDX license inventory (`THIRD_PARTY_LICENSES.md`). |
| CI Workflows & Multi-Host Defense | DONE | GitHub Actions CI workflow across Python 3.10-3.13, multi-host conflict file protection, atomic merge safeguards. |
| Ecosystem Integration | DONE | Registered in `.MODULES/.ORCHESTRATION/claude-desktop-automizer`, Plan-D pointer configured, shared under `dev-bricks` / `open-bricks`. |
| Public Release Gate | USER | MIT License confirmed; 10/10 automated release gates passing; explicit public visibility release pending user decision. |

## Formalized next tasks

- [ ] **TASK-ACD-01: Multi-Profil-Erkennung für Claude Desktop** (`effort=medium`, `scope=paths`, priority `normal`).
  - **Ziel:** Unterstützung für mehrere parallele Instanzen oder Profile der Desktop-Applikation erweitern.
  - **Definition of Done:** Profil-Flag in `tools/claude_desktop_paths.py` und automatisierte Tests.

- [ ] **TASK-ACD-02: macOS / Linux Launchd- & Cron-Adapter** (`effort=large`, `scope=os`, priority `low`).
  - **Ziel:** Erweiterung der Hintergrund-Synchronisation auf Unix-Umgebungen via Launchd bzw. Systemd-Timer.
  - **Definition of Done:** Plattform-Erkennung und plattformspezifische Runner-Skripte mit Testabdeckung.

- [x] **TASK-ACD-03: Release-Hygiene, Lizenzinventar & Gate-Bereitschaft (v1.0.3)** (`effort=low`, `scope=hygiene`, priority `high`).
  - **Ergebnis:** Standard-`TODO.md` mit `## STATUS`-Tabelle etabliert, `THIRD_PARTY_LICENSES.md` angelegt, `.gitignore` gehärtet, `final_gate_check.py` auf 10/10 PASS gebracht.

- [x] **TASK-ACD-04: CI-Workflow, PEP 621 Metadaten & Plan-D-Parität (v1.0.3)** (`effort=low`, `scope=metadata`, priority `high`).
  - **Ergebnis:** GitHub Actions CI mit Python 3.10-3.13, Single-Source-Versionierung, Plan-D-Spiegel `.MODULES/.ORCHESTRATION/claude-desktop-automizer` mit `PLAN_D_POINTER.md` synchronisiert.

---
<!-- REMEMBER: ENDUSERTEXTE BEKOMMEN ECHTE UMLAUTE Ü Ö Ä ß -->
