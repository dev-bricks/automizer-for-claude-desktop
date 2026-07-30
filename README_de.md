# Automizer for Claude Desktop (Deutsch)

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ecosystem: dev-bricks](https://img.shields.io/badge/Ecosystem-dev--bricks-blueviolet.svg)](https://github.com/dev-bricks)
[![Umbrella: open-bricks](https://img.shields.io/badge/Umbrella-open--bricks-indigo.svg)](https://github.com/open-bricks)
[![Pytest](https://img.shields.io/badge/Pytest-5%20passed-brightgreen.svg)](tests/test_automizer.py)
[![LLM Context](https://img.shields.io/badge/LLM%20Context-llms.txt-success.svg)](llms.txt)

**Geplante Aufgaben der Claude-Desktop-App zuverlässig ändern und anlegen — aus der App heraus, von außen, oder bei geschlossener App.**

[English](README.md) | Deutsch

> [!NOTE]
> **Maschinenlesbarer Kontext:** Eine kompakte Projektübersicht für LLM-Agenten ist unter [`llms.txt`](llms.txt) verfügbar.

> [!IMPORTANT]
> **Inoffizielles Werkzeug.** Dieses Projekt ist ein unabhängiges Community-Tool und steht in keiner Verbindung zu Anthropic. Es wird von Anthropic weder herausgegeben noch unterstützt oder geprüft.

---

## Architekturdialgramm & Ablauf

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

## Schnellstart

```bash
# Pfade verifizieren
python tools/apply_pending_tasks.py --paths

# Pytest Testsuite ausführen
pytest
```
