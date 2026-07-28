[CmdletBinding()]
param(
    [string]$ExecutablePath,
    [int]$TimeoutSeconds = 60
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
if (-not $ExecutablePath) {
    $ExecutablePath = Join-Path `
        $projectRoot `
        "dist\windows\PDFSilo.dist\PDFSilo.exe"
}
if (-not (Test-Path -LiteralPath $ExecutablePath -PathType Leaf)) {
    throw "Packaged executable was not found: $ExecutablePath"
}

function Invoke-PackageCheck {
    param([string[]]$Arguments)

    $process = Start-Process `
        -FilePath $ExecutablePath `
        -ArgumentList $Arguments `
        -PassThru `
        -WindowStyle Hidden
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        Stop-Process -Id $process.Id -Force
        throw "Packaged process exceeded the $TimeoutSeconds second timeout."
    }
    if ($process.ExitCode -ne 0) {
        throw "Packaged process failed with exit code $($process.ExitCode)."
    }
}

Invoke-PackageCheck -Arguments @("--smoke-test")

$validationRoot = Join-Path $projectRoot "dist\windows\package-validation"
New-Item -ItemType Directory -Path $validationRoot -Force | Out-Null
Invoke-PackageCheck -Arguments @("--package-self-test", "`"$validationRoot`"")

$reportPath = Join-Path $validationRoot "pdfsilo-package-self-test.json"
if (-not (Test-Path -LiteralPath $reportPath -PathType Leaf)) {
    throw "The packaged self-test report was not created."
}
$report = Get-Content -LiteralPath $reportPath -Encoding UTF8 -Raw |
    ConvertFrom-Json
if (-not $report.success) {
    throw "Packaged workflow validation failed: $($report.error)"
}

Write-Host "GUI startup smoke test passed."
Write-Host (
    "Packaged PDF workflows passed with {0} pages at path length {1}." -f `
        $report.page_count,
        $report.validation_path_length
)
Write-Host "Validation report: $reportPath"
