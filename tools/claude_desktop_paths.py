# -*- coding: utf-8 -*-
"""claude_desktop_paths.py - Auffinden der Claude-Desktop-Ablagen, ohne zu raten.

Die Desktop-App legt zwei Dinge getrennt ab:

  1. REGISTRY  - die Aufgabenliste mit Zeitplaenen:
                 Windows: %APPDATA%\\Claude\\local-agent-mode-sessions\\<session>\\<account>\\scheduled-tasks.json
                 macOS:   ~/Library/Application Support/Claude/local-agent-mode-sessions/<session>/<account>/scheduled-tasks.json
  2. AUFTRAGSTEXTE - ein Ordner je Aufgabe:
                 <Dokumente>/Claude/Scheduled/<slug>/SKILL.md

Beides zusammen ergibt erst eine lauffaehige Aufgabe. Fehlt der Registry-Eintrag,
existiert der Ordner zwar, die Aufgabe laeuft aber nie.

WARUM DIESES MODUL
Der Dokumente-Ordner ist NICHT verlaesslich "%USERPROFILE%\\Documents". Wird er nach
OneDrive umgeleitet (Known-Folder-Move), zeigt der Shell-Ordner "Personal" woanders hin.
Ein hart verdrahteter Pfad findet die Aufgaben dann nicht - deshalb wird er auf Windows
aus der Registry gelesen. Die GUIDs im Registry-Pfad wechseln ebenfalls; darum wird
dort gesucht statt geraten.

Alle Funktionen geben None zurueck, wenn nichts gefunden wurde - der Aufrufer
entscheidet, ob das ein Fehler ist.
"""
import glob
import os
import subprocess
import sys

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

APP_DIR_NAME = "Claude"
SCHEDULED_DIR_NAME = "Scheduled"
CARE_DIR_NAME = "_care"
REGISTRY_FILE = "scheduled-tasks.json"
SESSIONS_DIR = "local-agent-mode-sessions"


def ist_windows():
    return sys.platform.startswith("win")


def ist_macos():
    return sys.platform == "darwin"


def dokumente_verzeichnis():
    """Der echte Dokumente-Ordner.

    Windows: aus dem Shell-Ordner "Personal" (beruecksichtigt OneDrive-Umleitung).
    Sonst:   ~/Documents.
    """
    if ist_windows():
        try:
            import winreg
            schluessel = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, schluessel) as k:
                roh, _ = winreg.QueryValueEx(k, "Personal")
            pfad = os.path.expandvars(roh)
            if pfad and os.path.isdir(pfad):
                return pfad
        except Exception:
            pass  # Fallback unten
    return os.path.join(os.path.expanduser("~"), "Documents")


def scheduled_verzeichnis(basis=None):
    """<Dokumente>/Claude/Scheduled - Heimat der Auftragstexte."""
    return os.path.join(basis or dokumente_verzeichnis(), APP_DIR_NAME, SCHEDULED_DIR_NAME)


def care_verzeichnis(basis=None):
    """Arbeitsordner dieses Moduls (Wunschliste, Historie, Log)."""
    return os.path.join(scheduled_verzeichnis(basis), CARE_DIR_NAME)


def _app_daten_wurzeln():
    """Kandidaten fuer den App-Datenordner, je Plattform."""
    heim = os.path.expanduser("~")
    if ist_windows():
        appdata = os.environ.get("APPDATA") or os.path.join(heim, "AppData", "Roaming")
        return [os.path.join(appdata, APP_DIR_NAME)]
    if ist_macos():
        return [os.path.join(heim, "Library", "Application Support", APP_DIR_NAME)]
    # Linux: keine offizielle Desktop-App bekannt; die ueblichen Orte werden trotzdem
    # geprueft, damit inoffizielle Builds nicht kuenstlich ausgeschlossen sind.
    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(heim, ".config")
    return [os.path.join(xdg, APP_DIR_NAME), os.path.join(heim, ".claude-desktop")]


def registry_pfad():
    """Pfad zur scheduled-tasks.json - die zuletzt geschriebene gewinnt.

    Session- und Account-GUID im Pfad wechseln, deshalb wird gesucht statt verdrahtet.
    """
    treffer = []
    for wurzel in _app_daten_wurzeln():
        treffer.extend(glob.glob(os.path.join(wurzel, SESSIONS_DIR, "*", "*", REGISTRY_FILE)))
    if not treffer:
        return None
    treffer.sort(key=os.path.getmtime, reverse=True)
    return treffer[0]


def app_laeuft():
    """True, wenn die Claude-DESKTOP-App laeuft.

    Wichtig: Die Claude-Code-CLI heisst auf Windows ebenfalls claude.exe. Ein reiner
    Namensfilter loest deshalb Fehlalarm aus - es wird zusaetzlich auf den
    Installationspfad der Store-App (WindowsApps) gefiltert.

    Laesst sich der Zustand nicht ermitteln, gilt bewusst "laeuft": lieber einen Lauf
    auslassen als in eine offene App hineinschreiben.
    """
    try:
        if ist_windows():
            ps = ("Get-CimInstance Win32_Process -Filter \"Name='Claude.exe'\" | "
                  "Where-Object { $_.ExecutablePath -like '*WindowsApps*' } | "
                  "Measure-Object | Select-Object -ExpandProperty Count")
            out = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                capture_output=True, text=True, timeout=60, creationflags=NO_WINDOW,
            )
            if out.returncode != 0:
                return True
            return int((out.stdout or "0").strip() or 0) > 0

        if ist_macos():
            # -x = exakter Prozessname, damit "claude" (CLI) nicht mitzaehlt.
            out = subprocess.run(["pgrep", "-x", "Claude"],
                                 capture_output=True, text=True, timeout=60)
            return out.returncode == 0

        out = subprocess.run(["pgrep", "-x", "claude-desktop"],
                             capture_output=True, text=True, timeout=60)
        return out.returncode == 0
    except Exception:
        return True


def diagnose():
    """Menschenlesbarer Kurzbericht - erste Anlaufstelle bei 'findet nichts'."""
    zeilen = [
        "Plattform:        %s" % sys.platform,
        "Dokumente:        %s" % dokumente_verzeichnis(),
        "Scheduled:        %s%s" % (scheduled_verzeichnis(),
                                    "" if os.path.isdir(scheduled_verzeichnis()) else "   (fehlt)"),
        "_care:            %s%s" % (care_verzeichnis(),
                                    "" if os.path.isdir(care_verzeichnis()) else "   (wird bei Bedarf angelegt)"),
        "Registry:         %s" % (registry_pfad() or "NICHT GEFUNDEN"),
        "Desktop-App:      %s" % ("laeuft" if app_laeuft() else "geschlossen"),
    ]
    return "\n".join(zeilen)


if __name__ == "__main__":
    print(diagnose())
