@echo off
rem Leeravontuur starten op Windows: dubbelklik op dit bestand.
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py leeravontuur.py %*
) else (
    python leeravontuur.py %*
)
if errorlevel 9009 echo Python is niet gevonden. Installeer Python 3.10 of nieuwer: zie README.md.
if errorlevel 1 pause
