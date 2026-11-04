' ============================================================
'  DeepSeek Chatbot - tihi launcher (bez konzole)
'  Dvoklik na ovaj fajl pokreće aplikaciju bez crnog prozora.
'  Prečicu možeš napraviti na Desktop: desni klik -> Send to -> Desktop.
' ============================================================
Option Explicit

Dim sh, fso, base, py, cmd, rc

Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

base = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = base

' Pronađi Python: prvo "py" launcher, pa "python"
py = ""
rc = sh.Run("cmd /c py -3 -c ""import sys""", 0, True)
If rc = 0 Then
    py = "py -3"
Else
    rc = sh.Run("cmd /c python -c ""import sys""", 0, True)
    If rc = 0 Then
        py = "python"
    End If
End If

If py = "" Then
    MsgBox "Python nije pronađen." & vbCrLf & _
           "Instaliraj Python sa https://www.python.org/downloads/", _
           vbCritical, "DeepSeek Chatbot"
    WScript.Quit 1
End If

' 0 = skriven prozor, False = ne čekaj (da se skripta odmah zatvori)
cmd = "cmd /c cd /d """ & base & """ && " & py & " main.py"
sh.Run cmd, 0, False
