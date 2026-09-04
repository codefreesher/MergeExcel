#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppName "Excel Merger Pro"
#define AppExeName "ExcelMergerPro.exe"

[Setup]
AppId={{66E30196-6CAA-4FEC-B560-ECA6D1DA10B6}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Excel Merger Pro
DefaultDirName={localappdata}\Programs\Excel Merger Pro
DefaultGroupName=Excel Merger Pro
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\installer-output
OutputBaseFilename=ExcelMergerPro-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=yes
UninstallDisplayIcon={app}\{#AppExeName}

[Files]
Source: "..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "Tạo shortcut trên Desktop"; GroupDescription: "Shortcut:"; Flags: unchecked

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Khởi động {#AppName}"; Flags: nowait postinstall skipifsilent

