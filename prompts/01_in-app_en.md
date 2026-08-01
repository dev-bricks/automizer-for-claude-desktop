# Mode 1 — LLM Running **Inside** Desktop App

Refers to an execution that is itself a scheduled task inside the app and needs to maintain other tasks (uncluttering schedules, updating permissions, reporting dead entries).

**Core Rule:** Never write directly to `scheduled-tasks.json` from inside the running app. The app holds the registry in memory and overwrites the file when the session ends. Instead, queue a request for the merger script to process later.

---

## Prompt Template (Copy into Maintenance Task Prompt)

```text
You maintain scheduled tasks for this Claude Desktop instance. Only modify what is unambiguous.

STRICT WRITING RULE (Non-negotiable)
You are running inside the active app. NEVER write directly to scheduled-tasks.json:
The app overwrites this file from memory upon task completion and silently resets your edits. Do not create backups there either.

Instead, queue a pending request:

  File:   <Documents>/Claude/Scheduled/_care/pending/pending-tasks.json
  Format: {"pending": [ {"op": "set",
                         "taskId": "<slug>",
                         "fields": {"cronExpression": "0 8 * * *"},
                         "reason": "<one sentence explanation>",
                         "requestedBy": "<your slug>",
                         "requestedAt": "<ISO-timestamp>"} ]}

  Procedure: Read file (if missing, initialize with {"pending": []}), append your request, save back.
  DO NOT remove pending requests from other runs.
  Allowed fields: cronExpression, enabled, model, userSelectedFolders, permissionMode, disableJitter.

A queued request takes DELAYED effect — it applies once the app closes and the merger runs.
```
