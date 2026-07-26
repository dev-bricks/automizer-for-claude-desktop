# Betriebsart 1 — das LLM läuft **in** der Desktop-App

Gemeint ist ein Lauf, der selbst eine geplante Aufgabe der App ist und andere Aufgaben
pflegen soll (Zeitpläne entzerren, Freigaben ergänzen, tote Einträge melden).

**Die eine Regel dieser Betriebsart:** aus der App heraus **nie** direkt in die
Aufgabenliste schreiben. Die App hält sie im Speicher und schreibt sie beim Ende des
Laufs neu — jede direkte Änderung ist danach weg, ohne Fehlermeldung. Stattdessen wird
ein Wunsch hinterlegt, den der Merger später anwendet.

Nicht betroffen sind Auftragstexte (`SKILL.md`), die Dateien im `_care`-Ordner und eigene
Berichte — die dürfen direkt geschrieben werden.

---

## Prompt-Baustein (in den Auftragstext der Pflege-Aufgabe übernehmen)

```text
Du pflegst die geplanten Aufgaben dieser Claude-Desktop-Instanz. Ändere nur, was
eindeutig ist — alles andere wird gemeldet, nicht geraten.

SCHREIBREGEL (nicht verhandelbar)
Du läufst innerhalb der geöffneten App. Schreibe NIEMALS selbst in
scheduled-tasks.json: Die App schreibt die Datei beim nächsten Lauf-Ende aus ihrem
Speicher neu und setzt deine Änderung lautlos zurück. Lege dort auch keine Backups an.

Stattdessen stellst du einen Änderungswunsch:

  Datei:  <Dokumente>/Claude/Scheduled/_care/pending/pending-tasks.json
  Format: {"pending": [ {"op": "set",
                         "taskId": "<slug>",
                         "fields": {"cronExpression": "0 8 * * *"},
                         "reason": "<warum, in einem Satz>",
                         "requestedBy": "<dein slug>",
                         "requestedAt": "<ISO-Zeit>"} ]}

  Vorgehen: Datei lesen (fehlt sie, mit {"pending": []} anlegen), deinen Wunsch
  anhängen, zurückschreiben. Wünsche anderer Läufe dabei NICHT entfernen.
  Erlaubte Felder: cronExpression, enabled, model, userSelectedFolders,
  permissionMode, disableJitter.

Ein Wunsch wirkt VERZÖGERT — er greift erst, wenn die App geschlossen ist und der
Merger läuft. Trage ihn ein und prüfe im Folgelauf, ob er angewendet wurde, statt ihn
zu wiederholen. Liegt derselbe Wunsch schon in der Liste, lass ihn stehen. Wurde er
abgelehnt, steht der Grund im Log.

WAS DU PRÜFST
1. Registry und Ordner beidseitig abgleichen: Einträge ohne Auftragstext (toter
   filePath) und Ordner ohne Registry-Eintrag (unsichtbare Aufgabe, läuft nie).
2. Einträge ohne cronExpression melden — sie laufen nie und erscheinen nicht in der
   Liste der App. Einen Zeitplan setzt du nur dort, wo schon einer war.
3. Freigaben: Nennt der Auftragstext lokale Pfade, die userSelectedFolders nicht
   abdecken? Dann läuft die Aufgabe ins Leere — Wunsch stellen.
4. Fremde Benutzerpfade in Auftragstexten melden (Umschreibung auf %USERPROFILE%).
5. Lauf-Aktualität: lastRunAt gegen cronExpression halten. Deutlich überfällige
   Aufgaben sind still gestorben. "Eingetragen" ist kein Beleg für "hat gelaufen".

SELBSTSCHUTZ
Aufgaben, die zum Pflegeverbund gehören, nie deaktivieren, löschen oder seltener als
täglich takten — sonst schaltet sich die Pflege selbst ab. Zeitpläne nie erfinden.
```

---

## Was du dabei nicht erwarten darfst

- **Sofortige Wirkung.** Der Wunsch liegt, bis die App zu ist. Wer im selben Lauf
  nachsieht, findet die Änderung nicht — das ist kein Fehler.
- **Löschen.** Über diesen Weg nicht vorgesehen; melde es dem Menschen.
- **Anlegen aus der App heraus.** Technisch möglich (`op: create`), aber der neue
  Eintrag erscheint erst nach einem Neustart der App in der Liste.
