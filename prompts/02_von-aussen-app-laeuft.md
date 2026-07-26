# Betriebsart 2 — Zugriff **von außen**, während die App läuft

Gemeint ist ein Agent oder Mensch außerhalb der Desktop-App (CLI-Agent, Terminal,
anderes Automationssystem), der eine Aufgabe der App ändern oder anlegen will,
während die App geöffnet ist.

**Die Lage ist dieselbe wie in Betriebsart 1:** Solange die App läuft, überlebt keine
direkte Änderung an der Aufgabenliste — sie wird aus dem Speicher der App
überschrieben. Der Unterschied ist nur, dass du hier ein Werkzeug aufrufen kannst,
statt JSON von Hand zu schreiben.

---

## Prompt-Baustein

```text
Du sollst eine geplante Aufgabe der Claude-Desktop-App ändern. Die App läuft gerade.

Schreibe NICHT direkt in scheduled-tasks.json — die App überschreibt das lautlos.
Reihe den Wunsch stattdessen ein:

  python <modul>/tools/queue_request.py set <slug> --cron "0 8,20 * * *" \
      --reason "<warum>" --by "<wer du bist>"

Weitere Felder: --disabled / --enabled, --model <name>,
--folder <pfad> (wiederholbar, ersetzt die Freigabeliste),
--permission-mode auto|bypassPermissions

Danach prüfen, was offen ist:
  python <modul>/tools/apply_pending_tasks.py --status

Der Wunsch greift, sobald die App geschlossen ist und der Merger läuft (stündlicher
Windows-Task oder manueller Aufruf). Melde dem Nutzer genau das — nicht "erledigt",
sondern "eingereiht, wirkt nach dem Schließen der App".

Reiche denselben Wunsch nicht zweimal ein. Steht er schon in der Liste, lass ihn stehen.
```

---

## Wenn die Änderung sofort gelten muss

Dann führt kein Weg daran vorbei, die App zu schließen — danach gilt Betriebsart 3.
Sag das dem Nutzer offen, statt es zu umgehen: Ein Schreibversuch in die laufende App
sieht erfolgreich aus und ist es nicht.

Prüfen, ob die App überhaupt läuft:

```bash
python <modul>/tools/apply_pending_tasks.py --paths
```

Die letzte Zeile der Ausgabe sagt `laeuft` oder `geschlossen`. Lässt sich der Zustand
nicht ermitteln, meldet das Werkzeug bewusst „läuft" — im Zweifel wird nicht
geschrieben.

---

## Typische Fehlerbilder

| Symptom | Ursache |
|---|---|
| Wunsch bleibt ewig liegen | App war nie zu, oder der Merger-Task ist nicht registriert |
| „Aufgabe existiert nicht in der Registry" | Slug falsch geschrieben — er ist der Ordnername unter `Scheduled\` |
| Aufgabe läuft trotz Änderung nicht | Kein `cronExpression` gesetzt; ohne Zeitplan erscheint sie nicht einmal in der Liste |
| Aufgabe läuft, findet aber keine Dateien | `userSelectedFolders` deckt die im Auftragstext genannten Pfade nicht ab |
