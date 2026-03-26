; Inno Setup Script for Cancer Detection Dashboard
; This script packages the PyInstaller output folder into a true "Next > Next" Windows installer.

#define MyAppName "Cancer Detection Dashboard"
#define MyAppVersion "1.0.2"
#define MyAppPublisher "Clinical AI"
#define MyAppExeName "CancerDetectionDashboard.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
AppId={{9FAD6A8D-1B90-44DE-8B89-234234234234}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; We output the installer directly into the 'dist' folder next to the zip
OutputDir=dist
OutputBaseFilename=CancerDetectionDashboard_Installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=logo.ico

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Notice how this grabs everything inside dist\CancerDetectionDashboard
Source: "dist\CancerDetectionDashboard\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\CancerDetectionDashboard\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
