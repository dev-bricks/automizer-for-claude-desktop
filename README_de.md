# Automizer for Claude Desktop (Deutsch)

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

**Geplante Aufgaben der Claude-Desktop-App zuverlässig ändern und anlegen — aus der App heraus, von außen, oder bei geschlossener App.**

Sprache: [English](README.md) | **Deutsch**

> [!NOTE]
> **Maschinenlesbarer Kontext:** Eine kompakte Projektübersicht für LLM-Agenten ist unter [`llms.txt`](llms.txt) verfügbar.

> [!IMPORTANT]
> **Inoffizielles Community-Werkzeug.** Dieses Projekt ist ein unabhängiges Community-Tool und steht in keiner Verbindung zu Anthropic. Es wird von Anthropic weder herausgegeben noch unterstützt oder geprüft. „Claude" und „Claude Desktop" sind Bezeichnungen von Anthropic und werden hier ausschließlich beschreibend verwendet.
>
> Es liest und schreibt lokale Dateien, die die Desktop-App anlegt. Deren Format ist nicht dokumentiert und kann sich mit jeder Version ändern. Vor jedem Schreiben wird eine Sicherung angelegt. Nutzung auf eigene Verantwortung.

---

## Schnellnavigation

- [Architektur & Ablauf](#architektur--ablauf)
- [End-to-End Lebenszyklus](#end-to-end-lebenszyklus)
- [Das Problem](#das-problem)
- [Die Lösung](#die-lösung)
- [Kernfähigkeiten & Sicherheitsinvarianten](#kernfähigkeiten--sicherheitsinvarianten)
- [Die drei Betriebsarten](#die-drei-betriebsarten)
- [Installation & Einrichtung](#installation--einrichtung)
- [Fensterlose Hintergrund-Ausführung](#warum-ein-vbs-wrapper)
- [Werkzeuge im Überblick](#werkzeuge-im-überblick)
- [Sicherheitsmerkmale & Schutzfunktionen](#was-das-werkzeug-bewusst-nicht-tut--sicherheitsgarantien)
- [Self-Administration-Skill](#optional-der-self-administration-skill)
- [Begriffe](#begriffe)
- [Daten und Datenschutz](#daten-und-datenschutz)
- [Geschwister-Werkzeuge & Ökosystem](#geschwister-werkzeuge--ökosystem)
- [Sicherheitsrichtlinie & Schwachstellen melden](#sicherheitsrichtlinie--schwachstellen-melden)
- [Lizenz und Herkunft](#lizenz-und-herkunft)

---

## Architektur & Ablauf

```mermaid
flowchart TD
    subgraph AgentOrUser ["Nutzer / Agenten-Anfrage"]
        A["Aufgabe ändern oder anlegen"] --> B["queue_request.py"]
    end

    subgraph CareQueue ["Pending-Queue Schicht"]
        B --> C["_care/pending/pending-tasks.json"]
    end

    subgraph BackgroundMerger ["Hintergrund-Merger (Scheduled Task)"]
        D["apply_pending_tasks.py / VBS Wrapper"] --> E{"Läuft Claude Desktop?"}
        C -. Liest Ausstehende Wünsche .-> D
        E -- "Ja (Prozess aktiv)" --> F["Ausführung aufschieben"]
        E -- "Nein (App geschlossen)" --> G["Registry sichern & Skill-Ordner anlegen"]
        G --> H["scheduled-tasks.json atomar aktualisieren"]
        H --> I["Protokoll in _care/history/applied-tasks.json"]
    end

    classDef primary fill:#2563eb,stroke:#1d4ed8,color:#fff;
    classDef success fill:#16a34a,stroke:#15803d,color:#fff;
    classDef warning fill:#d97706,stroke:#b45309,color:#fff;
    class A,B primary;
    class G,H,I success;
    class E,F warning;
```

---

## End-to-End Lebenszyklus

```mermaid
sequenceDiagram
    autonumber
    actor Agent as Nutzer / Agent
    participant QR as queue_request.py
    participant PQ as pending-tasks.json
    participant Engine as apply_pending_tasks.py
    participant Paths as claude_desktop_paths.py
    participant App as Claude Desktop Prozess
    participant Reg as scheduled-tasks.json
    participant Hist as applied-tasks.json

    Agent->>QR: Aufgaben-Änderung übermitteln (set / create)
    QR->>PQ: Schema validieren & Wunsch an Queue anhängen
    Note over Engine: Stündlicher Hintergrund-Task / Manueller Aufruf
    Engine->>PQ: Ausstehende Wünsche einlesen
    Engine->>Paths: Prozess- und App-Zustand abfragen
    Paths->>App: Programmpfad auf aktive App prüfen (*WindowsApps*)
    alt Claude Desktop ist aktiv
        Paths-->>Engine: Prozess aktiv
        Engine-->>Agent: Ausführung aufschieben (Wünsche bleiben erhalten)
    else Claude Desktop ist geschlossen
        Paths-->>Engine: Prozess inaktiv (Schreiben sicher)
        Engine->>Reg: Zeitgestempeltes Backup-Snapshot anlegen
        Engine->>Reg: Validierte Änderungen atomar zusammenführen
        Engine->>Reg: Rücklese- und Integritätsprüfung durchführen
        Engine->>Hist: Ausführungsbericht protokollieren
        Engine->>PQ: Verarbeitete Wünsche aus Queue entfernen
        Note over App: Nächster Start: Claude Desktop lädt neuen Zeitplan
    end
```

---

## Das Problem

Die Desktop-App verwaltet ihre geplanten Aufgaben in zwei getrennten Ablagen:

| Was | Wo | Beschreibung |
|---|---|---|
| **Auftragstext** | `<Dokumente>/Claude/Scheduled/<slug>/SKILL.md` | Enthält die auszuführende Prompts und Anweisungen |
| **Aufgabenliste (Registry)** | `<App-Daten>/Claude/local-agent-mode-sessions/<session>/<account>/scheduled-tasks.json` | Verwaltet Zeitpläne (`cronExpression`), Status (`enabled`) und Berechtigungen |

Beides zusammen ergibt erst eine laufende Aufgabe. Nur den Ordner anzulegen genügt nicht:
Ohne Eintrag in der Aufgabenliste — und ohne `cronExpression` darin — läuft die Aufgabe nie und erscheint nicht einmal in der Übersicht der App.

Der eigentliche Stolperstein liegt aber woanders: **Die App hält die Aufgabenliste im Speicher und schreibt sie beim Ende eines Laufs komplett neu.** Wer sie ändert, während die App läuft, verliert seine Änderung wieder — ohne Fehlermeldung. Das trifft Läufe innerhalb der App genauso wie Werkzeuge von außen. Man merkt es erst, wenn die Aufgabe weiterhin zur alten Zeit startet.

---

## Die Lösung

Wünsche werden vom Schreiben entkoppelt:

```
  Wunsch schreiben (jederzeit, von innen wie von außen)
            │
            ▼
   pending-tasks.json ──▶ apply_pending_tasks.py ──▶ Läuft die App?
                                                       │
                                       ja ─────────────┤  nichts tun, später erneut
                                                       │
                                      nein ────────────┴─▶ Backup → schreiben →
                                                            nachlesen → protokollieren
```

Ein Wunsch wirkt also **verzögert**. Das ist kein Mangel, sondern der Punkt: Er geht nicht verloren, und er wird nachprüfbar angewandt.

---

## Kernfähigkeiten & Sicherheitsinvarianten

| Fähigkeit | Technischer Mechanismus | Sicherheits- & Zuverlässigkeitsgarantie |
|---|---|---|
| **Pfadbasierte Prozesserkennung** | Prüft den vollständigen Programmpfad (`*WindowsApps*`) | Verhindert Verwechslung der Desktop-App mit der Claude Code CLI (`claude.exe`) |
| **Entkoppelte Staging-Queue** | Hängt Mutationswünsche atomar an `pending-tasks.json` an | Schreibt isolationsecht; gefahrlos aus laufenden Claude-Sitzungen nutzbar |
| **Automatische Pre-Write Snapshots** | Sichert `scheduled-tasks.json` vor jedem Schreiben zeitgestempelt | Kein Datenverlust; strukturierte Rollback-Möglichkeit bei fehlerhaften Eingaben |
| **Sofortiges Nachlesen & Prüfen** | Validiert JSON-Schema und Schlüssel unmittelbar nach Schreibvorgang | Garantiert Dateiintegrität, bevor Wünsche aus der Warteschlange gelöscht werden |
| **Strikte Positivliste (Whitelisting)** | Erlaubt nur definierte Schema-Felder (`cronExpression`, `enabled`, etc.) | Schützt interne Pfade und verhindert Einschleusen invalider Konfigurationswerte |
| **Integrierter Selbstschutz** | Blockiert Deaktivierung von Aufgaben mit `CDA_SELF_PROTECT_PREFIX` | Verhindert, dass autonome Agenten versehentlich Schutz- und Wartungsaufgaben abschalten |
| **Host-Isolierung** | Filtert Wünsche nach lokalem Rechnernamen | Sicherer Parallelbetrieb in Multi-Host-Setups über synchronisierte OneDrive-Ordner |
| **Zero-Egress & Standardbibliothek** | 100% Python-Standardbibliothek ohne externe Drittpakete | Vollständig offline; keine Netzwerkverbindungen, keine Telemetrie, kein Datenaustritt |

---

## Die drei Betriebsarten

| # | Lage | Was möglich ist | Prompt-Vorlage |
|---|---|---|---|
| 1 | LLM läuft **in** der App | Wunsch hinterlegen (verzögert) | [`prompts/01_in-der-app.md`](prompts/01_in-der-app.md) |
| 2 | Zugriff **von außen**, App läuft | Wunsch einreihen per CLI (verzögert) | [`prompts/02_von-aussen-app-laeuft.md`](prompts/02_von-aussen-app-laeuft.md) |
| 3 | App ist **geschlossen** | direkt anwenden (sofort) | [`prompts/03_app-geschlossen.md`](prompts/03_app-geschlossen.md) |

Die Prompt-Dateien sind zum Kopieren gedacht — in den Auftragstext einer Aufgabe (1) oder in den Kontext eines externen Agenten (2, 3).

---

## Installation & Einrichtung

Voraussetzung: **Python 3.8+**. Keine Abhängigkeiten außerhalb der Standardbibliothek.

```bash
# 1. Pfade prüfen — findet das Werkzeug die Ablagen dieser Installation?
python tools/apply_pending_tasks.py --paths

# 2. Merger als stündlichen, fensterlosen Windows-Task registrieren (kein Admin nötig)
powershell -ExecutionPolicy Bypass -File tools/install_merger_task.ps1

# 3. Abnahme
#    a) bei geöffneter App auslösen -> es darf sich nichts ändern
#    b) App schließen, erneut auslösen -> Wunsch wird angewandt
#    c) in beiden Fällen darf kein Fenster aufblitzen
```

Ohne Schritt 2 funktioniert alles weiterhin — die Wünsche werden dann nur nicht von selbst angewandt, sondern erst beim manuellen Aufruf von `python tools/apply_pending_tasks.py`.

Den Installer **per `-File` aufrufen**, nicht den Inhalt in eine Konsole einfügen: Sonst ist `$PSScriptRoot` leer, der Task wird mit leerem Argument registriert und läuft stündlich ins Nichts.

### Warum ein VBS-Wrapper

„Fensterlos" heißt hier: versteckte Konsole, nicht gar keine. Ein nacktes `pythonw` genügt nicht, sobald Unterprozesse starten — die allozieren sich sonst eigene, sichtbare Fenster. Der Wrapper startet über `WScript.Shell.Run(cmd, 0, False)`, im Python-Teil sorgt `CREATE_NO_WINDOW` für den Rest.

---

## Werkzeuge im Überblick

| Datei | Zweck |
|---|---|
| [`tools/claude_desktop_paths.py`](tools/claude_desktop_paths.py) | Findet Dokumente-Ordner, Aufgabenliste und App-Zustand — ohne zu raten |
| [`tools/queue_request.py`](tools/queue_request.py) | Wunsch einreihen (`set` / `create`), ohne JSON von Hand |
| [`tools/apply_pending_tasks.py`](tools/apply_pending_tasks.py) | Der Merger: prüft, schreibt, verifiziert, protokolliert |
| [`tools/install_merger_task.ps1`](tools/install_merger_task.ps1) | Registriert den stündlichen Windows-Task |
| [`tools/run_apply_pending_hidden.vbs`](tools/run_apply_pending_hidden.vbs) | Fensterloser Start des Mergers |

### Warum Pfade nicht geraten werden

Der Dokumente-Ordner ist **nicht** verlässlich `%USERPROFILE%\Documents`. Wird er nach OneDrive umgeleitet (Known-Folder-Move), zeigt der Shell-Ordner „Personal" woanders hin — ein fest verdrahteter Pfad findet die Aufgaben dann nicht. Deshalb wird er aus der Registry gelesen. Die GUIDs im Pfad der Aufgabenliste wechseln ebenfalls; dort wird gesucht und die zuletzt geschriebene Datei genommen.

---

## Was das Werkzeug bewusst nicht tut & Sicherheitsgarantien

- **Löschen.** Aufgaben zu entfernen bleibt dem Menschen in der App. Ein versehentlich gelöschter Auftragstext ist nicht wiederherstellbar.
- **`filePath` ändern.** Sonst ließe sich ein Eintrag auf eine beliebige fremde Datei umbiegen. Das Feld steht nicht auf der Whitelist.
- **Zeitpläne erfinden.** Wo keiner gesetzt war, wird gemeldet statt geraten.
- **Im Zweifel schreiben.** Lässt sich der App-Zustand nicht ermitteln, gilt „läuft" — lieber ein Lauf ausgelassen als in eine offene App hineingeschrieben.

### Sicherheitsmerkmale

1. **App-Erkennung über den Pfad**, nicht über den Prozessnamen. Auf Windows heißt die Claude-Code-CLI ebenfalls `claude.exe`; ein reiner Namensfilter löst Fehlalarm aus.
2. **Feld-Whitelist:** nur `cronExpression`, `enabled`, `model`, `userSelectedFolders`, `permissionMode`, `disableJitter`.
3. **Selbstschutz:** Ein Wunsch, der eine Pflege-Aufgabe deaktiviert, wird abgelehnt — sonst schaltet sich die Pflege selbst ab. Präfix über `CDA_SELF_PROTECT_PREFIX` einstellbar (leer = aus).
4. **Backup vor jedem Schreiben**, **Nachlesen danach** — Abweichungen werden als WARNUNG protokolliert.
5. **`previousValues`** in der Historie — ohne Vorzustand kein Rollback.
6. **Fail-Closed Cross-Host Schutz:** Wünsche anderer Geräte in Multi-Host OneDrive-Setups werden isoliert und nicht fehlerhaft überschrieben.
7. **Abgelehnte Wünsche verschwinden nicht still**, sondern mit Grund im Log.

---

## Optional: der Self-Administration-Skill

Dieses Repo liefert zwei Dinge, die unabhängig voneinander nutzbar sind:

**Die Mechanik** (`tools/`, `prompts/`) — Wünsche einreihen und sicher anwenden. Für sich allein nutzbar: Ein Mensch oder ein beliebiger Agent kann damit Aufgaben ändern und anlegen.

**Den Skill** ([`skill/self-administration-of-scheduled-tasks/`](skill/self-administration-of-scheduled-tasks/SKILL.md)) — eine Anleitung für ein LLM, wie es sich einen *selbstpflegenden* Kern geplanter Aufgaben einrichtet: fünf schmale Aufsichtsrollen mit je einer Stellschraube (Bestand, Auftragstexte, Frequenz, Kontingent, Systemabgleich), ein gemeinsames Gedächtnis und fertige Prompttexte. Der Skill setzt die Mechanik voraus; die Mechanik läuft auch ohne ihn.

---

## Begriffe

| Begriff | Bedeutung |
|---|---|
| **Slug** | Kurzname einer Aufgabe = Ordnername unter `Scheduled\` = `id` in der Aufgabenliste |
| **Wunsch** | Ein Eintrag in `pending-tasks.json`, noch nicht angewandt |
| **Merger** | `apply_pending_tasks.py` — wendet Wünsche an, wenn die App zu ist |
| **Registry** | Hier: die Aufgabenliste `scheduled-tasks.json` (nicht die Windows-Registry) |

---

## Daten und Datenschutz

Das Werkzeug arbeitet **ausschließlich lokal**. Es sendet nichts über das Netz — weder Telemetrie noch Inhalte — und benötigt keine Zugangsdaten.

Es liest und schreibt drei Dinge auf demselben Rechner: die Aufgabenliste der App, die Auftragstexte unter `Scheduled/` und seine eigenen Dateien unter `_care/`. Diese Dateien können beschreiben, welche Ordner eine Aufgabe lesen darf, und der Auftragstext kann beliebige eigene Inhalte enthalten.

Daraus folgt für den Betrieb: **`pending-tasks.json`, `applied-tasks.json` und Logdateien gehören nicht in ein Repository** — sie enthalten die Pfade und Absichten des jeweiligen Systems. Die mitgelieferte `.gitignore` schließt sie deshalb aus.

---

## Geschwister-Werkzeuge & Ökosystem

`automizer-for-claude-desktop` ist Teil der [`dev-bricks`](https://github.com/dev-bricks)-Suite unter dem [`open-bricks`](https://github.com/open-bricks)-Dach:

| Werkzeug | Organisation | Schwerpunkt & Kurzbeschreibung |
|---|---|---|
| [`safe-start-for-codex`](https://github.com/dev-bricks/safe-start-for-codex) | `dev-bricks` | Prozesswächter & Sicherheitsaufseher für autonome Programmier-Agenten |
| [`companion-for-agy`](https://github.com/dev-bricks/companion-for-agy) | `dev-bricks` | CLI-Begleiter und Sitzungskoordinator für Antigravity-Agenten |
| [`DevCenter`](https://github.com/dev-bricks/DevCenter) | `dev-bricks` | Zentrale Entwickler-Werkbank und Workspace-Orchestrierung |
| [`CodeBox`](https://github.com/dev-bricks/CodeBox) | `dev-bricks` | Lokaler Container für Code-Snippets und Entwicklungs-Assets |
| [`automation-master`](https://github.com/dev-bricks/automation-master) | `dev-bricks` | Einheitliche Multi-Agenten-Workflow-Planung und Orchestrierung |
| [`MethodenAnalyser`](https://github.com/dev-bricks/MethodenAnalyser) | `dev-bricks` | Statische Codeanalyse und Methodenextraktion |
| [`coma`](https://github.com/ellmos-ai/coma) | `ellmos-ai` | Kooperative Multi-Agenten-Koordination und sperrenfreie Protokolle |
| [`workflowhooker`](https://github.com/ellmos-ai/workflowhooker) | `ellmos-ai` | Deterministische Hook-Interzeption und Event-Lebenszyklussteuerung |
| [`memoryhooker`](https://github.com/ellmos-ai/memoryhooker) | `ellmos-ai` | Lokale episodische und semantische Speicherindizierung für Agenten |
| [`open-bricks`](https://github.com/open-bricks) | `open-bricks` | Dachorganisation und offene Standardspezifikationen |

---

## Sicherheitsrichtlinie & Schwachstellen melden

Ausführliche Richtlinien und Sicherheitsgarantien finden Sie in unserer [Sicherheitsrichtlinie (SECURITY.md)](SECURITY.md).

- **Sicherheitshinweise:** [GitHub Security Advisories](https://github.com/dev-bricks/automizer-for-claude-desktop/security/advisories)
- **Sicherheitskontakte:** [security@ellmos.ai](mailto:security@ellmos.ai) · [lukas@open-bricks.org](mailto:lukas@open-bricks.org) · [support@lukasgeiger.com](mailto:support@lukasgeiger.com)

---

## Lizenz und Herkunft

MIT — siehe [LICENSE](LICENSE). Sie erfasst alles in diesem Repository: Code, Prompttexte und Dokumentation.

