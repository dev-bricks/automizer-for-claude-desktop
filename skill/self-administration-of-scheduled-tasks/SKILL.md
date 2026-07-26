---
name: self-administration-of-scheduled-tasks
description: Anleitung, wie ein LLM sich einen selbstpflegenden Kern geplanter Aufgaben einrichtet — fünf Aufsichtsrollen, gemeinsames Gedächtnis, Wunschkanal statt Direktschreiben. Nutze sie, wenn geplante Aufgaben, Automationen oder Loop-Routinen aufgesetzt, unbeaufsichtigt betrieben oder auf ein anderes System bzw. einen anderen Anbieter portiert werden sollen — inklusive fertiger Prompttexte.
---

# Selbstverwaltung geplanter Aufgaben

Diese Anleitung richtet **fünf geplante Aufgaben** ein, die nichts anderes tun, als die
**übrigen** geplanten Aufgaben derselben App am Leben und in Form zu halten. Sie ist an ein LLM
gerichtet, das den Kern auf einem System aufsetzen oder auf einen anderen Anbieter portieren
soll. Die fertigen Prompttexte stehen in Abschnitt 6 und können nach Anpassung der Pfade direkt
übernommen werden.

## 1. Wozu das gut ist

Automationen sterben still. Ein Zeitplan fehlt, eine Ordnerfreigabe passt nicht mehr, ein Pfad
zeigt auf einen fremden Benutzernamen, das Kontingent ist erschöpft, ein Prompt ist seit einem
Umbau irreführend — und niemand merkt es, weil kein Mensch täglich Laufprotokolle liest. Der
Kern übernimmt genau diese Aufsicht.

**Der tragende Gedanke: getrennte Rollen mit je einer Stellschraube.** Nicht ein Allesprüfer,
sondern fünf schmale Aufgaben mit unterschiedlichen Laufzeiten. Jede fasst nur ihr eigenes Feld
an. So bleibt zuordenbar, welche Änderung welche Wirkung hatte — und keine Aufgabe kann sich
selbst in einer einzigen Fehlentscheidung abschalten.

| Rolle | Stellschraube | Frage, die sie beantwortet |
|---|---|---|
| `task-care` | Bestand, Freigaben, Pfade | Existiert alles, was existieren soll, und läuft es? |
| `text-improver` | Auftragstexte | Verstehen die Aufgaben ihren Auftrag? |
| `scheduler-tuner` | Frequenz, Aktivierung, Lastverteilung | Läuft es zur richtigen Zeit und oft genug? |
| `token-watcher` | Kontingent, Modellwahl | Reicht das Budget bis zum Fensterende? |
| `task-sync` | Abgleich mit anderen Systemen | Machen wir woanders dasselbe doppelt oder gar nicht? |

## 2. Vier Dinge herausfinden, bevor du irgendetwas baust

Rate keinen dieser Punkte. Jeder Fehler hier vergiftet den ganzen Kern.

1. **Wo liegt die Aufgaben-Registry?** Also die Datei oder Datenbank, in der Zeitplan,
   Aktivierung, Modell und Rechte stehen. Bei Claude Desktop:
   `%APPDATA%\Claude\local-agent-mode-sessions\<session>\<account>\scheduled-tasks.json`.
   Bei Codex und Antigravity: je Automation eine `automation.toml` unter
   `~/.codex/automations/<id>/` bzw. `~/.gemini/automations/<id>/`.
2. **Wo liegen die Auftragstexte?** Bei Claude Desktop `<Dokumente>\Claude\Scheduled\<slug>\SKILL.md`
   — und der Dokumente-Ordner ist auf vielen Systemen nach OneDrive umgeleitet. **Prüfe den
   tatsächlichen Pfad, nimm nicht den Standardpfad an.** Bei Codex/Antigravity steckt der Text
   als `prompt`-Feld in der TOML selbst.
3. **Wo liegen die Laufprotokolle?** Das ist die einzige belastbare Quelle für „hat gelaufen"
   und „hat etwas gebracht". Bei Claude Desktop die Dateien `local_*.json` im Ordner der
   Registry. **Ein Registry-Eintrag ist kein Beleg für einen Lauf** — das ist der häufigste
   Fehlschluss.
4. **Überlebt eine direkte Änderung an der Registry?** Prüfe das empirisch, bevor du dich darauf
   verlässt: Wert ändern, App normal weiterlaufen lassen, nach dem nächsten Lauf-Ende erneut
   lesen. Bei Claude Desktop lautet das Ergebnis **nein** — die App schreibt die Datei beim
   Lauf-Ende komplett aus ihrem Speicher neu und setzt jede Fremdänderung zurück. Deshalb
   Abschnitt 4.

## 3. Das gemeinsame Gedächtnis anlegen

Ohne geteiltes Gedächtnis prüfen fünf Aufgaben fünfmal dasselbe und widersprechen einander.
Lege neben den Aufgabenordnern ein `_care`-Verzeichnis an:

```
Scheduled/_care/
  CARE-LOG.md            Lauf-Log, neueste Einträge oben: Datum, Rolle, Befund,
                         Maßnahme, offene Punkte. Ab 300 Zeilen nach _archive/
                         auslagern und mit Kopfverweis neu beginnen.
  CARE-REGISTRY.md       Was dauerhaft gilt: getroffene Entscheidungen, belegte
                         Eigenheiten der Umgebung, Grundsätze. Kein Verlauf.
  DELETED-TASKS-LOG.md   Was der User bewusst entfernt hat — mit Grund.
                         Was hier steht, wird NIE wiederhergestellt.
  text-versions/         Kopie jedes Auftragstextes vor einer Änderung:
                         <slug>_<datum>.md. Das ist der Rollback.
  _archive/              Ausgelagerte Log-Teile.
  pending/               Der Wunschkanal, siehe Abschnitt 4.
  tools/                 Der Merger, siehe Abschnitt 4.
```

Regeln dazu, die in jeden Prompttext gehören:

- **Jeder Lauf schreibt einen CARE-LOG-Eintrag** — auch ein Lauf ohne Änderung. „Geprüft, nichts
  zu tun" ist ein Ergebnis und verhindert, dass der nächste Lauf dieselbe Prüfung wiederholt.
- **Vorzustand notieren, sonst gibt es kein Zurück.** Jede Änderung mit Ausgangswert **und**
  Rückstellbedingung („zurück auf X, sobald Y wieder gilt").
- **Höchstens eine Stellschraube pro Lauf und Rolle.** Sonst ist die Wirkung im Folgelauf nicht
  zuordenbar.

## 4. Wenn die Registry flüchtig ist: der Wunschkanal

Trifft Punkt 4 aus Abschnitt 2 zu — die App überschreibt Fremdänderungen —, dann darf **keine**
Aufgabe je selbst in die Registry schreiben. Stattdessen stellt sie einen Änderungswunsch, den
ein Prozess **außerhalb** der App anwendet, sobald die App geschlossen ist.

`_care/pending/pending-tasks.json`:

```json
{"pending": [
  {"op": "set",
   "taskId": "<slug>",
   "fields": {"cronExpression": "0 8 * * *"},
   "reason": "<warum, in einem Satz>",
   "requestedBy": "<slug der anfragenden Rolle>",
   "requestedAt": "<ISO-Zeit>"}
]}
```

- **Erlaubte Felder eng halten:** Zeitplan, Aktivierung, Modell, Ordnerfreigaben, Rechtemodus.
  Alles andere ablehnen.
- **Anlegen und Löschen von Aufgaben gehört NICHT in diesen Kanal.** Ein Merger, der Aufgaben
  erzeugen kann, ist ein Merger, der Aufgaben zerstören kann. Fehlt eine Aufgabe, wird das dem
  User gemeldet.
- **Der Merger schreibt den Vorzustand mit**, nach `applied-tasks.json`, und protokolliert jede
  Anwendung im CARE-LOG. Ohne diesen Vorzustand ist ein Rollback Ratearbeit.
- **Wünsche wirken verzögert.** Der Prompttext muss das ausdrücklich sagen, sonst trägt der
  nächste Lauf denselben Wunsch erneut ein, weil er ihn für verloren hält.
- **Der Merger braucht einen Auslöser außerhalb der App** — auf Windows ein Scheduled Task,
  fensterlos gestartet. **Ohne diesen Auslöser ist der ganze Kanal wirkungslos**, und das fällt
  erst auf, wenn Wünsche wochenlang liegen bleiben. Prüfe bei der Einrichtung, dass der Auslöser
  wirklich registriert ist, und lass jede Rolle im Folgelauf prüfen, ob ihr Wunsch angewendet
  wurde.

## 5. Selbstschutz — nicht verhandelbar

Diese drei Sätze gehören wörtlich in **jeden** der fünf Prompttexte:

- Aufgaben, deren Kennung mit dem Präfix des Pflegeverbunds beginnt (z. B. `claude-desktop-`),
  werden **nie** deaktiviert, gelöscht oder unter tägliche Frequenz gesetzt. Sonst schaltet sich
  die Aufsicht selbst ab und niemand merkt es.
- **Niemals einen Zeitplan erfinden**, wo der User keinen gesetzt hat — nur melden.
- **Keine Zugangsdaten, Tokens oder sensiblen Auftragsinhalte** in geteilte Ordner exportieren.

Ergänzend: **Fremde Systeme nur lesen.** In die Automationsordner einer anderen Entität wird nie
geschrieben; Abweichungen werden gemeldet.

## 6. Die fünf Prompttexte

Jeder Text besteht aus einem **gemeinsamen Rumpf** und einem **Rollenteil**. Setze beides
zusammen und ersetze die Platzhalter `<...>` durch die in Abschnitt 2 ermittelten Werte.

### 6.0 Gemeinsamer Rumpf — an den Anfang jedes der fünf Texte

```
VORBEREITUNG - SYSTEMREGELN ZUERST LESEN (nicht überspringen)
Diese App lädt die zentrale Regeldatei NICHT automatisch. Lies daher zu Beginn jedes Laufs:
1. <Pfad zur globalen Regeldatei> - die maßgebliche Regeldatei (Sprache, Faktentreue,
   Sperrsystem, Arbeitsweise).
2. <Pfad zur Ordner-/Pfadkonvention>.
FALLBACK: Ist (1) nicht lesbar, nimm <Spiegelpfad> und vermerke im Log, dass das Original
nicht erreichbar war. Der Spiegel kann älter sein; das Original hat Vorrang.

Besonders verbindlich: aktive Sperrdateien im Zielbereich zuerst lesen und befolgen; echte
Umlaute in allen deutschen Texten; keine erfundenen Angaben - im Zweifel prüfen oder melden.

GRUNDLAGEN
- Registry:        <Pfad>   (Felder: id, Zeitplan, enabled, filePath, Freigaben, Rechtemodus,
                             optional model. Laufzeitfelder pflegt die App.)
- Auftragstexte:   <Pfad>\<slug>\SKILL.md
- Laufprotokolle:  <Pfad>   - die einzige belastbare Quelle für Erfolgsbewertung.
- Gemeinsames Gedächtnis: _care\CARE-LOG.md und _care\CARE-REGISTRY.md. Jeder Lauf trägt dort
  Datum, Rolle, Befund, Maßnahme und offene Punkte ein - so weiß der nächste Lauf, was bereits
  entschieden wurde. Über 300 Zeilen nach _care\_archive\ auslagern.
- Lösch-Log: _care\DELETED-TASKS-LOG.md. Was dort mit Grund steht, wird NICHT wiederhergestellt.

SCHREIBREGEL - DIE REGISTRY NIE DIREKT ÄNDERN
Direkte Änderungen überleben nicht: Die App schreibt die Datei beim Lauf-Ende aus ihrem Speicher
neu. Stelle stattdessen einen Wunsch in _care\pending\pending-tasks.json (Format siehe unten),
ohne die Wünsche anderer Läufe zu entfernen. Erlaubte Felder: Zeitplan, enabled, model,
Ordnerfreigaben, Rechtemodus. Aufgaben ANLEGEN oder LÖSCHEN geht so NICHT - das meldest du dem
User. Ein Wunsch wirkt VERZÖGERT (erst bei geschlossener App): eintragen, im Folgelauf prüfen,
NICHT wiederholen. Nicht betroffen: Auftragstexte, _care-Dateien und Exporte.

SELBSTSCHUTZ (nicht verhandelbar)
- Aufgaben mit dem Präfix <präfix> nie deaktivieren, löschen oder unter tägliche Frequenz setzen.
- Niemals einen Zeitplan erfinden, wo der User keinen gesetzt hat - nur melden.
- Keine Zugangsdaten oder sensiblen Inhalte in geteilte Ordner.

MEMORY-REGEL: Schreibe vor der finalen Antwort einen kurzen Eintrag in _care\CARE-LOG.md -
was geprüft, was geändert, was offen ist. Deutsche Texte mit echten Umlauten.
```

### 6.1 Rollenteil `task-care` — Bestand und Hygiene

```
Pflege die geplanten Aufgaben dieser Instanz. Ändere nur, was eindeutig ist - alles andere wird
gemeldet, nicht geraten.

1) Registry und Auftragsordner beidseitig abgleichen: Eintrag ohne Auftragstext (tote filePath)
   und Ordner ohne Registry-Eintrag (unsichtbare Aufgabe, läuft nie).
2) Einträge ohne Zeitplan melden - sie laufen nie und erscheinen in keiner Liste.
3) Freigaben prüfen: Nennt der Auftragstext Pfade, die die Ordnerfreigaben nicht abdecken? Dann
   läuft die Aufgabe ins Leere. Geht der Pfad eindeutig aus dem Text hervor, als Wunsch
   einreichen; sonst melden.
4) Host-Pfade prüfen: Auftragstexte auf fremde Benutzerpfade absuchen (ein Pfad mit einem
   Benutzernamen, den es auf diesem Rechner nicht gibt, ist ein toter Pfad).
5) Lauf-Aktualität: letzten Lauf gegen den Zeitplan halten. Deutlich überfällige Aufgaben sind
   still gestorben - melden. Achte auf die Verwechslung von Anlegedatum und Laufdatum: eine
   Aufgabe, die jünger ist als ihr erster Termin, ist nicht defekt.
6) Lösch-Log lesen und pflegen; nichts wiederherstellen, was dort mit Grund steht.
7) Stand nach <geteilter Ordner> exportieren: je Aufgabe Kennung, Zeitplan, aktiv, Freigaben,
   letzter Lauf, Befunde.
```

### 6.2 Rollenteil `text-improver` — Qualität der Auftragstexte

```
Du bist die Qualitätskontrolle der Auftragstexte. Drei Phasen pro Lauf:

PHASE 1 - NACHSORGE: Lies im CARE-LOG, welche Texte du zuletzt geändert hast. Hat die Änderung
gewirkt? Wenn nein oder schlechter: nachziehen oder Rollback auf die Fassung in
_care\text-versions\. Lege vor JEDER Textänderung dort eine Kopie <slug>_<datum>.md an.

PHASE 2 - ANALYSE: Wähle GENAU EINE Aufgabe - bevorzugt die, deren Text am längsten nicht
geprüft wurde. Sieh dir ihre letzten Läufe im Laufprotokoll an. Lief sie reibungslos, lass den
Text unverändert.

PHASE 3 - URSACHE UND MASSNAHME. Prüfe bei Auffälligkeiten diese Hypothesen:
- h1 Modell passt nicht zur Aufgabenschwere -> Modell als Wunsch anpassen.
- h2 Prompttext missverständlich, veraltet oder irreführend -> präzisieren; falls nötig
     zusätzliche Wegweiser im Zielordner aufstellen.
- h3 Es fehlen Werkzeuge oder Berechtigungen -> Freigaben als Wunsch ergänzen und die nötigen
     Werkzeuge im Text ausdrücklich benennen. Der Textteil wirkt sofort, der Rechteteil verzögert.
- h4 Es fehlt Policy-Wissen -> Ursache des Nichtwissens klären, lokal nachtragen, Fundorte als
     Bootschritt in den Prompt aufnehmen.
- h5 Text ist nicht auf das Modell zugeschnitten (zu enge oder zu lose Führung) -> anpassen.
- h6 Andere Ursache -> als neue Hypothese in DIESEN Text aufnehmen.
- h7 Ursache unklar -> nichts raten. Befund melden, Aufgabe beobachten; im Zweifel Rechte enger
     setzen statt blind ändern.

Ändere pro Lauf höchstens einen Text, damit die Wirkung zuordenbar bleibt.
```

### 6.3 Rollenteil `scheduler-tuner` — Frequenz, Aktivierung, Last

```
Du stellst ein, WANN und OB Aufgaben laufen. Drei Felder pro Lauf:

A) FREQUENZ. Viel Arbeit bei hoher Priorität -> hochregeln. Wenig Arbeit bei niedriger
   Priorität -> herunterregeln. Die Priorität schätzt du aus der jüngsten tatsächlichen
   Nutzeraufmerksamkeit ab. Wie oft eine Automation läuft, ist KEIN Wichtigkeitssignal.

B) AKTIVIERUNG. Findet eine Aufgabe wiederholt keine Arbeit, prüfe ZUERST, ob das am Text liegt
   (dann übernimmt der Text-Improver) oder an echtem Arbeitsmangel. Nur bei echtem Arbeitsmangel
   deaktivieren und begründen. Reaktiviere pro Lauf HÖCHSTENS EINE deaktivierte Aufgabe
   testweise und entscheide beim nächsten Lauf, ob sie aktiv bleibt.

C) LASTVERTEILUNG. Verteile Startzeiten gleichmäßig über Tag und Woche. Mehrere Aufgaben zur
   selben Stunde konkurrieren um Rechenzeit, Kontingent und Dateizugriffe. Belegte Zeiten der
   anderen Systeme mitberücksichtigen.

Ändere pro Lauf wenige Stellschrauben, nicht alles auf einmal. Alle drei Felder änderst du
ausschließlich als Wunsch.
```

### 6.4 Rollenteil `token-watcher` — Kontingentaufsicht

```
Du wachst über das Nutzungskontingent.

MESSEN: Erhebe pro Lauf Verbrauch und Restkontingent, schreibe jeden Messpunkt fort, ordne die
Änderung zwischen zwei Messpunkten den dazwischen gelaufenen Aufgaben zu und aktualisiere ein
Übersichtsdokument.

BAUE DAS NICHT NEU, wenn es auf dem System schon ein Verbrauchs-Tracking gibt - prüfe zuerst,
ob du Schema und Auswertungslogik übernehmen kannst. Schreibe aber niemals in fremde Datenbanken
oder Berichte; lege eine eigene Datenhaltung an und halte dich nur ans gleiche Schema.

RECHNE DAS TEMPO AUS, nicht nur den Stand. Die entscheidende Zahl ist das Verhältnis von
beobachtetem zu budgetkonformem Verbrauch pro Tag und der daraus folgende Zeitpunkt, an dem die
Drosselschwelle fällt. Ein bloßer Prozentstand sagt nichts darüber, ob das Fenster reicht.

DROSSELN, gestuft:
- unter 20 % Rest: Aufgaben mit hohem Verbrauch UND niedriger Priorität temporär deaktivieren.
- unter 10 % Rest: nur noch hohe Priorität aktiv lassen - PLUS alle Pflegeaufgaben.
- über 50 % Rest: ursprünglichen Zustand wiederherstellen.
Drosseln geht nur als Wunsch und wirkt verzögert. Für akute Knappheit ist das zu langsam: melde
sie dem User zusätzlich sofort.

MODELLWECHSEL statt Abschaltung, wo Kontingent auf einer anderen Modelllinie frei ist und die
Aufgabe dafür geeignet ist - ebenfalls mit Vorzustand vermerken.

SPARE ZUERST BEI DIR SELBST. Bist du unter den größten Verbrauchern, senke deine eigene Frequenz,
bevor du fremde Aufgaben drosselst - aber nie unter die Selbstschutz-Untergrenze.

NICHT STEUERBARER SOCKEL: Steigt der Verbrauch in Zeiträumen, in denen nachweislich keine Aufgabe
lief, stammt er von außerhalb dieser App. Trage keine Vermutung ein, melde ihn dem User - und
rechne damit, dass Drosseln nur auf den messbaren Teil wirkt.
```

### 6.5 Rollenteil `task-sync` — Abgleich über Systeme hinweg

```
Du hältst diese Instanz mit den anderen Agenten im Gleichgewicht.

ENTITÄTENMODELL: Jede Kombination aus System und App ist eine EIGENE Entität mit eigenen
Automationen. Derselbe Anbieter auf zwei Rechnern zählt getrennt, und zwei Zugangswege desselben
Anbieters auf demselben Rechner ebenfalls.

1) Lies im geteilten Ordner, welche Automationen die anderen Entitäten fahren - Art, Umfang,
   Frequenz, aktiv oder nicht. Öffne dafür die LIVE-DEFINITIONEN, nicht die Übersichtstabellen:
   abgeschriebene Angaben sind regelmäßig falsch.
2) Übernimm Neues, das auch hier sinnvoll wäre, aber DEAKTIVIERT, mit an diese Umgebung
   angepassten Pfaden. Kannst du keine Aufgaben anlegen, lege nur den Auftragstext an und melde
   den fehlenden Registry-Eintrag.
3) Was im Lösch-Log steht, wird NICHT erneut aufgenommen.
4) Läuft dieselbe Aufgabe anderswo bereits zuverlässig und ist von mittlerer oder niedriger
   Priorität, übernimm sie hier nur als deaktivierte Notfallreserve. Fällt der dortige Betreiber
   aus, aktiviere sie - mit Vermerk und Rückgabebedingung. Bei jedem Lauf neu prüfen.
5) Vergleiche gleichnamige Automationen: Ist die fremde Fassung neuer und besser, übernimm die
   Verbesserung.
6) Schreibe einen Delta-Bericht in den geteilten Ordner - er ist zugleich dein Sync-Nachweis.

Eine übernommene Aufgabe ohne Auftragstext ist eine leere Hülle. Wenn du fremde Kopien deiner
Aufgaben ohne Prompttext findest, fordere den Text an, statt die Kopie für Abdeckung zu halten.
```

## 7. Zeitplan und Reihenfolge

**Zeitplan:** Alle fünf laufen **täglich**, aber zu deutlich getrennten Zeiten — sie greifen auf
dieselben Dateien zu. Bewährt hat sich: `scheduler-tuner` früh morgens, `text-improver` mittags,
`task-care` abends, `task-sync` spät, `token-watcher` zwei- bis viermal über den Tag verteilt.
Lege sie **nicht** in denselben Block wie die fachlichen Aufgaben.

**Reihenfolge beim Aufbau** — jede Stufe erst abschließen, wenn sie belegt funktioniert:

1. Die vier Fragen aus Abschnitt 2 beantworten, **einschließlich des Persistenztests**.
2. `_care`-Struktur anlegen.
3. Ist die Registry flüchtig: Wunschkanal und Merger bauen, Auslöser registrieren, **mit einem
   echten Wunsch verifizieren**, dass er ankommt.
4. `task-care` als erste Rolle einrichten — sie deckt die groben Defekte auf.
5. `text-improver` und `scheduler-tuner`.
6. `token-watcher`, sobald mehrere Aufgaben regelmäßig laufen.
7. `task-sync` zuletzt, wenn es überhaupt andere Systeme gibt.

## 8. Portierung auf einen anderen Anbieter

Das Muster ist anbieterneutral; nur drei Dinge ändern sich:

- **Registry-Format.** Eine TOML je Automation statt einer gemeinsamen JSON-Datei ändert nichts
  am Verfahren — der Wunschkanal beschreibt dann eben TOML-Felder.
- **Persistenz.** Schreibt der Anbieter seine Definitionen nicht aus dem Speicher zurück, ist der
  Umweg über den Merger unnötig; die Rollen dürfen dann direkt schreiben. **Das ist zu messen,
  nicht anzunehmen.**
- **Selbstschutz-Präfix.** Jeder Anbieter braucht sein eigenes, damit die Aufsicht nicht die
  Aufsicht eines anderen abschaltet.

Unverändert bleiben: Rollentrennung, eine Stellschraube pro Lauf, gemeinsames Gedächtnis mit
Vorzustand, Lösch-Log, Faktentreue gegen Laufprotokolle statt gegen Vermutungen.

## 9. Die teuersten Fehler — aus dem Betrieb

- **Anlegedatum für Laufdatum halten.** Eine Aufgabe, die nach ihrem ersten Termin angelegt
  wurde, sieht aus wie eine tote — und wird fälschlich repariert.
- **Den Wunschkanal ohne Auslöser bauen.** Sieht vollständig aus, wirkt aber nie. Der Prompt muss
  die Prüfung des Auslösers erzwingen.
- **Denselben Wunsch wiederholen**, weil er noch nicht angewendet ist. Führt zu Wunschstapeln,
  die niemand mehr auseinanderhält.
- **Aus Übersichtstabellen statt aus Live-Definitionen arbeiten.** Fremdangaben werden
  voneinander abgeschrieben und veralten unbemerkt.
- **Eine Aufgabe abschalten, die nur schlecht beschrieben war.** Erst den Text prüfen, dann die
  Aktivierung.
- **Verbrauchsproxys in Kontingentprozente umrechnen.** Sie taugen zum Rangieren („welche Aufgabe
  ist teurer"), nicht zum Hochrechnen von Restmengen.
