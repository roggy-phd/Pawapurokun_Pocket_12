@echo off
cd /d "%~dp0"
py -3 pp12_pennant_stats.py
if errorlevel 1 (
  echo.
  echo Python could not start or an error occurred.
  pause
)
