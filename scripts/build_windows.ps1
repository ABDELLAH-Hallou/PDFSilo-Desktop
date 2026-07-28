[CmdletBinding()]
param(
    [string]$PythonPath,
    [switch]$KeepDeploymentFiles
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path

if (-not $PythonPath) {
    $PythonPath = Join-Path $projectRoot "venv\Scripts\python.exe"
}
$environmentRoot = Split-Path -Parent (Split-Path -Parent $PythonPath)
$deployScript = Join-Path `
    $environmentRoot `
    "Lib\site-packages\PySide6\scripts\deploy.py"
$configPath = Join-Path $projectRoot "pysidedeploy.spec"
$iconScript = Join-Path $projectRoot "scripts\generate_windows_icon.py"
$outputDirectory = Join-Path $projectRoot "dist\windows\PDFSilo.dist"
$expectedExecutable = Join-Path $outputDirectory "PDFSilo.exe"

foreach ($requiredPath in @(
    $PythonPath,
    $deployScript,
    $configPath,
    $iconScript
)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Required deployment file was not found: $requiredPath"
    }
}

Push-Location $projectRoot
try {
    if (Test-Path -LiteralPath $outputDirectory) {
        $resolvedOutput = (Resolve-Path -LiteralPath $outputDirectory).Path
        $expectedRoot = (Join-Path $projectRoot "dist\windows") +
            [IO.Path]::DirectorySeparatorChar
        if (-not $resolvedOutput.StartsWith(
            $expectedRoot,
            [StringComparison]::OrdinalIgnoreCase
        )) {
            throw "Refusing to replace an output outside dist\windows."
        }
        Remove-Item -LiteralPath $resolvedOutput -Recurse -Force
    }

    & $PythonPath $iconScript
    if ($LASTEXITCODE -ne 0) {
        throw "Windows icon generation failed with exit code $LASTEXITCODE."
    }

    $arguments = @(
        "-c",
        $configPath,
        "--force",
        "--extra-ignore-dirs=venv,tests,Skills,Fixes,docs,build,dist"
    )
    if ($KeepDeploymentFiles) {
        $arguments += "--keep-deployment-files"
    }
    & $PythonPath $deployScript @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "pyside6-deploy failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $expectedExecutable -PathType Leaf)) {
    $candidate = Get-ChildItem `
        -LiteralPath (Join-Path $projectRoot "dist\windows") `
        -Filter "PDFSilo.exe" `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $candidate) {
        throw "The deployment completed but PDFSilo.exe was not found."
    }
    $candidateDirectory = $candidate.Directory
    if (
        $candidateDirectory.Parent.FullName -ne
            (Join-Path $projectRoot "dist\windows") -or
        $candidateDirectory.Extension -ne ".dist"
    ) {
        throw (
            "PDFSilo.exe was not inside a standalone .dist directory: " +
            $candidate.FullName
        )
    }
    Move-Item `
        -LiteralPath $candidateDirectory.FullName `
        -Destination $outputDirectory
}

$checksum = (
    Get-FileHash -LiteralPath $expectedExecutable -Algorithm SHA256
).Hash.ToLowerInvariant()
$checksumPath = "$expectedExecutable.sha256"
"$checksum  $([IO.Path]::GetFileName($expectedExecutable))" |
    Set-Content -LiteralPath $checksumPath -Encoding ascii

Write-Host "Standalone application: $expectedExecutable"
Write-Host "SHA-256 file: $checksumPath"
