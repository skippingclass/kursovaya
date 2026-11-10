@echo off
cd /d "%~dp0"
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" run.py
) else (
    python run.py
)
if %ERRORLEVEL% NEQ 0 (
    pause
)
