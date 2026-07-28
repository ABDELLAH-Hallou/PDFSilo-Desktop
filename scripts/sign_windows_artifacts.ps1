[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$CertificateThumbprint,
    [Parameter(Mandatory)]
    [string[]]$ArtifactPath,
    [string]$TimestampUrl = "https://timestamp.digicert.com",
    [string]$SignToolPath
)

$ErrorActionPreference = "Stop"
if (-not $SignToolPath) {
    $command = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        throw (
            "signtool.exe was not found. Install the Windows SDK or pass " +
            "-SignToolPath explicitly."
        )
    }
    $SignToolPath = $command.Source
}

foreach ($path in $ArtifactPath) {
    $resolved = (Resolve-Path -LiteralPath $path).Path
    & $SignToolPath sign `
        /sha1 $CertificateThumbprint `
        /fd SHA256 `
        /tr $TimestampUrl `
        /td SHA256 `
        $resolved
    if ($LASTEXITCODE -ne 0) {
        throw "Signing failed for $resolved."
    }
    & $SignToolPath verify /pa /all $resolved
    if ($LASTEXITCODE -ne 0) {
        throw "Signature verification failed for $resolved."
    }
}
