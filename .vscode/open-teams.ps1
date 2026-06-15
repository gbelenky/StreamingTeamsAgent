# Opens the Teams sideload URL for the locally-provisioned app in the
# requested browser. TEAMS_APP_ID is read from env/.env.local (written by
# Microsoft 365 Agents Toolkit during Provision).
param(
    [ValidateSet('msedge', 'chrome')]
    [string]$Browser = 'msedge'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $repoRoot 'env/.env.local'

if (-not (Test-Path $envFile)) {
    Write-Error "Could not find $envFile. Run Provision first."
    exit 1
}

$match = Select-String -Path $envFile -Pattern '^TEAMS_APP_ID=(.+)$' | Select-Object -First 1
if (-not $match) {
    Write-Error "TEAMS_APP_ID is not set in $envFile. Run Provision first."
    exit 1
}

$teamsAppId = $match.Matches[0].Groups[1].Value.Trim()
$url = "https://teams.microsoft.com/l/app/$teamsAppId" + '?installAppPackage=true&webjoin=true'

Write-Host "Opening Teams app $teamsAppId in $Browser..."
Start-Process "$Browser.exe" $url
