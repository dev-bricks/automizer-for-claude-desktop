# -*- coding: utf-8 -*-
"""queue_request.py - einen Aenderungswunsch einreihen, ohne JSON von Hand zu schreiben.

Gedacht fuer alles, was NICHT selbst Dateien bearbeiten will oder soll: ein Agent von
aussen, ein Skript, ein Mensch auf der Kommandozeile. Der Wunsch landet in
`_care/pending/pending-tasks.json`; angewendet wird er von `apply_pending_tasks.py`,
sobald die Desktop-App geschlossen ist.

BEISPIELE

    # Zeitplan einer bestehenden Aufgabe aendern
    python queue_request.py set mein-task --cron "0 8,20 * * *" \\
        --reason "12:00 war dreifach belegt" --by "agent-x"

    # Aufgabe voruebergehend abschalten
    python queue_request.py set mein-task --disabled --reason "Quelle offline"

    # Ordnerfreigaben setzen (ohne die laeuft die Aufgabe ins Leere)
    python queue_request.py set mein-task --folder "C:\\Projekte\\A" --folder "C:\\Projekte\\B"

    # Neue Aufgabe anlegen; Auftragstext aus einer Datei
    python queue_request.py create tagesbericht --cron "0 7 * * *" \\
        --description "Fasst den Vortag zusammen" --body-file auftrag.md

Ohne --by wird "queue_request-cli" eingetragen. Der Wunsch wirkt VERZOEGERT - nach dem
Einreichen mit `apply_pending_tasks.py --status` pruefen, nicht wiederholt einreichen.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claude_desktop_paths as pfade  # noqa: E402


def main():
    p = argparse.ArgumentParser(description="Aenderungswunsch fuer Claude-Desktop-Aufgaben einreihen.")
    p.add_argument("op", choices=["set", "create"])
    p.add_argument("task_id", help="Slug der Aufgabe (= Ordnername unter Scheduled\\)")
    p.add_argument("--cron", help="Zeitplan, z.B. \"0 8,20 * * *\". Bei create Pflicht.")
    p.add_argument("--enabled", dest="enabled", action="store_true", default=None)
    p.add_argument("--disabled", dest="enabled", action="store_false")
    p.add_argument("--model", help="z.B. claude-opus-4-8")
    p.add_argument("--folder", action="append", dest="folders",
                   help="Ordnerfreigabe (wiederholbar); ersetzt die bisherige Liste")
    p.add_argument("--permission-mode", choices=["auto", "bypassPermissions"])
    p.add_argument("--description", default="", help="einzeilige Beschreibung (nur create)")
    p.add_argument("--body-file", help="Datei mit dem Auftragstext (nur create)")
    p.add_argument("--reason", default="", help="warum - erscheint im Log")
    p.add_argument("--by", default="queue_request-cli", help="wer den Wunsch stellt")
    p.add_argument("--care-dir", help="abweichender _care-Ordner (Tests)")
    a = p.parse_args()

    felder = {}
    if a.cron:
        felder["cronExpression"] = a.cron
    if a.enabled is not None:
        felder["enabled"] = a.enabled
    if a.model:
        felder["model"] = a.model
    if a.folders:
        felder["userSelectedFolders"] = a.folders
    if a.permission_mode:
        felder["permissionMode"] = a.permission_mode

    if not felder:
        print("FEHLER: kein einziges Feld angegeben - es gaebe nichts zu tun.")
        return 1
    if a.op == "create" and not a.cron:
        print("FEHLER: create ohne --cron. Die Aufgabe wuerde nie laufen und nicht in der "
              "Liste der App erscheinen.")
        return 1

    wunsch = {
        "op": a.op,
        "taskId": a.task_id,
        "fields": felder,
        "reason": a.reason,
        "requestedBy": a.by,
        "requestedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    if a.op == "create":
        wunsch["description"] = a.description
        if a.body_file:
            try:
                with open(a.body_file, "r", encoding="utf-8") as f:
                    wunsch["skillBody"] = f.read()
            except OSError as e:
                print("FEHLER: Auftragstext nicht lesbar (%s)" % e)
                return 1

    care = a.care_dir or pfade.care_verzeichnis()
    ziel = os.path.join(care, "pending", "pending-tasks.json")

    daten = {"pending": []}
    if os.path.exists(ziel):
        try:
            with open(ziel, "r", encoding="utf-8") as f:
                daten = json.load(f)
            if not isinstance(daten, dict) or not isinstance(daten.get("pending"), list):
                print("FEHLER: %s hat ein ungueltiges Format (muss JSON-Objekt mit 'pending'-Liste sein) - nichts eingereiht." % ziel)
                return 1
        except (ValueError, OSError) as e:
            # Nicht ueberschreiben - sonst gingen fremde Wuensche verloren.
            print("FEHLER: %s ist nicht lesbar (%s) - nichts eingereiht." % (ziel, e))
            return 1

    daten.setdefault("pending", []).append(wunsch)

    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    tmp = ziel + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=2, ensure_ascii=False)
    os.replace(tmp, ziel)

    print("Eingereiht: [%s] %s %s" % (a.op, a.task_id, felder))
    print("Datei:      %s (%d offene Wuensche)" % (ziel, len(daten["pending"])))
    print("Wirkung:    sobald die Desktop-App geschlossen ist und der Merger laeuft.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
