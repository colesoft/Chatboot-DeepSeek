@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Instalacija DeepSeek Assistant - zavisnosti
cd /d "%~dp0"

echo.
echo   Instaliram potrebne zavisnosti...
echo.

REM ---------- 1. Pronadji Python (pip ne mora biti u PATH-u!) ----------
set "PYTHON_CMD="

py -3 -c "import sys" >nul 2>&1
if !ERRORLEVEL! EQU 0 set "PYTHON_CMD=py -3"

if not defined PYTHON_CMD (
    python -c "import sys" >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    python3 -c "import sys" >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "PYTHON_CMD=python3"
)

REM ---------- 1b. Ako nije u PATH-u, trazi u standardnim folderima ----------
if not defined PYTHON_CMD (
    for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        if exist "%%d\python.exe" set PYTHON_CMD="%%d\python.exe"
    )
)
if not defined PYTHON_CMD (
    for /d %%d in ("%ProgramFiles%\Python3*") do (
        if exist "%%d\python.exe" set PYTHON_CMD="%%d\python.exe"
    )
)
if not defined PYTHON_CMD (
    for /d %%d in ("C:\Python3*") do (
        if exist "%%d\python.exe" set PYTHON_CMD="%%d\python.exe"
    )
)

REM ---------- 1c. Nema Pythona -> ponudi automatsku instalaciju ----------
if not defined PYTHON_CMD (
    echo   [!] Python nije pronadjen na ovom racunaru.
    echo.
    echo       Mogu da ga instaliram automatski - potrebna je
    echo       internet veza i oko 2 minuta.
    echo.
    choice /c DN /n /m "  Instalirati Python automatski? [D/N] "
    if !ERRORLEVEL! EQU 2 goto :manual_python
    echo.

    REM --- pokusaj 1: winget (Win10 1809+ / Win11) ---
    where winget >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo   Instaliram Python preko winget-a...
        winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements --silent
    ) else (
        echo   winget nije dostupan - prelazim na direktan download.
    )

    REM --- pokusaj 2: direktan download zvanicnog instalera ---
    if not exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        if not exist "%ProgramFiles%\Python312\python.exe" (
            where curl >nul 2>&1
            if !ERRORLEVEL! EQU 0 (
                echo   Preuzimam Python 3.12.8 instaler...
                curl -L --fail -o "%TEMP%\python-installer.exe" "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
                if exist "%TEMP%\python-installer.exe" (
                    echo   Instaliram (moze da potraje 1-2 min, bez dijaloga)...
                    start /wait "" "%TEMP%\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1 Include_test=0
                    del /q "%TEMP%\python-installer.exe" >nul 2>&1
                )
            ) else (
                echo   curl nije dostupan - automatski download nije moguc.
            )
        )
    )

    REM --- ponovna detekcija posle instalacije ---
    py -3 -c "import sys" >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "PYTHON_CMD=py -3"

    if not defined PYTHON_CMD (
        python -c "import sys" >nul 2>&1
        if !ERRORLEVEL! EQU 0 set "PYTHON_CMD=python"
    )
    if not defined PYTHON_CMD (
        for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
            if exist "%%d\python.exe" set PYTHON_CMD="%%d\python.exe"
        )
    )
    if not defined PYTHON_CMD (
        for /d %%d in ("%ProgramFiles%\Python3*") do (
            if exist "%%d\python.exe" set PYTHON_CMD="%%d\python.exe"
        )
    )
    echo.
)

if not defined PYTHON_CMD goto :manual_python

for /f "delims=" %%v in ('!PYTHON_CMD! -c "import sys;print(sys.version.split()[0])"') do set "PYVER=%%v"
echo   Python: !PYVER!   (komanda: !PYTHON_CMD!)

goto :after_manual_python

:manual_python
echo   [X] Python nije pronadjen / nije uspeo da se instalira.
echo.
echo   Rucna instalacija:
echo     1) Otvori https://www.python.org/downloads/
echo     2) Skini "Windows installer (64-bit)" za Python 3.12
echo     3) Pri instalaciji OBAVEZNO stikliraj:
echo          [x] Add python.exe to PATH
echo          [x] py launcher
echo     4) Zatvori ovaj prozor i ponovo pokreni install_deps.bat
echo.
pause
exit /b 1

:after_manual_python
echo.

REM ---------- 2. Proveri pip modul; ako ne postoji -> ensurepip ----------
!PYTHON_CMD! -m pip --version >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo   pip nije instaliran - pokrecem ensurepip...
    !PYTHON_CMD! -m ensurepip --upgrade
    if !ERRORLEVEL! NEQ 0 (
        echo   [X] Ne mogu da instaliram pip.
        echo       Pokreni rucno: !PYTHON_CMD! -m ensurepip --upgrade
        pause
        exit /b 1
    )
)

echo   Azuriram pip...
!PYTHON_CMD! -m pip install --upgrade pip --quiet --disable-pip-version-check 2>nul

REM ---------- 3. Instaliraj PyQt5 ----------
echo.
echo   PyQt5 (GUI biblioteka)...
!PYTHON_CMD! -m pip install "PyQt5>=5.15.0"
if !ERRORLEVEL! NEQ 0 (
    echo   Pokusavam ponovo sa only-binary...
    !PYTHON_CMD! -m pip install "PyQt5>=5.15.0" --only-binary :all:
    if !ERRORLEVEL! NEQ 0 (
        echo.
        echo   [X] Greska pri instalaciji PyQt5!
        echo       Pokreni rucno: !PYTHON_CMD! -m pip install PyQt5
        pause
        exit /b 1
    )
)

REM ---------- 4. Opciono ----------
echo.
echo   requests (opciono)...
!PYTHON_CMD! -m pip install requests --quiet --disable-pip-version-check 2>nul

echo.
echo   [OK] Zavisnosti uspesno instalirane!
echo.
echo   Sada mozes pokrenuti aplikaciju preko run.bat
echo.
pause
endlocal