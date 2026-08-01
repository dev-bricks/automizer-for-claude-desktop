# Mode 3 — App is **Closed**

This is the only state where task registry modifications can be applied immediately to disk.

---

## Prompt Template

```text
The Claude Desktop App is not running. You can apply pending scheduled task changes now.

1. Verify environment and app state:
     python <module>/tools/apply_pending_tasks.py --paths

2. Queue request (recommended method for backup creation and verification):
     python <module>/tools/queue_request.py set <slug> --cron "0 6 * * *" --by "<identity>"

3. Apply changes:
     python <module>/tools/apply_pending_tasks.py
   (Use --dry-run to preview changes safely)

4. Verify results:
   Review status output (APPLIED, CREATED, SKIPPED, or REJECTED).
```
