# Roadmap

## Stand

Windows ist die einzige verifizierte Plattform. Alle Pfade, die App-Erkennung und der
fensterlose Merger-Task wurden dort gegen eine echte Installation entwickelt.

Die Plattformabhängigkeiten sind bereits in **einer** Datei gebündelt
(`tools/claude_desktop_paths.py`) — Merger und CLI kennen keine Pfade mehr selbst. Der
Portierungsaufwand liegt damit fast vollständig in dieser einen Datei plus dem Auslöser.

---

## Phase 1 — macOS

Die Desktop-App gibt es für macOS; die Ablagen dürften den bekannten Konventionen folgen.
`claude_desktop_paths.py` enthält dafür bereits Kandidatenpfade — **ungetestet**.

| Punkt | Stand |
|---|---|
| Aufgabenliste unter `~/Library/Application Support/Claude/local-agent-mode-sessions/*/*/scheduled-tasks.json` | Annahme, an echter Installation zu prüfen |
| Auftragstexte unter `~/Documents/Claude/Scheduled/<slug>/SKILL.md` | Annahme, zu prüfen |
| App-Erkennung via `pgrep -x Claude` | implementiert, ungetestet |
| Auslöser statt Windows-Task: **launchd**-Agent (`~/Library/LaunchAgents/*.plist`, `StartInterval`) | offen |
| Fensterlos-Thematik entfällt (launchd startet ohne Terminal) | — |

**Erster Schritt:** `python tools/apply_pending_tasks.py --paths` auf einem Mac mit
installierter App ausführen. Die Ausgabe beantwortet die ersten drei Punkte auf einmal.

**Zu klären, bevor Aufwand entsteht:** Ob die App auf macOS überhaupt dieselbe
Speicher-Rückschreib-Eigenschaft hat. Trifft sie dort nicht zu, ist der ganze
Wunsch-Umweg auf macOS unnötig — dann genügt direktes Schreiben, und das Modul reduziert
sich auf Pfadauflösung plus Validierung.

## Phase 2 — Linux

**Ausgangslage (GitHub-Recherche 2026-07-26):** Eine offizielle Linux-App ist nicht
bekannt. Es existieren jedoch mehrere Community-Repackages des Windows-Builds
(z. B. `aaddrick/claude-desktop-debian`, `k3d3/claude-desktop-linux-flake`). Der Befund
ist Websuche-Niveau und ersetzt keine Prüfung an einer echten Installation.

Daraus folgt:

- **Nicht blind unterstützen.** Ein Repackage kann Ablagen an beliebige Orte legen; die
  Kandidatenpfade in `_app_daten_wurzeln()` (`$XDG_CONFIG_HOME/Claude`,
  `~/.claude-desktop`) sind Vermutungen und müssen gegen die jeweilige Installation
  ersetzt statt geraten werden.
- **Erst messen, dann bauen:** `--paths` auf dem Zielsystem ausführen. Findet es die
  Aufgabenliste nicht, ist der Rest der Phase gegenstandslos.
- **Offen ist auch, ob geplante Aufgaben in diesen Builds überhaupt funktionieren.** Ohne
  das ist ein Merger dort sinnlos.
- Auslöser bei Machbarkeit: systemd-User-Timer oder cron.

Fazit: Phase bleibt **bedingt** — nicht einplanen, bevor jemand mit einem solchen Build
die drei Punkte oben beantwortet hat.

## Phase 3 — Verbreitung und Sprache

| Punkt | Warum |
|---|---|
| Englische Fassung von README und Prompts | Aktuell durchgehend deutsch; für Veröffentlichung erste Wahl |
| Testsuite gegen eine Registry-**Kopie** | `--registry` + `--care-dir` + `--ignore-app-state` sind dafür vorhanden; die Produktivdaten dürfen ein Test nie anfassen |
| Rollback-Befehl | `applied-tasks.json` enthält mit `previousValues` bereits alles Nötige; es fehlt nur die Bedienung |
| Trockenlauf-Bericht als Datei | Für Läufe ohne Konsole am Bildschirm |

---

## Bewusst nicht geplant

- **Löschen von Aufgaben.** Bleibt der App vorbehalten; ein gelöschter Auftragstext ist
  nicht wiederherstellbar.
- **GUI.** Die App hat eine; dieses Modul ist der Weg für Agenten und Skripte.
- **Schreiben in laufende App erzwingen.** Es gibt keinen sicheren Weg dorthin — die
  Verzögerung ist die Lösung, nicht das Problem.
