; pcrc_installer.iss - Inno Setup script for Records Classifier
[Setup]
AppName=Pierce County Records Classifier
AppVersion=1.0
DefaultDirName={pf64}\PierceCounty\RecordsClassifier
OutputDir=release
OutputBaseFilename=PCRC_Setup
SilentInstall=false
Compression=lzma
SolidCompression=yes

[Files]
Source: "{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer\models\*"; DestDir: "{app}\models"; Flags: recursesubdirs ignoreversion
Source: "installer\install_ollama.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "PC_Logo_Round_white.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Records Classifier"; Filename: "{app}\PC-RecordsClassifier.exe"
Name: "{userdesktop}\Records Classifier"; Filename: "{app}\PC-RecordsClassifier.exe"

[Run]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File \"{app}\install_ollama.ps1\""; StatusMsg: "Setting up local model..."; Flags: runhidden
