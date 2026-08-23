# Automizer for Claude Desktop

<img src="assets/banner.png" width="100%" alt="Automizer For Claude Desktop banner">

[![CI](https://github.com/dev-bricks/automizer-for-claude-desktop/actions/workflows/ci.yml/badge.svg)](https://github.com/dev-bricks/automizer-for-claude-desktop/actions/workflows/ci.yml)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D6.svg?logo=windows&logoColor=white)](https://github.com/dev-bricks/automizer-for-claude-desktop)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Version: 1.0.3](https://img.shields.io/badge/version-1.0.3-blue.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ecosystem: dev-bricks](https://img.shields.io/badge/Ecosystem-dev--bricks-blueviolet.svg)](https://github.com/dev-bricks)
[![Umbrella: open-bricks](https://img.shields.io/badge/Umbrella-open--bricks-indigo.svg)](https://github.com/open-bricks)
[![Security: Local-First](https://img.shields.io/badge/Security-Local--First%20%7C%20Zero--Egress-10b981.svg)](SECURITY.md)
[![Pytest](https://img.shields.io/badge/Pytest-25%20passed%20%7C%20100%25-brightgreen.svg)](tests/)
[![LLM Context](https://img.shields.io/badge/LLM%20Context-llms.txt-success.svg)](llms.txt)

**Reliably modify, queue, and manage scheduled tasks for the Claude Desktop App — from inside the app, externally via CLI, or when the app is closed.**

Language: **English** | [Deutsch](README_de.md)

> [!NOTE]
> **AI / LLM Agent Ready:** A structured, machine-readable overview for LLM agents is available at [`llms.txt`](llms.txt).

> [!IMPORTANT]
> **Unofficial Community Tool.** This project is an independent community utility and is not affiliated with, endorsed, or audited by Anthropic. "Claude" and "Claude Desktop" are trademarks of Anthropic and are used here solely for descriptive purposes to identify compatible software.
>
> It reads and writes local configuration files created by the Desktop App. Their format is undocumented and subject to unannounced changes across app releases. Backups are automatically created before every write operation. Use at your own risk.

---

## Quick Navigation

- [Architecture & Queueing Workflow](#architecture--queueing-workflow)
- [End-to-End Task Lifecycle](#end-to-end-task-lifecycle)
- [The Challenge](#the-challenge)
- [The Solution](#the-solution)
- [Key Capabilities & Safety Invariants](#key-capabilities--safety-invariants)
- [Three Operating Modes](#three-operating-modes)
- [Quickstart & Installation](#quickstart--installation)
- [Windowless Background Execution](#windowless-background-execution)
- [Tooling Overview](#tooling-overview)
- [Safety Guarantees & Safeguards](#safety-guarantees--safeguards)
- [Self-Administration Skill](#optional-self-administration-skill)
- [Terminology](#terminology)
- [Privacy & Local Execution](#privacy--local-execution)
- [Sibling Tools & Ecosystem](#sibling-tools--ecosystem)
- [Security & Vulnerability Reporting](#security--vulnerability-reporting)
- [License](#license)

---

## Architecture & Queueing Workflow

```mermaid
flowchart TD
    subgraph AgentOrUser ["User / Agent Request"]
        A["Request Task Change or Creation"] --> B["queue_request.py"]
    end

    subgraph CareQueue ["Pending Queue Layer"]
        B --> C["_care/pending/pending-tasks.json"]
    end

    subgraph BackgroundMerger ["Background Merger (Scheduled Task)"]
        D["apply_pending_tasks.py / VBS Wrapper"] --> E{"Is Claude Desktop Running?"}
        C -. Reads Pending Requests .-> D
        E -- "Yes (Process Running)" --> F["Skip / Defer Execution"]
        E -- "No (App Closed)" --> G["Backup Registry & Create Skill Directory"]
        G --> H["Atomically Update scheduled-tasks.json"]
        H --> I["Log to _care/history/applied-tasks.json"]
    end

    classDef primary fill:#2563eb,stroke:#1d4ed8,color:#fff;
    classDef success fill:#16a34a,stroke:#15803d,color:#fff;
    classDef warning fill:#d97706,stroke:#b45309,color:#fff;
    class A,B primary;
    class G,H,I success;
    class E,F warning;
```

---

## End-to-End Task Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Agent as User / Agent
    participant QR as queue_request.py
    participant PQ as pending-tasks.json
    participant Engine as apply_pending_tasks.py
    participant Paths as claude_desktop_paths.py
    participant App as Claude Desktop Process
    participant Reg as scheduled-tasks.json
    participant Hist as applied-tasks.json

    Agent->>QR: Submit Task Mutation (set / create)
    QR->>PQ: Validate Schema & Append Pending Wish
    Note over Engine: Hourly Background Task / Triggered Run
    Engine->>PQ: Read Pending Wishes
    Engine->>Paths: Query Execution & Process State
    Paths->>App: Check Active Executable Path (*WindowsApps*)
    alt Claude Desktop is Active
        Paths-->>Engine: Process Active
        Engine-->>Agent: Defer Execution (Preserve Pending Wishes)
    else Claude Desktop is Closed
        Paths-->>Engine: Process Inactive (Safe to Write)
        Engine->>Reg: Create Timestamped Backup Snapshot
        Engine->>Reg: Atomically Merge Validated Changes
        Engine->>Reg: Perform Readback Integrity Verification
        Engine->>Hist: Record Execution Report
        Engine->>PQ: Remove Processed Wishes
        Note over App: Next Launch: Claude Desktop loads new schedule
    end
```

---

## The Challenge

The Claude Desktop App manages its scheduled tasks across two separate storage locations:

| Component | Path | Description |
|---|---|---|
| **Task Prompt** | `<Documents>/Claude/Scheduled/<slug>/SKILL.md` | Contains the prompt instructions to execute |
| **Task Registry** | `<AppData>/Claude/local-agent-mode-sessions/<session>/<account>/scheduled-tasks.json` | Stores schedules (`cronExpression`), enabled state, and permissions |

Both components are required for a functional task. Simply creating the prompt folder is insufficient: without a corresponding registry entry and valid `cronExpression`, the task will never trigger and won't appear in the app's schedule overview.

Crucially: **The Desktop App maintains the task registry in memory and writes it back to disk upon session exit.** Any direct modifications made to `scheduled-tasks.json` while the app is active will be silently overwritten and lost without warning.

---

## The Solution

Automizer decouples change requests from disk-write operations through a staged queue:

```
  Queue Request (anytime, in-app or from external agents)
            │
            ▼
    pending-tasks.json ──▶ apply_pending_tasks.py ──▶ Is Claude Desktop Running?
                                                        │
                                        yes ────────────┤  skip and retry next cycle
                                                        │
                                        no ─────────────┴─▶ Backup → Write →
                                                             Verify → Log Report
```

Modifications take effect with a **deliberate delayed execution**. This prevents silent overwrites, avoids race conditions, and provides an auditable history of applied changes.

---

## Key Capabilities & Safety Invariants

| Capability | Technical Mechanism | Security & Reliability Invariant |
|---|---|---|
| **Process Discrimination** | Inspects binary path (`*WindowsApps*`) rather than just process name | Distinguishes Desktop App from Claude Code CLI (`claude.exe`) without false lockouts |
| **Decoupled Staging Queue** | Atomically appends requests to `_care/pending/pending-tasks.json` | Non-blocking write isolation; safe to enqueue mutations from active Claude sessions |
| **Automated Pre-Write Snapshots** | Backs up `scheduled-tasks.json` with timestamped snapshot before writing | Zero data loss; automated recovery rollback capability on malformed edits |
| **Post-Write Readback Verification** | Re-parses JSON and verifies keys immediately after file writes | Guarantees registry integrity before clearing queued mutation requests |
| **Strict Field Whitelisting** | Whitelists allowed schema keys (`cronExpression`, `enabled`, `model`, etc.) | Prevents tampering with internal paths or unvalidated configuration fields |
| **Self-Protection Guard** | Rejects requests disabling tasks matching `CDA_SELF_PROTECT_PREFIX` | Prevents automated agents from accidentally disabling supervisory maintenance tasks |
| **Cross-Host Isolation** | Filters pending requests by matching local hostname | Safe synchronization across multi-device OneDrive environments |
| **Zero-Egress & Standard Library** | 100% Python standard library with zero external dependencies | Completely offline; zero telemetry, zero analytics, zero network exposure |

---

## Three Operating Modes

| Mode | Context | Workflow | Prompt Template |
|---|---|---|---|
| **1. In-App** | LLM running inside Claude Desktop | Append request to `pending-tasks.json` (delayed) | [`prompts/01_in-app_en.md`](prompts/01_in-app_en.md) |
| **2. External (Active)** | External CLI / Agent, app is running | Enqueue request via `queue_request.py` (delayed) | [`prompts/02_from-outside-app-running_en.md`](prompts/02_from-outside-app-running_en.md) |
| **3. App Closed** | App is verified closed | Execute `apply_pending_tasks.py` (immediate) | [`prompts/03_app-closed_en.md`](prompts/03_app-closed_en.md) |

---

## Quickstart & Installation

Prerequisites: **Python 3.8+**. Zero third-party dependencies (standard library only).

```bash
# 1. Verify path detection across local installation
python tools/apply_pending_tasks.py --paths

# 2. Register hourly background merger task (Windows Scheduled Task, no admin needed)
powershell -ExecutionPolicy Bypass -File tools/install_merger_task.ps1

# 3. Acceptance test:
#    a) Trigger while app is open -> changes deferred
#    b) Close app and re-trigger -> changes safely merged
#    c) Zero visible terminal flicker in background mode
```

> [!TIP]
> Always execute the installer via `-File tools/install_merger_task.ps1` rather than pasting snippet contents into PowerShell, ensuring `$PSScriptRoot` resolves reliably.

### Windowless Background Execution

Background execution uses `tools/run_apply_pending_hidden.vbs` wrapping `apply_pending_tasks.py` with `WScript.Shell.Run(cmd, 0, False)` and `subprocess.CREATE_NO_WINDOW` to prevent disruptive console popups.

---

## Tooling Overview

| Script | Purpose |
|---|---|
| [`tools/claude_desktop_paths.py`](tools/claude_desktop_paths.py) | Dynamic path resolution for Documents, registry files, and process detection |
| [`tools/queue_request.py`](tools/queue_request.py) | CLI utility for enqueueing `set` or `create` requests into pending queue |
| [`tools/apply_pending_tasks.py`](tools/apply_pending_tasks.py) | Safe merger engine: verifies app state, backs up registry, merges changes, logs |
| [`tools/install_merger_task.ps1`](tools/install_merger_task.ps1) | PowerShell installer registering scheduled background merger |
| [`tools/run_apply_pending_hidden.vbs`](tools/run_apply_pending_hidden.vbs) | Windowless VBScript launch wrapper |

### Robust Path Resolution

On Windows, the Documents folder may be redirected to OneDrive (Known-Folder-Move). Automizer queries the Windows User Shell Folders registry key (`Personal`) rather than guessing `%USERPROFILE%\Documents`. Session GUIDs in AppData are scanned dynamically to select the latest active session.

---

## Safety Guarantees & Safeguards

1. **Path-Based Process Detection:** Distinguishes the Claude Desktop Windows Store app (`*WindowsApps*`) from the Claude Code CLI (`claude.exe`) to prevent false-positive lockouts.
2. **Field Whitelisting:** Strict schema whitelist (`cronExpression`, `enabled`, `model`, `userSelectedFolders`, `permissionMode`, `disableJitter`).
3. **Self-Protection Guard:** Rejects requests attempting to disable maintenance tasks (prefix customizable via `CDA_SELF_PROTECT_PREFIX`).
4. **Pre-Write Backups & Post-Write Verification:** Automatic snapshot created before every modification, followed by immediate readback verification.
5. **Fail-Closed Cross-Host Isolation:** Pending wishes tagged with foreign host identifiers in multi-device OneDrive setups are preserved rather than consumed locally.
6. **No Silent Drops:** Rejected or malformed wishes are logged with clear diagnostic rationale.

---

## Optional: Self-Administration Skill

This repository provides two independent layers:

1. **The Core Engine** (`tools/`, `prompts/`) — Queueing mechanism and atomic merger for humans and external agents.
2. **The Self-Administration Skill** ([`skill/self-administration-of-scheduled-tasks/SKILL.md`](skill/self-administration-of-scheduled-tasks/SKILL.md)) — An instruction framework enabling Claude Desktop tasks to maintain, monitor, and optimize themselves through five modular supervisory roles.

---

## Terminology

| Term | Definition |
|---|---|
| **Slug** | Short task identifier matching folder name under `Scheduled/<slug>/` and `id` in the task registry |
| **Wish / Request** | A pending mutation record in `pending-tasks.json` awaiting application |
| **Merger** | `apply_pending_tasks.py` engine applying queued requests when the app is inactive |
| **Registry** | The `scheduled-tasks.json` configuration store inside Claude AppData |

---

## Privacy & Local Execution

Automizer operates **100% locally**. It never communicates over external networks, sends zero telemetry, and requires no API keys or credentials.

`pending-tasks.json`, `applied-tasks.json`, and local logs are strictly excluded via `.gitignore` to safeguard system paths and custom prompt instructions.

---

## Sibling Tools & Ecosystem

`automizer-for-claude-desktop` is part of the [`dev-bricks`](https://github.com/dev-bricks) suite under the [`open-bricks`](https://github.com/open-bricks) umbrella:

| Tool | Organization | Focus & Description |
|---|---|---|
| [`safe-start-for-codex`](https://github.com/dev-bricks/safe-start-for-codex) | `dev-bricks` | Safety supervisor & execution guard for autonomous coding agents |
| [`companion-for-agy`](https://github.com/dev-bricks/companion-for-agy) | `dev-bricks` | CLI companion and session coordinator for Antigravity agents |
| [`DevCenter`](https://github.com/dev-bricks/DevCenter) | `dev-bricks` | Central developer workbench and workspace orchestration dashboard |
| [`CodeBox`](https://github.com/dev-bricks/CodeBox) | `dev-bricks` | Local-first code snippet and development asset container |
| [`automation-master`](https://github.com/dev-bricks/automation-master) | `dev-bricks` | Unified multi-agent workflow scheduling and orchestration engine |
| [`MethodenAnalyser`](https://github.com/dev-bricks/MethodenAnalyser) | `dev-bricks` | Structural code analysis and method extraction utility |
| [`coma`](https://github.com/ellmos-ai/coma) | `ellmos-ai` | Cooperative Multi-Agent coordination and lock-free execution protocol |
| [`workflowhooker`](https://github.com/ellmos-ai/workflowhooker) | `ellmos-ai` | Deterministic hook interception and event lifecycle engine |
| [`memoryhooker`](https://github.com/ellmos-ai/memoryhooker) | `ellmos-ai` | Local-first episodic and semantic memory indexing for agents |
| [`open-bricks`](https://github.com/open-bricks) | `open-bricks` | Umbrella organization and open standard specifications |

---

## Security & Vulnerability Reporting

Please review our [Security Policy](SECURITY.md) for details on responsible vulnerability disclosure and our zero-egress commitments.

- **Security Advisories:** [GitHub Security Advisories](https://github.com/dev-bricks/automizer-for-claude-desktop/security/advisories)
- **Security Contacts:** [security@ellmos.ai](mailto:security@ellmos.ai) · [lukas@open-bricks.org](mailto:lukas@open-bricks.org) · [support@lukasgeiger.com](mailto:support@lukasgeiger.com)

---

## License

Released under the [MIT License](LICENSE).

