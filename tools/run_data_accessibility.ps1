$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

Write-Host "[INFO] Data accessibility validation start"

$pythonCmd = "python"
if ($env:KIWOOM_PYTHON -and (Test-Path $env:KIWOOM_PYTHON)) {
    $pythonCmd = $env:KIWOOM_PYTHON
}

Write-Host "[INFO] Python command: $pythonCmd"

if (Test-Path "requirements-data-accessibility.txt") {
    Write-Host "[INFO] Installing dependencies"
    & $pythonCmd -m pip install -r requirements-data-accessibility.txt
}

Write-Host "[INFO] Running Kiwoom access pre-check"
& $pythonCmd tools/kiwoom_access_check.py

Write-Host "[INFO] Running accessibility validator"
& $pythonCmd tools/data_accessibility_validator.py --check-environment --kiwoom-mode require

Write-Host "[INFO] Done: docs/data-accessibility-report.md"
