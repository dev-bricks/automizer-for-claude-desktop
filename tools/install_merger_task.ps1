# install_merger_task.ps1
# Registriert einen stuendlichen, fensterlosen Windows-Task, der die Aenderungswuensche
# anwendet, sobald die Claude-Desktop-App geschlossen ist.
#
# Warum ueberhaupt ein Task ausserhalb der App:
# Aenderungen an scheduled-tasks.json ueberleben nicht, solange die App laeuft - sie
# schreibt die Datei aus ihrem Speicher neu. Der Merger muss daher warten koennen.
#
# Aufruf (normale PowerShell, KEIN Admin noetig - der Task laeuft im Benutzerkontext):
#     powershell -ExecutionPolicy Bypass -File "<dieser Pfad>"
# Eigener Name / anderes Intervall:
#     ... -File "<pfad>" -TaskName "mein-merger" -IntervalHours 2
# Entfernen:
#     Unregister-ScheduledTask -TaskName "claude-desktop-pending-merger" -Confirm:$false

param(
    [string]$TaskName = "claude-desktop-pending-merger",
    [int]$IntervalHours = 1,
    [int]$StartOffsetMinutes = 7
)

$ErrorActionPreference = "Stop"

$Wrapper = Join-Path $PSScriptRoot "run_apply_pending_hidden.vbs"
$Merger  = Join-Path $PSScriptRoot "apply_pending_tasks.py"

if (-not (Test-Path $Wrapper)) { throw "Wrapper nicht gefunden: $Wrapper" }
if (-not (Test-Path $Merger))  { throw "Merger nicht gefunden: $Merger" }

# wscript //B (Batchmodus, keine Dialoge) //Nologo - der Wrapper versteckt das Fenster selbst
$Action = New-ScheduledTaskAction -Execute "wscript.exe" `
    -Argument ("//B //Nologo `"{0}`"" -f $Wrapper)

# Die App ist oft offen; dann tut der Lauf nichts und probiert es spaeter erneut.
# StartWhenAvailable holt Laeufe bei ausgeschaltetem Rechner nach.
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddMinutes($StartOffsetMinutes) `
    -RepetitionInterval (New-TimeSpan -Hours $IntervalHours)

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
    -Settings $Settings -Description `
    "Wendet Aenderungswuensche auf die geplanten Aufgaben der Claude-Desktop-App an, sobald diese geschlossen ist." `
    -Force | Out-Null

Write-Host "Task '$TaskName' registriert (alle $IntervalHours h)."
Write-Host ""
Write-Host "Abnahme (bitte einmal durchgehen):"
Write-Host "  1. Bei GEOEFFNETER App:   Start-ScheduledTask -TaskName $TaskName"
Write-Host "     -> nichts darf sich aendern, die Wunschliste bleibt voll."
Write-Host "  2. App schliessen, erneut Start-ScheduledTask"
Write-Host "     -> Wunsch steht als ANGEWENDET im Log, applied-tasks.json hat previousValues."
Write-Host "  3. Waehrend beider Laeufe darf KEIN Fenster aufblitzen."
Write-Host ""
Write-Host "Status jederzeit ohne Task:  python `"$Merger`" --status"
Write-Host "Pfade pruefen:               python `"$Merger`" --paths"
