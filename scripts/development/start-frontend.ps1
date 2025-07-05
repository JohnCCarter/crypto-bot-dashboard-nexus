# PowerShell-skript för att starta frontend-utvecklingsservern på ett smidigt sätt

# Gå till projektets rotmapp
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = (Get-Item $scriptPath).Parent.Parent.FullName
Set-Location -Path $rootPath

# Kontrollera om node_modules finns, om inte installera beroenden
if (-not (Test-Path -Path "node_modules")) {
    Write-Host "node_modules hittades inte. Installerar beroenden..."
    npm install
}

# Skapa .vscode/settings.json om den inte finns
if (-not (Test-Path -Path ".vscode")) {
    New-Item -ItemType Directory -Path ".vscode" | Out-Null
}

if (-not (Test-Path -Path ".vscode/settings.json")) {
    @'
{
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true
}
'@ | Out-File -FilePath ".vscode/settings.json" -Encoding utf8
    Write-Host "Skapade .vscode/settings.json för TypeScript-konfiguration"
}

# Starta utvecklingsservern
Write-Host "Startar frontend-utvecklingsservern..."
npm run dev 