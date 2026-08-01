# Automizer for Claude Desktop

**Reliably manage and modify scheduled tasks for the Claude Desktop App — from inside the app, from the outside, or when the app is closed.**

> [!NOTE]
> **Unofficial Tool.** This project is an independent community utility and is not affiliated with, endorsed, or audited by Anthropic. "Claude" and "Claude Desktop" are trademarks of Anthropic and are used here solely for descriptive purposes to identify compatible software.
>
> It reads and writes local configuration files created by the Desktop App. Their format is undocumented and subject to unannounced changes across app releases. Backups are automatically created before every write operation. Use at your own risk.

Status: Draft · Tested on Windows (macOS/Linux see [ROADMAP.md](ROADMAP.md)) · License: MIT

Language: [German (Canonical)](README.md) | **English**

---

## The Problem

The Claude Desktop App manages its scheduled tasks in two separate locations:

| What | Where |
|---|---|
| **Task Prompt** — what needs to be done | `<Documents>/Claude/Scheduled/<slug>/SKILL.md` |
| **Task Registry** — when it needs to run | `<AppData>/Claude/local-agent-mode-sessions/<session>/<account>/scheduled-tasks.json` |

Only both combined yield a functional scheduled task. Simply creating the directory is insufficient: without an entry in the task registry — and without a valid `cronExpression` inside it — the task will never execute and won't even appear in the app's UI.

Furthermore, **the app keeps the task registry in memory and completely overwrites the file on disk upon finishing a run.** Modifying `scheduled-tasks.json` while the app is running causes changes to be silently lost.

## The Solution

Requested changes are decoupled from direct disk writing:

```
  Queue Request (anytime, from inside or outside)
            │
            ▼
   pending-tasks.json ──▶ apply_pending_tasks.py ──▶ Is App Running?
                                                       │
                                       yes ────────────┤  do nothing, retry later
                                                       │
                                       no ─────────────┴─▶ Backup → write →
                                                            verify → log report
```

Requests act with a **delayed effect**. This ensures changes are never silently overwritten and remain fully auditable.

---

## The Three Operating Modes

| # | Situation | Capability | Prompt Template |
|---|---|---|---|
| 1 | LLM running **inside** the app | Queue request (delayed) | [`prompts/01_in-app_en.md`](prompts/01_in-app_en.md) |
| 2 | Access **from outside**, app running | Queue request via CLI (delayed) | [`prompts/02_from-outside-app-running_en.md`](prompts/02_from-outside-app-running_en.md) |
| 3 | App is **closed** | Apply directly (immediate) | [`prompts/03_app-closed_en.md`](prompts/03_app-closed_en.md) |

---

## Installation & Usage

Prerequisites: Python 3.8+. No dependencies outside the standard library.

```bash
# 1. Verify paths — check if local task registries are detected
python tools/apply_pending_tasks.py --paths

# 2. Register background merger task (Windows Scheduled Task, no admin required)
powershell -ExecutionPolicy Bypass -File tools/install_merger_task.ps1

# 3. Queue a request (Mode 2)
python tools/queue_request.py set <slug> --cron "0 8 * * *" --reason "Morning run" --by "cli"

# 4. Dry-run or apply pending requests (Mode 3)
python tools/apply_pending_tasks.py --dry-run
python tools/apply_pending_tasks.py
```
