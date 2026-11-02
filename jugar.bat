@echo off
REM Lanza Astro Recolector (instala Pygame si hace falta).
cd /d "%~dp0"
set PY=
where py >nul 2>nul && set PY=py -3
if "%PY%"=="" ( where python >nul 2>nul && set PY=python )
if "%PY%"=="" ( echo Instala Python desde https://www.python.org/downloads/ & pause & exit /b 1 )
%PY% -c "import pygame" >nul 2>nul || %PY% -m pip install -r requirements.txt
%PY% main.py
if errorlevel 1 pause
