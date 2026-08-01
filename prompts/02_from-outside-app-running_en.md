# Mode 2 — External Access While App is Running

Refers to an agent or human outside the Desktop App (CLI agent, terminal, automation system) attempting to create or modify a task while the app is active.

---

## Prompt Template

```text
You need to modify a scheduled task for the Claude Desktop App. The app is currently running.

DO NOT write directly to scheduled-tasks.json — the app will silently overwrite it.
Queue the request instead:

  python <module>/tools/queue_request.py set <slug> --cron "0 8,20 * * *" \
      --reason "<why>" --by "<identity>"

Additional parameters: --disabled / --enabled, --model <name>,
--folder <path> (repeatable, replaces folder permissions),
--permission-mode auto|bypassPermissions

Check pending status:
  python <module>/tools/apply_pending_tasks.py --status

The request takes effect once the app is closed and the merger runs. Inform the user that the request is queued and pending app closure.
```
