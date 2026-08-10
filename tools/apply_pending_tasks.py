# -*- coding: utf-8 -*-
"""apply_pending_tasks.py - wendet Aenderungswuensche auf die Claude-Desktop-Aufgaben an.

DAS PROBLEM
Die Desktop-App haelt ihre Aufgabenliste im Speicher und schreibt sie beim Ende eines
Laufs komplett neu. Wer die Datei aendert, waehrend die App laeuft, verliert die
Aenderung wieder - lautlos. Das gilt fuer Laeufe INNERHALB der App genauso wie fuer
Werkzeuge von aussen.

DIE LOESUNG
Wuensche werden entkoppelt: Wer etwas aendern will, schreibt einen Wunsch nach
`_care/pending/pending-tasks.json`. Dieses Werkzeug laeuft ausserhalb der App und
wendet die Wuensche an, sobald die App geschlossen ist.

    Wunsch schreiben (jederzeit, von innen wie von aussen)
              |
              v
    pending-tasks.json  --->  apply_pending_tasks.py  --->  App zu?
                                                              |  nein -> nichts tun
                                                              |  ja   -> Backup, schreiben,
                                                                        verifizieren, protokollieren

UNTERSTUETZTE OPERATIONEN
    set     Felder einer bestehenden Aufgabe aendern
    create  neue Aufgabe anlegen (Auftragstext + Registry-Eintrag)
Loeschen ist bewusst NICHT vorgesehen - das bleibt dem Menschen in der App.

AUFRUF
    python apply_pending_tasks.py                 normaler Lauf
    python apply_pending_tasks.py --status        Kurzstatus, aendert nichts
    python apply_pending_tasks.py --dry-run       zeigt nur, was passieren wuerde
    python apply_pending_tasks.py --rollback <id> Rollback der letzten set-Aenderung
    python apply_pending_tasks.py --report <path> Trockenlauf-Bericht schreiben
    python apply_pending_tasks.py --paths         gefundene Pfade zeigen (Fehlersuche)
    python apply_pending_tasks.py --registry <p> --care-dir <p> --ignore-app-state
                                                  NUR FUER TESTS gegen Kopien

Exit-Codes: 0 = ok (auch "App laeuft, nichts getan"), 1 = Fehler.
"""
import argparse
import json
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claude_desktop_paths as pfade  # noqa: E402

# Aufgaben mit diesem Praefix duerfen nicht abgeschaltet werden (Selbstschutz des
# Pflegeverbunds). Wer kein Praefix nutzt, setzt hier "" - dann entfaellt der Schutz.
SELBSTSCHUTZ_PREFIX = os.environ.get("CDA_SELF_PROTECT_PREFIX", "claude-desktop-")

# Nur diese Felder duerfen per "set" geaendert werden. Alles andere wird abgelehnt -
# insbesondere filePath, damit kein Wunsch auf fremde Dateien umbiegen kann.
ERLAUBTE_FELDER = {
    "cronExpression", "enabled", "model", "userSelectedFolders",
    "permissionMode", "disableJitter",
}

ERLAUBTE_MODI = {"auto", "bypassPermissions"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def lade(pfad, default):
    """Liest JSON. Fehlende Datei -> default. Kaputte Datei -> None (Aufrufer bricht ab)."""
    if not os.path.exists(pfad):
        return default
    try:
        with open(pfad, "r", encoding="utf-8") as f:
            return json.load(f)
    except (ValueError, OSError):
        return None


def schreibe(pfad, daten):
    if isinstance(daten, str):
        content = daten
    else:
        content = json.dumps(daten, indent=2, ensure_ascii=False)
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    tmp = pfad + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp, pfad)


def log(logpfad, zeilen):
    if not zeilen:
        return
    try:
        os.makedirs(os.path.dirname(logpfad), exist_ok=True)
        with open(logpfad, "a", encoding="utf-8") as f:
            f.write("\n## %s - apply_pending_tasks\n\n" % time.strftime("%Y-%m-%d %H:%M"))
            for z in zeilen:
                f.write("- %s\n" % z)
    except OSError as e:
        print("WARNUNG: Log nicht schreibbar (%s)" % e)


def ist_fremder_host(w, nach_id):
    """True, wenn ein set-Wunsch eine hier nicht registrierte Aufgabe meint.

    pending-tasks.json liegt in OneDrive und wird von ALLEN Hosts geteilt; die Registry
    (scheduled-tasks.json) liegt hostlokal unter %APPDATA%. Ein Wunsch fuer eine Aufgabe,
    die nur der andere Host kennt, ist hier kein Fehler - er ist nicht zustaendig und muss
    in der Warteschlange bleiben, sonst loescht ihn der erste Lauf auf dem falschen Host.

    Belegt am 2026-08-01: WORKSTATION-LG hatte 1 registrierte Aufgabe, ASUS-GEI mehrere;
    alle 4 offenen Wuensche gehoerten zu ASUS-Aufgaben und waeren hier verlorengegangen.

    Nur fuer op="set". Ein create-Wunsch, dessen Aufgabe hier bereits existiert, ist eine
    echte Kollision und wird weiterhin abgelehnt.
    """
    return (isinstance(w, dict)
            and w.get("op", "set") == "set"
            and isinstance(w.get("taskId"), str)
            and w["taskId"] not in nach_id)


LOKALER_HOST = (os.environ.get("COMPUTERNAME") or "").strip().upper()


def ist_fuer_fremden_host(w):
    """True, wenn ein Wunsch ausdruecklich einem ANDEREN Host zugeordnet ist.

    ist_fremder_host() oben erkennt Unzustaendigkeit nur daran, dass es die Aufgabe
    hier nicht gibt. Das genuegte, solange jeder Slug nur auf einem Host registriert
    war. Seit dem 2026-08-10 fuehrt WORKSTATION-LG denselben Pflegeverbund wie
    ASUS-GEI - damit ist jeder Wunsch des Nachbarhosts hier formal "zustaendig" und
    wuerde angewendet, obwohl er gegen dessen Belegungsprofil gemessen wurde.

    Deshalb das Feld "host" im Wunsch (queue_request.py setzt es). Wuensche OHNE das
    Feld verhalten sich wie bisher - Altbestand bleibt gueltig. Ist der eigene
    Hostname nicht ermittelbar, wird fail-closed entschieden: lieber stehen lassen
    als den Wunsch des anderen Hosts verbrauchen.
    """
    if not isinstance(w, dict):
        return False
    h = w.get("host")
    if not isinstance(h, str) or not h.strip():
        return False
    if not LOKALER_HOST:
        return True
    return h.strip().upper() != LOKALER_HOST


def pruefe_set(w, nach_id):
    if not isinstance(w, dict):
        return False, "ABGELEHNT: Ungueltiger Wunsch-Eintrag (kein JSON-Objekt)"
    tid = w.get("taskId")
    felder = w.get("fields")
    wer = w.get("requestedBy", "?")

    if not tid or not isinstance(tid, str) or not isinstance(felder, dict) or not felder:
        return False, "ABGELEHNT (%s): Wunsch ohne gueltige taskId oder ohne fields" % wer
    if tid not in nach_id:
        # Kein Fehler, sondern Unzustaendigkeit: pending-tasks.json wird ueber OneDrive von
        # allen Hosts geteilt, die Registries liegen aber hostlokal unter %APPDATA%. Der
        # Wunsch gehoert dann dem anderen Host und darf hier NICHT verworfen werden -
        # siehe ist_fremder_host() und den Aufrufer.
        return False, ("UEBERGANGEN (%s): Aufgabe '%s' gibt es auf diesem Host nicht - "
                       "Wunsch bleibt fuer den zustaendigen Host stehen" % (wer, tid))

    unerlaubt = set(felder) - ERLAUBTE_FELDER
    if unerlaubt:
        return False, "ABGELEHNT (%s/%s): unerlaubte Felder %s" % (wer, tid, sorted(unerlaubt))

    modus = felder.get("permissionMode")
    if modus is not None and modus not in ERLAUBTE_MODI:
        return False, ("ABGELEHNT (%s/%s): permissionMode '%s' unbekannt (erlaubt: %s)"
                       % (wer, tid, modus, ", ".join(sorted(ERLAUBTE_MODI))))

    if SELBSTSCHUTZ_PREFIX and tid.startswith(SELBSTSCHUTZ_PREFIX) and felder.get("enabled") is False:
        return False, ("ABGELEHNT (%s): '%s' ist eine Pflegeaufgabe und darf nicht deaktiviert "
                       "werden (Selbstschutz)" % (wer, tid))
    return True, None


def pruefe_create(w, nach_id, scheduled_dir):
    if not isinstance(w, dict):
        return False, "ABGELEHNT: Ungueltiger Wunsch-Eintrag (kein JSON-Objekt)"
    tid = w.get("taskId")
    wer = w.get("requestedBy", "?")
    felder = w.get("fields")

    if not tid or not isinstance(tid, str) or not SLUG_RE.match(tid):
        return False, ("ABGELEHNT (%s): '%s' ist kein gueltiger Slug (klein, a-z 0-9 -)"
                       % (wer, tid))
    if tid in nach_id:
        return False, "ABGELEHNT (%s): Aufgabe '%s' existiert bereits - nutze 'set'" % (wer, tid)

    if not isinstance(felder, dict):
        return False, "ABGELEHNT (%s/%s): 'fields' muss ein JSON-Objekt sein" % (wer, tid)

    unerlaubt = set(felder) - ERLAUBTE_FELDER
    if unerlaubt:
        return False, "ABGELEHNT (%s/%s): unerlaubte Felder %s" % (wer, tid, sorted(unerlaubt))

    if not felder.get("cronExpression") or not isinstance(felder.get("cronExpression"), str):
        return False, ("ABGELEHNT (%s/%s): create ohne cronExpression - die Aufgabe wuerde nie "
                       "laufen und nicht in der Liste erscheinen" % (wer, tid))

    modus = felder.get("permissionMode")
    if modus is not None and modus not in ERLAUBTE_MODI:
        return False, ("ABGELEHNT (%s/%s): permissionMode '%s' unbekannt (erlaubt: %s)"
                       % (wer, tid, modus, ", ".join(sorted(ERLAUBTE_MODI))))

    body = w.get("skillBody")
    ziel = os.path.join(scheduled_dir, tid, "SKILL.md")
    if not body and not os.path.exists(ziel):
        return False, ("ABGELEHNT (%s/%s): weder skillBody uebergeben noch vorhandene SKILL.md "
                       "unter %s" % (wer, tid, ziel))
    return True, None


def schreibe_skill_datei(scheduled_dir, tid, w):
    """Legt <Scheduled>/<slug>/SKILL.md an. Gibt den Pfad zurueck."""
    ordner = os.path.join(scheduled_dir, tid)
    os.makedirs(ordner, exist_ok=True)
    ziel = os.path.join(ordner, "SKILL.md")
    if os.path.exists(ziel):
        return ziel

    beschreibung = (w.get("description") or "").replace("\n", " ").strip()
    inhalt = "---\nname: %s\ndescription: %s\n---\n\n%s\n" % (
        tid, beschreibung, (w.get("skillBody") or "").strip())
    with open(ziel, "w", encoding="utf-8") as f:
        f.write(inhalt)
    return ziel


def schreibe_bericht(report_pfad, reg_pfad, care, pending_pfad, app_laeuft, modus, meldungen):
    lines = [
        "# Merger Dry-Run-Bericht",
        "",
        "- **Zeit:** %s" % time.strftime("%Y-%m-%d %H:%M:%S"),
        "- **Registry:** `%s`" % reg_pfad,
        "- **CARE-Verzeichnis:** `%s`" % care,
        "- **Pending-Pfad:** `%s`" % pending_pfad,
        "- **Desktop-App:** %s" % ("laeuft" if app_laeuft else "geschlossen"),
        "- **Modus:** %s" % modus,
        "",
        "## Entscheidungen und Protokoll",
        "",
    ]
    if meldungen:
        for m in meldungen:
            lines.append("- %s" % m)
    else:
        lines.append("- Keine Aenderungen oder Entscheidungen protokolliert.")
    lines.extend([
        "",
        "## Status",
        "- Exit Code: 0",
        "- naechster Schritt: sobald die Desktop-App geschlossen ist, verarbeitet der Merger offene Wuensche.",
        "",
    ])
    schreibe(report_pfad, "\n".join(lines))


def main():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--status", action="store_true")
    p.add_argument("--paths", action="store_true", help="gefundene Pfade zeigen")
    p.add_argument("--rollback", help="taskId (Slug) fuer den Rollback der letzten angewandten set-Aenderung")
    p.add_argument("--report", help="Pfad fuer den persistenten Bericht (z. B. _care/reports/dry-run.md)")
    p.add_argument("--registry")
    p.add_argument("--care-dir")
    p.add_argument("--ignore-app-state", action="store_true",
                   help="NUR FUER TESTS gegen eine Registry-Kopie")
    a = p.parse_args()

    if a.paths:
        print(pfade.diagnose())
        return 0

    care = a.care_dir or pfade.care_verzeichnis()
    scheduled_dir = os.path.dirname(care) if a.care_dir else pfade.scheduled_verzeichnis()
    pending_pfad = os.path.join(care, "pending", "pending-tasks.json")
    applied_pfad = os.path.join(care, "pending", "applied-tasks.json")
    logpfad = os.path.join(care, "CARE-LOG.md")

    reg_pfad = a.registry or pfade.registry_pfad()
    if not reg_pfad or not os.path.exists(reg_pfad):
        print("FEHLER: Registry nicht gefunden. Diagnose:\n%s" % pfade.diagnose())
        log(logpfad, ["FEHLER: Registry nicht gefunden (%s)" % reg_pfad])
        return 1

    reg = lade(reg_pfad, None)
    if not isinstance(reg, dict) or "scheduledTasks" not in reg or not isinstance(reg.get("scheduledTasks"), list):
        print("FEHLER: Registry unlesbar oder unerwartetes Format: %s" % reg_pfad)
        log(logpfad, ["FEHLER: Registry unlesbar: %s" % reg_pfad])
        return 1
    nach_id = {t.get("id"): t for t in reg["scheduledTasks"] if isinstance(t, dict) and isinstance(t.get("id"), str)}

    app_laeuft = False if a.ignore_app_state else pfade.app_laeuft()

    # --- ROLLBACK MODUS ---
    if a.rollback:
        rollback_tid = a.rollback
        hist = lade(applied_pfad, None)
        if not isinstance(hist, dict) or "applied" not in hist or not isinstance(hist.get("applied"), list):
            print("FEHLER: Historie %s ist unlesbar oder hat unerwartetes Format." % applied_pfad)
            log(logpfad, ["FEHLER: Historie %s unlesbar für Rollback von '%s'" % (applied_pfad, rollback_tid)])
            return 1

        passende = [e for e in hist["applied"] if isinstance(e, dict) and e.get("taskId") == rollback_tid]
        if not passende:
            print("FEHLER: Kein angewandter Eintrag fuer '%s' in der Historie gefunden." % rollback_tid)
            log(logpfad, ["FEHLER: Rollback fuer '%s' fehlgeschlagen (kein Historieneintrag)" % rollback_tid])
            return 1

        letzter = passende[-1]
        if letzter.get("op") != "set":
            print("FEHLER: Rollback fuer 'create' ('%s') wird nicht unterstuetzt - Loeschen bleibt dem Menschen in der App vorbehalten." % rollback_tid)
            log(logpfad, ["FEHLER: Rollback fuer 'create' ('%s') abgelehnt" % rollback_tid])
            return 1

        previous = letzter.get("previousValues")
        if not isinstance(previous, dict):
            print("FEHLER: Fuer '%s' existiert kein gespeicherter Vorzustand (previousValues)." % rollback_tid)
            log(logpfad, ["FEHLER: Rollback fuer '%s' abgelehnt (keine previousValues)" % rollback_tid])
            return 1

        if rollback_tid not in nach_id:
            print("FEHLER: Aufgabe '%s' existiert nicht mehr in der Registry." % rollback_tid)
            log(logpfad, ["FEHLER: Rollback fuer '%s' abgelehnt (nicht in Registry)" % rollback_tid])
            return 1

        eintrag = nach_id[rollback_tid]
        ist_werte = {k: eintrag.get(k) for k in previous}
        meldungen = []

        if ist_werte == previous:
            msg = "HINWEIS (%s): '%s' steht bereits auf den Werten des Vorzustands (%s)" % (letzter.get("requestedBy", "?"), rollback_tid, previous)
            meldungen.append(msg)
            print(msg)
            if a.report:
                schreibe_bericht(a.report, reg_pfad, care, pending_pfad, app_laeuft, "rollback", meldungen)
            return 0

        if a.dry_run:
            msg = "DRY-RUN rollback %s: %s -> %s" % (rollback_tid, ist_werte, previous)
            meldungen.append(msg)
            print(msg)
            if a.report:
                schreibe_bericht(a.report, reg_pfad, care, pending_pfad, app_laeuft, "rollback dry-run", meldungen)
            return 0

        shutil.copyfile(reg_pfad, reg_pfad + ".backup-" + time.strftime("%Y%m%d-%H%M%S"))
        eintrag.update(previous)
        schreibe(reg_pfad, reg)
        msg = "ROLLBACK ANGEWANDT (%s): %s %s -> %s" % (letzter.get("requestedBy", "?"), rollback_tid, ist_werte, previous)
        meldungen.append(msg)
        log(logpfad, [msg])
        print(msg)
        if a.report:
            schreibe_bericht(a.report, reg_pfad, care, pending_pfad, app_laeuft, "rollback", meldungen)
        return 0

    pend = lade(pending_pfad, {"pending": []})
    if pend is None or not isinstance(pend, dict) or "pending" not in pend or not isinstance(pend.get("pending"), list):
        print("FEHLER: %s ist kein gueltiges JSON oder unerwartetes Format (muss JSON-Objekt mit 'pending'-Liste sein) - nichts geaendert." % pending_pfad)
        log(logpfad, ["FEHLER: pending-tasks.json ist kein gueltiges JSON oder unerwartetes Format - nichts geaendert."])
        return 1
    wuensche = pend["pending"]

    if a.status:
        print("Registry:         %s" % reg_pfad)
        print("Offene Wuensche:  %d" % len(wuensche))
        for w in wuensche:
            if isinstance(w, dict):
                print("  - [%s] %s %s (von %s)" % (w.get("op", "set"), w.get("taskId"),
                                                   w.get("fields"), w.get("requestedBy")))
            else:
                print("  - [ungueltig] Kein JSON-Objekt")
        print("Desktop-App:      %s" % ("laeuft" if app_laeuft else "geschlossen"))
        return 0

    if not wuensche:
        print("Keine offenen Wuensche.")
        if a.report:
            schreibe_bericht(a.report, reg_pfad, care, pending_pfad, app_laeuft, "no pending", ["Keine offenen Wuensche."])
        return 0

    if not a.ignore_app_state and app_laeuft:
        print("Desktop-App laeuft - nichts geaendert (%d Wuensche warten)." % len(wuensche))
        if a.report:
            schreibe_bericht(a.report, reg_pfad, care, pending_pfad, app_laeuft, "app running", ["Desktop-App laeuft - Execution pausiert."])
        return 0

    meldungen, offen, erledigt = [], [], []
    for w in wuensche:
        if not isinstance(w, dict):
            meldungen.append("ABGELEHNT: Ungueltiger Wunsch-Eintrag (kein JSON-Objekt)")
            continue
        op = w.get("op", "set")
        wer = w.get("requestedBy", "?")

        if op not in ("set", "create"):
            meldungen.append("ABGELEHNT (%s): unbekannte Operation '%s' - erlaubt sind 'set' "
                             "und 'create'" % (wer, op))
            continue

        if ist_fuer_fremden_host(w):
            meldungen.append("UEBERGANGEN (%s): Wunsch gehoert Host '%s', hier laeuft '%s' - "
                             "bleibt fuer den zustaendigen Host stehen"
                             % (wer, w.get("host"), LOKALER_HOST or "?"))
            offen.append(w)
            continue

        pruefer = pruefe_set if op == "set" else pruefe_create
        ok, meldung = (pruefer(w, nach_id) if op == "set"
                       else pruefer(w, nach_id, scheduled_dir))
        if not ok:
            meldungen.append(meldung)
            if ist_fremder_host(w, nach_id):
                offen.append(w)   # anderer Host zustaendig - NICHT verwerfen
            continue

        tid, felder = w["taskId"], w.get("fields") or {}

        if op == "set":
            eintrag = nach_id[tid]
            vorher = {k: eintrag.get(k) for k in felder}
            if vorher == felder:
                meldungen.append("UEBERSPRUNGEN (%s): '%s' steht bereits auf dem gewuenschten "
                                 "Wert" % (wer, tid))
                continue
            if a.dry_run:
                meldungen.append("DRY-RUN set %s: %s -> %s" % (tid, vorher, felder))
                offen.append(w)
                continue
            eintrag.update(felder)
            w["previousValues"] = vorher   # Gedaechtnis fuer Rollback
            meldungen.append("ANGEWENDET (%s): %s %s -> %s%s"
                             % (wer, tid, vorher, felder,
                                (" [%s]" % w["reason"]) if w.get("reason") else ""))
        else:
            if a.dry_run:
                meldungen.append("DRY-RUN create %s: %s" % (tid, felder))
                offen.append(w)
                continue
            skill_pfad = schreibe_skill_datei(scheduled_dir, tid, w)
            eintrag = {
                "id": tid,
                "enabled": felder.get("enabled", True),
                "filePath": skill_pfad,
                "createdAt": int(time.time() * 1000),
                "cronExpression": felder["cronExpression"],
                "userSelectedFolders": felder.get("userSelectedFolders", []),
                "permissionMode": felder.get("permissionMode", "auto"),
                "disableJitter": felder.get("disableJitter", False),
            }
            if felder.get("model"):
                eintrag["model"] = felder["model"]
            reg["scheduledTasks"].append(eintrag)
            nach_id[tid] = eintrag
            w["previousValues"] = None
            meldungen.append("ANGELEGT (%s): %s (%s, Auftragstext %s)%s"
                             % (wer, tid, felder["cronExpression"], skill_pfad,
                                (" [%s]" % w["reason"]) if w.get("reason") else ""))

        w["appliedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        erledigt.append(w)

    if erledigt:
        shutil.copyfile(reg_pfad, reg_pfad + ".backup-" + time.strftime("%Y%m%d-%H%M%S"))
        schreibe(reg_pfad, reg)

        kontrolle = lade(reg_pfad, {}) or {}
        k_nach_id = {t.get("id"): t for t in kontrolle.get("scheduledTasks", []) if isinstance(t, dict) and isinstance(t.get("id"), str)}
        for w in erledigt:
            ist = k_nach_id.get(w["taskId"])
            if ist is None:
                meldungen.append("WARNUNG: '%s' nach dem Schreiben nicht auffindbar" % w["taskId"])
                continue
            abweichung = {k: ist.get(k) for k, v in (w.get("fields") or {}).items()
                          if ist.get(k) != v}
            if abweichung:
                meldungen.append("WARNUNG: Aenderung an '%s' nicht bestaendig (gelesen: %s)"
                                 % (w["taskId"], abweichung))

        hist = lade(applied_pfad, {"applied": []}) or {"applied": []}
        if not isinstance(hist, dict) or "applied" not in hist or not isinstance(hist.get("applied"), list):
            hist = {"applied": []}
        hist.setdefault("applied", []).extend(erledigt)
        schreibe(applied_pfad, hist)

    if not a.dry_run:
        schreibe(pending_pfad, {"pending": offen})

    log(logpfad, meldungen)
    for m in meldungen:
        print(m)

    if a.report:
        schreibe_bericht(a.report, reg_pfad, care, pending_pfad, app_laeuft, "dry-run" if a.dry_run else "normal", meldungen)

    if erledigt:
        print("\nHinweis: Die App liest die Registry beim Start. Neu angelegte oder geaenderte "
              "Aufgaben erscheinen erst nach dem naechsten Start der Desktop-App.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
