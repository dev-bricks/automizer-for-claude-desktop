' run_apply_pending_hidden.vbs
' Startet apply_pending_tasks.py OHNE sichtbares Fenster.
'
' Warum ein VBS-Wrapper und nicht direkt pythonw?
' "Fensterlos" heisst hier: versteckte Konsole, nicht gar keine. Ein nacktes pythonw genuegt
' nicht, sobald Unterprozesse starten (der Merger ruft powershell auf) - die allozieren sich
' sonst eigene, sichtbare Konsolen. WScript.Shell.Run(cmd, 0, False) versteckt das Fenster,
' im Python-Teil sorgt CREATE_NO_WINDOW fuer den Rest.
'
' Aufruf:  wscript.exe //B //Nologo "<pfad>\run_apply_pending_hidden.vbs"

Option Explicit

Dim fso, sh, skript, interpreter, kandidaten, i, cmd, ordner

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

ordner = fso.GetParentFolderName(WScript.ScriptFullName)
skript = fso.BuildPath(ordner, "apply_pending_tasks.py")

If Not fso.FileExists(skript) Then
    ' Kein stiller Tod: Grund in eine Datei neben dem Skript schreiben.
    Dim f
    Set f = fso.OpenTextFile(fso.BuildPath(ordner, "merger-wrapper.log"), 8, True)
    f.WriteLine Now & " FEHLER: " & skript & " nicht gefunden"
    f.Close
    WScript.Quit 1
End If

' pythonw zuerst, py-Launcher als Rueckfall. Beide starten ohne Konsolenfenster.
' Die Liste deckt Benutzer- und Maschineninstallationen ab; gefunden wird der erste Treffer.
kandidaten = Array( _
    sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"), _
    sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"), _
    sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"), _
    sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"), _
    sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe"), _
    sh.ExpandEnvironmentStrings("%PROGRAMFILES%\Python314\pythonw.exe"), _
    sh.ExpandEnvironmentStrings("%PROGRAMFILES%\Python313\pythonw.exe"), _
    sh.ExpandEnvironmentStrings("%PROGRAMFILES%\Python312\pythonw.exe"), _
    sh.ExpandEnvironmentStrings("%PROGRAMFILES%\Python311\pythonw.exe"), _
    sh.ExpandEnvironmentStrings("%PROGRAMFILES%\Python310\pythonw.exe"), _
    sh.ExpandEnvironmentStrings("%WINDIR%\pyw.exe") )

interpreter = ""
For i = 0 To UBound(kandidaten)
    If fso.FileExists(kandidaten(i)) Then
        interpreter = kandidaten(i)
        Exit For
    End If
Next

If interpreter = "" Then interpreter = "pythonw.exe"   ' letzter Rueckfall: PATH

cmd = """" & interpreter & """ """ & skript & """"

' 0 = verstecktes Fenster, False = nicht auf Ende warten
sh.Run cmd, 0, False
