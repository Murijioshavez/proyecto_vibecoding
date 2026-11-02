@echo off
REM Instala dependencias, ejecuta las pruebas y genera capturas reales.
REM Todos los resultados se guardan en la carpeta evidencias\
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
if not exist evidencias mkdir evidencias
set PY=
where py >nul 2>nul && set PY=py -3
if "%PY%"=="" ( where python >nul 2>nul && set PY=python )
if "%PY%"=="" (
  echo No se encontro Python. Instalalo desde https://www.python.org/downloads/ > evidencias\log_windows.txt
  echo No se encontro Python. Instalalo desde https://www.python.org/downloads/
  pause
  exit /b 1
)
echo ==== Entorno ==== > evidencias\log_windows.txt
%PY% -c "import sys, platform; print(sys.version); print(platform.platform())" >> evidencias\log_windows.txt 2>&1
echo ==== pip install -r requirements.txt ==== >> evidencias\log_windows.txt
%PY% -m pip install -r requirements.txt >> evidencias\log_windows.txt 2>&1
echo ==== pytest ==== >> evidencias\log_windows.txt
%PY% -m pytest -v -rs > evidencias\resultado_pruebas_windows.txt 2>&1
echo codigo de salida pytest: %ERRORLEVEL% >> evidencias\resultado_pruebas_windows.txt
echo ==== prueba de humo ==== >> evidencias\log_windows.txt
%PY% main.py --prueba-humo 900 >> evidencias\log_windows.txt 2>&1
echo ==== capturas ==== >> evidencias\log_windows.txt
%PY% main.py --capturas evidencias >> evidencias\log_windows.txt 2>&1
echo FIN >> evidencias\log_windows.txt
echo Terminado. Revisa la carpeta evidencias.
