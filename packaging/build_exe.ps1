# LicTracer desktop packaging script (Windows PowerShell 5.1+, ASCII only).
# Prereq: .venv ready with all extras:
#   .venv\Scripts\python -m pip install -e ".[dev,gui,package]"
# Run:   powershell -ExecutionPolicy Bypass -File packaging\build_exe.ps1
# Output: dist\LicTracer\LicTracer.exe  (onedir; ship the whole folder, e.g. zipped)
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $repoRoot

Write-Host "[1/2] Cleaning previous build output..." -ForegroundColor Cyan
foreach ($d in @("build\LicTracer", "dist\LicTracer")) {
    if (Test-Path $d) { Remove-Item -Recurse -Force $d }
}

Write-Host "[2/2] Running PyInstaller (takes a few minutes)..." -ForegroundColor Cyan
& ".venv\Scripts\python" -m PyInstaller --noconfirm --clean packaging\lictracer_gui.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed (exit=$LASTEXITCODE)" }

$exe = "dist\LicTracer\LicTracer.exe"
if (-not (Test-Path $exe)) { throw "Build output not found: $exe" }
$sizeMB = [math]::Round((Get-ChildItem dist\LicTracer -Recurse -File | Measure-Object Length -Sum).Sum / 1MB, 1)
Write-Host "Build OK: $exe (folder total $sizeMB MB)" -ForegroundColor Green
Write-Host "Distribute: zip the whole dist\LicTracer folder, extract on target machine, double-click LicTracer.exe."
Write-Host "Before release, verify every item in docs\desktop-release-checklist.md."
