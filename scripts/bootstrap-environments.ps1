param(
    [string]$PythonLauncher = "py",
    [string]$PythonVersion = "3.12"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Native command failed with exit code $LASTEXITCODE`: $Executable $($Arguments -join ' ')"
    }
}

$ChemEnvironment = Join-Path $ProjectRoot ".venv-chem"
$MammalEnvironment = Join-Path $ProjectRoot ".venv-mammal"
$VendorRoot = Join-Path $ProjectRoot "vendor\biomed-multi-alignment"
$BootstrapRoot = Join-Path $ProjectRoot "artifacts\bootstrap"

foreach ($target in @($ChemEnvironment, $MammalEnvironment)) {
    if (Test-Path -LiteralPath $target) {
        throw "Refusing to overwrite existing environment: $target"
    }
}

New-Item -ItemType Directory -Force -Path $BootstrapRoot | Out-Null
$ChemRequirements = Join-Path $BootstrapRoot "chemistry-third-party.txt"
$MammalRequirements = Join-Path $BootstrapRoot "mammal-third-party.txt"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$ChemPackages = @(Get-Content -LiteralPath "environment\chemistry-lock.txt" |
    Where-Object { $_ -notmatch '^mammal-dili==' })
$MammalPackages = @(Get-Content -LiteralPath "environment\mammal-lock.txt" |
    Where-Object { $_ -notmatch '^(mammal-dili|biomed-multi-alignment)==' })
[System.IO.File]::WriteAllLines($ChemRequirements, $ChemPackages, $Utf8NoBom)
[System.IO.File]::WriteAllLines($MammalRequirements, $MammalPackages, $Utf8NoBom)

Invoke-Checked $PythonLauncher @("-$PythonVersion", "-m", "venv", $ChemEnvironment)
$ChemPython = Join-Path $ChemEnvironment "Scripts\python.exe"
Invoke-Checked $ChemPython @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Checked $ChemPython @("-m", "pip", "install", "-r", $ChemRequirements)
Invoke-Checked $ChemPython @("-m", "pip", "install", "--no-deps", "-e", ".")

Invoke-Checked $PythonLauncher @("-$PythonVersion", "-m", "venv", $MammalEnvironment)
$MammalPython = Join-Path $MammalEnvironment "Scripts\python.exe"
Invoke-Checked $MammalPython @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Checked $MammalPython @("-m", "pip", "install", "-r", $MammalRequirements)

if (-not (Test-Path -LiteralPath $VendorRoot)) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $VendorRoot) | Out-Null
    Invoke-Checked "git" @("clone", "https://github.com/BiomedSciAI/biomed-multi-alignment.git", $VendorRoot)
}
Invoke-Checked "git" @("-C", $VendorRoot, "checkout", "--detach", "8cc56e9494b489ca86a63b76fa4cd2921f8af7f7")
$VendorRevision = (& git -C $VendorRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $VendorRevision -ne "8cc56e9494b489ca86a63b76fa4cd2921f8af7f7") {
    throw "Pinned MAMMAL vendor revision was not established"
}
Invoke-Checked $MammalPython @("-m", "pip", "install", "--no-deps", "-e", $VendorRoot)
Invoke-Checked $MammalPython @("-m", "pip", "install", "--no-deps", "-e", ".")

Invoke-Checked "pnpm.cmd" @("install", "--frozen-lockfile")
Write-Host "Created the two pinned Python environments and installed the web workspace."
