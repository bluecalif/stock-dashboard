@echo off
REM ============================================================
REM Stock Dashboard - Register Windows Task Scheduler
REM Creates a daily task to run daily_collect.bat at 18:00
REM Must run as Administrator
REM ============================================================

setlocal

set TASK_NAME=StockDashboard_DailyCollect
set SCRIPT_DIR=%~dp0
set BAT_PATH=%SCRIPT_DIR%daily_collect.bat
set SCHEDULE_TIME=18:00

REM Check if running as admin
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Administrator privileges required.
    echo Right-click this script and select "Run as administrator".
    pause
    exit /b 1
)

REM Verify daily_collect.bat exists
if not exist "%BAT_PATH%" (
    echo ERROR: daily_collect.bat not found at %BAT_PATH%
    pause
    exit /b 1
)

echo Registering scheduled task: %TASK_NAME%
echo   Schedule: Daily at %SCHEDULE_TIME%
echo   Script: %BAT_PATH%
echo.

REM Delete existing task if present (ignore errors)
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Create new scheduled task
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%BAT_PATH%\"" ^
    /sc daily ^
    /st %SCHEDULE_TIME% ^
    /rl HIGHEST ^
    /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Task registered successfully.
    echo.
    echo Useful commands:
    echo   schtasks /query /tn "%TASK_NAME%" /v    -- View task details
    echo   schtasks /run /tn "%TASK_NAME%"          -- Run now (manual)
    echo   schtasks /delete /tn "%TASK_NAME%" /f    -- Remove task
) else (
    echo.
    echo ERROR: Failed to register task.
)

echo.
pause
endlocal
