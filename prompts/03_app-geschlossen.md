# Betriebsart 3 — die App läuft **nicht**

Das ist der einzige Zustand, in dem direkt geschrieben werden darf. Der Merger erkennt
ihn selbst: Läuft die App nicht, arbeitet er die Wunschliste sofort ab.

---

## Prompt-Baustein

```text
Die Claude-Desktop-App läuft nicht. Du darfst die geplanten Aufgaben jetzt tatsächlich
ändern. Vorgehen:

1. Lage prüfen
     python <modul>/tools/apply_pending_tasks.py --paths
   Bestätigt Registry-Pfad und dass die App geschlossen ist.

2. Wunsch einreihen (auch jetzt der saubere Weg — er erzeugt Backup, Verifikation
   und Historie mit Vorzustand):
     python <modul>/tools/queue_request.py set <slug> --cron "0 6 * * *" --by "<wer>"

3. Anwenden
     python <modul>/tools/apply_pending_tasks.py
   Vorher gefahrlos ansehen: --dry-run

4. Ergebnis prüfen: Jede Zeile beginnt mit ANGEWENDET, ANGELEGT, ÜBERSPRUNGEN oder
   ABGELEHNT. ABGELEHNT nennt immer den Grund — nicht ignorieren.

Berichte, was wirklich in der Datei steht, nicht was du geschrieben hast. Der Merger
liest nach dem Schreiben erneut und meldet Abweichungen als WARNUNG.
```

---

## Neue Aufgabe anlegen

Eine Aufgabe besteht immer aus **zwei** Teilen — der Auftragstext allein genügt nicht:

1. `<Dokumente>/Claude/Scheduled/<slug>/SKILL.md` — was zu tun ist
2. ein Eintrag in der Aufgabenliste — **wann** es zu tun ist

Fehlt Teil 2, existiert der Ordner, die Aufgabe läuft aber nie und taucht in der App
nicht auf. Genau deshalb lehnt das Werkzeug ein `create` ohne `cronExpression` ab.

```bash
# Auftragstext vorbereiten
cat > auftrag.md <<'TEXT'
Fasse zusammen, was seit gestern in den freigegebenen Ordnern passiert ist.
Schreibe das Ergebnis als Markdown-Datei mit dem heutigen Datum im Namen.
TEXT

# Aufgabe anlegen: täglich 07:00, mit einer Ordnerfreigabe
python <modul>/tools/queue_request.py create tagesbericht \
    --cron "0 7 * * *" \
    --description "Fasst den Vortag zusammen" \
    --body-file auftrag.md \
    --folder "<pfad-den-die-aufgabe-lesen-darf>" \
    --by "setup"

python <modul>/tools/apply_pending_tasks.py
```

**Ohne `--folder` läuft die Aufgabe ins Leere**, sobald ihr Auftragstext lokale Pfade
nennt: Sie startet, sieht die Dateien aber nicht.

Neu angelegte Aufgaben erscheinen erst **nach dem nächsten Start der App** in der
Liste — die App liest die Aufgabenliste beim Start.

---

## Cron-Kurzreferenz

| Ausdruck | Bedeutung |
|---|---|
| `0 7 * * *` | täglich 07:00 |
| `0 8,12,16,20 * * *` | täglich um 08:00, 12:00, 16:00 und 20:00 |
| `30 6 * * 1-5` | werktags 06:30 |
| `0 3 * * 0` | sonntags 03:00 |

Zeitzone ist die des Rechners. Mehrere Aufgaben auf dieselbe Minute zu legen, ist die
häufigste Ursache dafür, dass eine davon still ausfällt — entzerren.
