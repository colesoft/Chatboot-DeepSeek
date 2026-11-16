@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title DeepSeek Code Assistant - instalacija zavisnosti
cd /d "%~dp0"

set "QUIET=0"
if /i "%~1"=="/quiet" set "QUIET=1"

echo.
echo   Instaliram potrebne zavisnosti...
echo.

set "PYTHON_CMD="
call :find_python
if defined PYTHON_CMD goto :have_python

echo   [!] Python nije pronadjen na ovom racunaru.
echo.
echo       Mogu da ga instaliram automatski.
echo       Potrebna je internet veza i oko 2 minuta.
echo.
choice /c DN /n /m "  Instalirati Python automatski? [D/N] "
if errorlevel 2 goto :manual_python
echo.

call :auto_install_python
set "PYTHON_CMD="
call :find_python
if defined PYTHON_CMD goto :have_python

:manual_python
echo.
echo   [X] Python nije pronadjen ili instalacija nije uspela.
echo.
echo   Rucna instalacija:
echo     1. Otvori https://www.python.org/downloads/
echo     2. Skini Windows installer 64-bit za Python 3.12
echo     3. Pri instalaciji OBAVEZNO stikliraj:
echo          [x] Add python.exe to PATH
echo          [x] py launcher
echo     4. Zatvori ovaj prozor i ponovo pokreni INSTALL.bat
echo.
pause
exit /b 1

:have_python
for /f "delims=" %%v in ('!PYTHON_CMD! -c "import sys;print(sys.version.split()[0])"') do set "PYVER=%%v"
echo   Python: !PYVER!
echo   Komanda: !PYTHON_CMD!
echo.

REM ---------- pip modul ----------
!PYTHON_CMD! -m pip --version >nul 2>&1
if !ERRORLEVEL! EQU 0 goto :pip_ok
echo   pip nije instaliran - pokrecem ensurepip...
!PYTHON_CMD! -m ensurepip --upgrade
if !ERRORLEVEL! NEQ 0 goto :err_pip
:pip_ok

echo   Azuriram pip...
!PYTHON_CMD! -m pip install --upgrade pip --quiet --disable-pip-version-check 2>nul

REM ---------- PyQt5 ----------
echo.
echo   Instaliram PyQt5...
!PYTHON_CMD! -m pip install "PyQt5>=5.15.0"
if !ERRORLEVEL! EQU 0 goto :pyqt5_ok
echo.
echo   Prvi pokusaj nije uspeo - probam samo binary pakete...
!PYTHON_CMD! -m pip install "PyQt5>=5.15.0" --only-binary :all:
if !ERRORLEVEL! EQU 0 goto :pyqt5_ok
echo.
echo   [X] Greska pri instalaciji PyQt5!
echo       Pokreni rucno: !PYTHON_CMD! -m pip install PyQt5
echo.
pause
exit /b 1
:pyqt5_ok

REM ---------- requests ----------
echo.
echo   Instaliram requests - opciono...
!PYTHON_CMD! -m pip install requests --quiet --disable-pip-version-check 2>nul

echo.
echo   [OK] Zavisnosti uspesno instalirane!
echo.
if "!QUIET!"=="1" exit /b 0
pause
exit /b 0

:err_pip
echo.
echo   [X] Ne mogu da instaliram pip.
echo       Pokreni rucno: !PYTHON_CMD! -m ensurepip --upgrade
echo.
pause
exit /b 1

REM =========================================================
REM  SUBROUTINE: pronadji Python
REM =========================================================
:find_python
py -3 -c "import sys" >nul 2>&1
if !ERRORLEVEL! EQU 0 set "PYTHON_CMD=py -3"
if defined PYTHON_CMD goto :eof

python -c "import sys" >nul 2>&1
if !ERRORLEVEL! EQU 0 set "PYTHON_CMD=python"
if defined PYTHON_CMD goto :eof

python3 -c "import sys" >nul 2>&1
if !ERRORLEVEL! EQU 0 set "PYTHON_CMD=python3"
if defined PYTHON_CMD goto :eof

call :scan_python_dirs
goto :eof

REM =========================================================
REM  SUBROUTINE: trazi python.exe u standardnim folderima
REM =========================================================
:scan_python_dirs
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python3*") do call :try_pydir "%%d"
if defined PYTHON_CMD goto :eof
for /d %%d in ("%ProgramFiles%\Python3*") do call :try_pydir "%%d"
if defined PYTHON_CMD goto :eof
for /d %%d in ("%ProgramFiles(x86)%\Python3*") do call :try_pydir "%%d"
if defined PYTHON_CMD goto :eof
for /d %%d in ("C:\Python3*") do call :try_pydir "%%d"
goto :eof

:try_pydir
if defined PYTHON_CMD goto :eof
if not exist "%~1\python.exe" goto :eof
set "PYTHON_CMD=%~1\python.exe"
goto :eof

REM =========================================================
REM  SUBROUTINE: automatska instalacija Pythona
REM =========================================================
:auto_install_python
where winget >nul 2>&1
if !ERRORLEVEL! NEQ 0 goto :aip_download

echo   Instaliram Python preko winget-a...
winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements --silent
if !ERRORLEVEL! EQU 0 goto :aip_done
echo   winget nije uspeo - prelazim na direktan download.
echo.

:aip_download
where curl >nul 2>&1
if !ERRORLEVEL! NEQ 0 goto :aip_nocurl

echo   Preuzimam Python 3.12.8 instaler, oko 25 MB...
curl -L --fail -o "%TEMP%\python-installer.exe" "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
if not exist "%TEMP%\python-installer.exe" goto :aip_nocurl

echo   Instaliram Python - moze da potraje 1 do 2 minuta.
echo   Molim sacekaj, ne zatvaraj ovaj prozor.
start /wait "" "%TEMP%\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1 Include_test=0
del /q "%TEMP%\python-installer.exe" >nul 2>&1
echo   Instalacija Pythona zavrsena.
goto :aip_done

:aip_nocurl
echo   Automatski download nije moguc - nema curl ili nema interneta.
echo.

:aip_done
goto :eof
