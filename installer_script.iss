; Inno Setup Script za DeepSeek Code Assistant
; Instaliraj Inno Setup: https://jrsoftware.org/isdl.php
; Onda desni klik na ovaj fajl -> "Compile"
; Dobicete DeepSeek_Assistant_Setup.exe

#define MyAppName "DeepSeek Code Assistant"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Cole_Soft Krusevac"
#define MyAppURL "https://www.colesoft.net"
#define MyAppExeName "run.bat"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName=C:\ColeSoft\DeepSeekAssistant
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=DeepSeek_Assistant_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=deepseek.ico
UninstallDisplayIcon={app}\deepseek.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "serbian"; MessagesFile: "compiler:Languages\Serbian.isl"

[Tasks]
Name: "desktopicon"; Description: "Kreiraj prečicu na radnoj površini"; GroupDescription: "Dodatne opcije:"

[Files]
Source: "deepseek_chatbot.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "deepseek.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_deps.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "run.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\deepseek.ico"
Name: "{group}\Deinstaliraj {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\deepseek.ico"; Tasks: desktopicon

[Run]
; Prvo instaliraj zavisnosti (PyQt5)
Filename: "{app}\install_deps.bat"; Description: "Instaliraj PyQt5 i ostale zavisnosti"; Flags: postinstall nowait skipifsilent runascurrentuser
; Zatim pokreni aplikaciju
Filename: "{app}\{#MyAppExeName}"; Description: "Pokreni {#MyAppName}"; Flags: postinstall nowait skipifsilent shellexec

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip"; Flags: runhidden

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Kreiraj prazan fajl za settings (ako ne postoji)
    if not FileExists(ExpandConstant('{app}\settings.json')) then
    begin
      SaveStringToFile(ExpandConstant('{app}\settings.json'), '{}', False);
    end;
  end;
end;
