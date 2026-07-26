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
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    tmp = pfad + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=2, ensure_ascii=False)
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


def pruefe_set(w, nach_id):
    tid = w.get("taskId")
    felder = w.get("fields") or {}
    wer = w.get("requestedBy", "?")

    if not tid or not isinstance(felder, dict) or not felder:
        return False, "ABGELEHNT (%s): Wunsch ohne taskId oder ohne fields" % wer
    if tid not in nach_id:
        return False, "ABGELEHNT (%s): Aufgabe '%s' existiert nicht in der Registry" % (wer, tid)

    unerlaubt = set(felder) - ERLAUBTE_FELDER
    if unerlaubt:
        return False, "ABGELEHNT (%s/%s): unerlaubte Felder %s" % (wer, tid, sorted(unerlaubt))

    if SELBSTSCHUTZ_PREFIX and tid.startswith(SELBSTSCHUTZ_PREFIX) and felder.get("enabled") is False:
        return False, ("ABGELEHNT (%s): '%s' ist eine Pflegeaufgabe und darf nicht deaktiviert "
                       "werden (Selbstschutz)" % (wer, tid))
    return True, None


def pruefe_create(w, nach_id, scheduled_dir):
    tid = w.get("taskId")
    wer = w.get("requestedBy", "?")
    felder = w.get("fields") or {}

    if not tid or not SLUG_RE.match(tid):
        return False, ("ABGELEHNT (%s): '%s' ist kein gueltiger Slug (klein, a-z 0-9 -)"
                       % (wer, tid))
    if tid in nach_id:
        return False, "ABGELEHNT (%s): Aufgabe '%s' existiert bereits - nutze 'set'" % (wer, tid)

    unerlaubt = set(felder) - ERLAUBTE_FELDER
    if unerlaubt:
        return False, "ABGELEHNT (%s/%s): unerlaubte Felder %s" % (wer, tid, sorted(unerlaubt))

    # Ohne Zeitplan wird die Aufgabe angelegt, laeuft aber nie und taucht in der
    # Liste der App nicht auf. Das ist erfahrungsgemaess der haeufigste Fehler.
    if not felder.get("cronExpression"):
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
    """Legt <Scheduled>/<slug>/SKILL.md an. Gibt den Pfad zurueck.

    Eine bereits vorhandene Datei wird NICHT ueberschrieben - sonst ginge ein von Hand
    gepflegter Auftragstext verloren.
    """
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


def main():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--status", action="store_true")
    p.add_argument("--paths", action="store_true", help="gefundene Pfade zeigen")
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

    pend = lade(pending_pfad, {"pending": []})
    if pend is None:
        print("FEHLER: %s ist kein gueltiges JSON - nichts geaendert." % pending_pfad)
        log(logpfad, ["FEHLER: pending-tasks.json ist kein gueltiges JSON - nichts geaendert."])
        return 1
    wuensche = pend.get("pending") or []

    if a.status:
        print("Registry:         %s" % reg_pfad)
        print("Offene Wuensche:  %d" % len(wuensche))
        for w in wuensche:
            print("  - [%s] %s %s (von %s)" % (w.get("op", "set"), w.get("taskId"),
                                               w.get("fields"), w.get("requestedBy")))
        if not a.ignore_app_state:
            print("Desktop-App:      %s" % ("laeuft" if pfade.app_laeuft() else "geschlossen"))
        return 0

    if not wuensche:
        print("Keine offenen Wuensche.")
        return 0

    if not a.ignore_app_state and pfade.app_laeuft():
        print("Desktop-App laeuft - nichts geaendert (%d Wuensche warten)." % len(wuensche))
        return 0

    reg = lade(reg_pfad, None)
    if not reg or "scheduledTasks" not in reg:
        print("FEHLER: Registry unlesbar oder unerwartetes Format: %s" % reg_pfad)
        log(logpfad, ["FEHLER: Registry unlesbar: %s" % reg_pfad])
        return 1
    nach_id = {t.get("id"): t for t in reg["scheduledTasks"]}

    meldungen, offen, erledigt = [], [], []
    for w in wuensche:
        op = w.get("op", "set")
        wer = w.get("requestedBy", "?")

        if op not in ("set", "create"):
            meldungen.append("ABGELEHNT (%s): unbekannte Operation '%s' - erlaubt sind 'set' "
                             "und 'create'" % (wer, op))
            continue

        pruefer = pruefe_set if op == "set" else pruefe_create
        ok, meldung = (pruefer(w, nach_id) if op == "set"
                       else pruefer(w, nach_id, scheduled_dir))
        if not ok:
            meldungen.append(meldung)      # abgelehnt: mit Grund protokolliert, nicht still
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
            w["previousValues"] = None     # es gab keinen Vorzustand
            meldungen.append("ANGELEGT (%s): %s (%s, Auftragstext %s)%s"
                             % (wer, tid, felder["cronExpression"], skill_pfad,
                                (" [%s]" % w["reason"]) if w.get("reason") else ""))

        w["appliedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        erledigt.append(w)

    if erledigt:
        shutil.copyfile(reg_pfad, reg_pfad + ".backup-" + time.strftime("%Y%m%d-%H%M%S"))
        schreibe(reg_pfad, reg)

        # Verifikation: erneut lesen und vergleichen. Ohne diesen Schritt wuerde ein
        # Rueckschreiben der App unbemerkt bleiben.
        kontrolle = lade(reg_pfad, {}) or {}
        k_nach_id = {t.get("id"): t for t in kontrolle.get("scheduledTasks", [])}
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
        hist.setdefault("applied", []).extend(erledigt)
        schreibe(applied_pfad, hist)

    if not a.dry_run:
        schreibe(pending_pfad, {"pending": offen})

    log(logpfad, meldungen)
    for m in meldungen:
        print(m)
    if erledigt:
        print("\nHinweis: Die App liest die Registry beim Start. Neu angelegte oder geaenderte "
              "Aufgaben erscheinen erst nach dem naechsten Start der Desktop-App.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
