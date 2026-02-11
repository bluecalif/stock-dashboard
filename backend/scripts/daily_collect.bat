@echo off
REM ============================================================
REM Stock Dashboard - Daily OHLCV Collection
REM Schedule: Daily 18:00 KST via Windows Task Scheduler
REM Collects last 7 days (UPSERT-safe overlap for gap prevention)
REM ============================================================

setlocal enabledelayedexpansion

REM UTF-8 output
set PYTHONUTF8=1
chcp 65001 >nul 2>&1

REM Resolve paths (script is in backend/scripts/)
set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%..
set PROJECT_ROOT=%SCRIPT_DIR%..\..
set VENV_PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe
set COLLECT_SCRIPT=%BACKEND_DIR%\scripts\collect.py
set HEALTHCHECK_SCRIPT=%BACKEND_DIR%\scripts\healthcheck.py
set LOG_DIR=%PROJECT_ROOT%\logs

REM Verify venv exists
if not exist "%VENV_PYTHON%" (
    echo ERROR: venv not found at %VENV_PYTHON%
    echo Run: cd backend ^&^& python -m venv .venv ^&^& pip install -e ".[dev]"
    exit /b 1
)

REM Create logs directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Calculate dates using Python (T-7 to T)
for /f %%i in ('"%VENV_PYTHON%" -c "from datetime import date,timedelta;print((date.today()-timedelta(days=7)).isoformat())"') do set START_DATE=%%i
for /f %%i in ('"%VENV_PYTHON%" -c "from datetime import date;print(date.today().isoformat())"') do set END_DATE=%%i
for /f %%i in ('"%VENV_PYTHON%" -c "from datetime import date;print(date.today().strftime('%%Y%%m%%d'))"') do set LOG_DATE=%%i

set LOG_FILE=%LOG_DIR%\collect_%LOG_DATE%.log

echo [%date% %time%] Starting daily collection: %START_DATE% ~ %END_DATE%
echo Log: %LOG_FILE%

REM Run collection
"%VENV_PYTHON%" "%COLLECT_SCRIPT%" --start %START_DATE% --end %END_DATE% >> "%LOG_FILE%" 2>&1
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% EQU 0 (
    echo [%date% %time%] Collection completed successfully.
) else (
    echo [%date% %time%] Collection finished with errors (exit code: %EXIT_CODE%).
)

echo [%date% %time%] Collection exit code: %EXIT_CODE% >> "%LOG_FILE%"

REM Run data freshness check
echo [%date% %time%] Running healthcheck...
"%VENV_PYTHON%" "%HEALTHCHECK_SCRIPT%" >> "%LOG_FILE%" 2>&1
set HC_CODE=%ERRORLEVEL%

if %HC_CODE% EQU 0 (
    echo [%date% %time%] Healthcheck passed.
) else (
    echo [%date% %time%] Healthcheck found stale data (exit code: %HC_CODE%).
)

echo [%date% %time%] Healthcheck exit code: %HC_CODE% >> "%LOG_FILE%"

endlocal
REM Exit with collection exit code (primary indicator)
exit /b %EXIT_CODE%
