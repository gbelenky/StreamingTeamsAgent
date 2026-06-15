# Opens the Teams sideload URL for the locally-provisioned app in the
# requested browser. TEAMS_APP_ID is read from env/.env.local (written by
# Microsoft 365 Agents Toolkit during Provision).
#
# To open in a specific browser profile (recommended when you have a
# personal Edge profile signed into a different M365 tenant than the bot),
# set BROWSER_PROFILE_DIR in env/.env.local.user, e.g.:
#   BROWSER_PROFILE_DIR=Profile 1
# Find profile folder names under %LOCALAPPDATA%\Microsoft\Edge\User Data
# or  %LOCALAPPDATA%\Google\Chrome\User Data.
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

# Optional profile override. Check env/.env.local.user first, then process env.
$profileDir = $env:BROWSER_PROFILE_DIR
$userEnvFile = Join-Path $repoRoot 'env/.env.local.user'
if (-not $profileDir -and (Test-Path $userEnvFile)) {
    $pMatch = Select-String -Path $userEnvFile -Pattern '^BROWSER_PROFILE_DIR=(.+)$' | Select-Object -First 1
    if ($pMatch) {
        $profileDir = $pMatch.Matches[0].Groups[1].Value.Trim().Trim('"').Trim("'")
    }
}

$argsList = @()
if ($profileDir) {
    Write-Host "Opening Teams app $teamsAppId in $Browser (profile: $profileDir)..."
    $argsList += "--profile-directory=$profileDir"
} else {
    Write-Host "Opening Teams app $teamsAppId in $Browser (default profile)..."
    Write-Host "  Tip: set BROWSER_PROFILE_DIR in env/.env.local.user to pin a specific profile."
}
$argsList += $url

Start-Process "$Browser.exe" -ArgumentList $argsList
