#define MyAppName "PDFSilo"
#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif
#define MyAppPublisher "Abdellah HALLOU"
#define MyAppURL "https://pdfsilo.com/"
#define MyAppSupportURL "https://pdfsilo.com/faq/"
#define MyAppUpdatesURL "https://github.com/ABDELLAH-Hallou/PDFSilo/releases"
#define MyAppExeName "PDFSilo.exe"

[Setup]
AppId={{42D6E175-AD4A-4D6A-98F6-E85A25A86F62}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppSupportURL}
AppUpdatesURL={#MyAppUpdatesURL}
DefaultDirName={localappdata}\Programs\PDFSilo
DefaultGroupName=PDFSilo
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
OutputDir=..\..\dist\installer
OutputBaseFilename=PDFSilo-Setup-{#MyAppVersion}-x64
SetupIconFile=pdfsilo.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
MinVersion=10.0.17763
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=yes
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Privacy-first local PDF toolkit
VersionInfoCopyright=Copyright (c) 2026-present Abdellah HALLOU
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; \
    GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\..\dist\windows\PDFSilo.dist\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PDFSilo"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\PDFSilo"; Filename: "{app}\{#MyAppExeName}"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch PDFSilo"; \
    Flags: nowait postinstall skipifsilent
