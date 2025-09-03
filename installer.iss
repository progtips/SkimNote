; Скрипт установки Inno Setup для SkimNote
; Создайте установщик, запустив: iscc installer.iss

[Setup]
; Основная информация о программе
AppName=SkimNote
AppVersion=1.02
AppPublisher=ProgTips
AppPublisherURL=https://progtips.ru/skimnote
AppSupportURL=https://progtips.ru/skimnote
AppUpdatesURL=https://progtips.ru/skimnote
DefaultDirName={autopf}\SkimNote
DefaultGroupName=SkimNote
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer
OutputBaseFilename=SkimNote_Setup
SetupIconFile=icons\app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Языки
ShowLanguageDialog=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Languages\English.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; Основной исполняемый файл
Source: "dist\SkimNote.exe"; DestDir: "{app}"; Flags: ignoreversion
; Иконки
Source: "icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion recursesubdirs createallsubdirs
; Файл лицензии
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
; README файл (если есть)
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SkimNote"; Filename: "{app}\SkimNote.exe"
Name: "{group}\{cm:UninstallProgram,SkimNote}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\SkimNote"; Filename: "{app}\SkimNote.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\SkimNote"; Filename: "{app}\SkimNote.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\SkimNote.exe"; Description: "{cm:LaunchProgram,SkimNote}"; Flags: nowait postinstall skipifsilent

[Code]
// (Пользовательская логика не требуется)

[CustomMessages]
; Русские сообщения
russian.LicenseAccepted=Я принимаю условия лицензионного соглашения
russian.LicenseNotAccepted=Вы должны принять условия лицензионного соглашения для продолжения установки.
; Английские сообщения
english.LicenseAccepted=I accept the terms of the license agreement
english.LicenseNotAccepted=You must accept the terms of the license agreement to continue with the installation. 