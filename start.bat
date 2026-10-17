@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
  echo Python launcher not found. Install Python 3 from python.org with the py launcher.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv || goto error
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto error
".venv\Scripts\python.exe" ut99_presence.py
pause
exit /b
:error
echo Setup failed. Check Python installation and internet connection.
pause
exit /b 1
