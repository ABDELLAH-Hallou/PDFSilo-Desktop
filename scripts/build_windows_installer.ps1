[CmdletBinding()]
param(
    [string]$Version = "0.1.0",
    [string]$IsccPath
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$standaloneDirectory = Join-Path $projectRoot "dist\windows\PDFSilo.dist"
$installerScript = Join-Path $projectRoot "packaging\windows\PDFSilo.iss"

if (-not (Test-Path -LiteralPath $standaloneDirectory -PathType Container)) {
    throw "Build the standalone application before creating an installer."
}
if (-not $IsccPath) {
    $command = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        throw (
            "Inno Setup 6 was not found. Install it, then pass " +
            "-IsccPath 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'."
        )
    }
    $IsccPath = $command.Source
}

Push-Location $projectRoot
try {
    & $IsccPath "/DMyAppVersion=$Version" $installerScript
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

$installer = Join-Path `
    $projectRoot `
    "dist\installer\PDFSilo-Setup-$Version-x64.exe"
if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
    throw "Installer output was not found: $installer"
}
$checksum = (
    Get-FileHash -LiteralPath $installer -Algorithm SHA256
).Hash.ToLowerInvariant()
"$checksum  $([IO.Path]::GetFileName($installer))" |
    Set-Content -LiteralPath "$installer.sha256" -Encoding ascii
Write-Host "Installer: $installer"
Write-Host "Checksum: $installer.sha256"
