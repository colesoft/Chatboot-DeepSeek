@echo off
title DeepSeek Chatbot - Instalacija i pokretanje
setlocal enabledelayedexpansion

color 0B

echo.
echo   =============================================
echo    🤖 DeepSeek Chatbot - Pametni AI Asistent
echo   =============================================
echo.

:: === MINIMALNA PYTHON VERZIJA ===
set MIN_PY_MAJOR=3
set MIN_PY_MINOR=9

:: === PRONAĐI PYTHON ===
set PYTHON_CMD=

:: Prvo probaj py launcher (najbolji izbor na Windows)
py --version >nul 2>nul
if !ERRORLEVEL! EQU 0 (
    for /f "tokens=2" %%V in ('py --version') do set PY_VER=%%V
    for /f "tokens=1,2 delims=." %%a in ("!PY_VER!") do (
        if %%a GEQ !MIN_PY_MAJOR! if %%b GEQ !MIN_PY_MINOR! (
            set PYTHON_CMD=py -3
        )
    )
)

:: Ako py nije našao, probaj python
if "!PYTHON_CMD!"=="" (
    python --version >nul 2>nul
    if !ERRORLEVEL! EQU 0 (
        for /f "tokens=2" %%V in ('python --version') do set PY_VER=%%V
        for /f "tokens=1,2 delims=." %%a in ("!PY_VER!") do (
            if %%a GEQ !MIN_PY_MAJOR! if %%b GEQ !MIN_PY_MINOR! (
                set PYTHON_CMD=python
            )
        )
    )
)

:: Ako nije pronađen, ponudi preuzimanje
if "!PYTHON_CMD!"=="" (
    echo   ❌ Nije pronađen Python !MIN_PY_MAJOR!.!MIN_PY_MINOR!+ na sistemu.
    echo.
    echo   Da li zelis da preuzmes i instaliras Python automatski?
    echo.
    set /p INSTALL_PY="   (D/n): "
    if /i "!INSTALL_PY!"=="" set INSTALL_PY=D
    if /i "!INSTALL_PY!"=="d" (
        echo.
        echo   ⬇️ Preuzimam Python !MIN_PY_MAJOR!.!MIN_PY_MINOR! (64-bit)...
        echo.
        
        :: Proveri da li je Windows 64-bit
        wmic os get osarchitecture | find "64" >nul 2>nul
        if !ERRORLEVEL! EQU 0 (
            set PY_URL=https://www.python.org/ftp/python/3.12.5/python-3.12.5-amd64.exe
        ) else (
            set PY_URL=https://www.python.org/ftp/python/3.12.5/python-3.12.5.exe
        )
        
        echo   URL: !PY_URL!
        echo.
        
        :: Skini Python installer pomocu PowerShell-a
        echo   ⏳ Preuzimam...
        powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '!PY_URL!' -OutFile '%TEMP%\python_installer.exe' }"
        
        if not exist "%TEMP%\python_installer.exe" (
            echo   ❌ Preuzimanje nije uspelo!
            echo.
            echo   Molim te, skini Python rucno sa:
            echo   https://www.python.org/downloads/
            echo.
            pause
            exit /b 1
        ) else (
            echo   ✅ Preuzeto! Pokrecem instalaciju...
            echo.
            echo   ⚠️ Instalacija je automatska - ne moras nista da radis.
            echo   Samo sacekaj da se instalira...
            echo.
            
            :: Instaliraj Python (tiche mod, dodaj u PATH)
            start /wait "" "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0 Include_tcltk=0 Include_launcher=1 SimpleInstall=1
            
            :: Sačekaj da se instalira
            timeout /t 3 /nobreak >nul
            
            :: Probaj ponovo da nadješ python
            py --version >nul 2>nul
            if !ERRORLEVEL! EQU 0 (
                set PYTHON_CMD=py -3
                echo   ✅ Python uspesno instaliran!
            ) else (
                python --version >nul 2>nul
                if !ERRORLEVEL! EQU 0 (
                    set PYTHON_CMD=python
                    echo   ✅ Python uspesno instaliran!
                ) else (
                    echo   ❌ Instalacija nije uspela!
                    echo.
                    echo   Molim te, instaliraj Python rucno sa:
                    echo   https://www.python.org/downloads/
                    echo.
                    pause
                    exit /b 1
                )
            )
        )
    ) else (
        echo.
        echo   ⚠️ Ne mogu da nastavim bez Python-a.
        echo   Preuzmi ga sa: https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
)

echo   ✅ Python pronađen: !PYTHON_CMD!
echo.

:: === INSTALACIJA BIBLIOTEKA ===

:: Ažuriraj pip
echo   ⚙️ Azuriram pip...
"!PYTHON_CMD!" -m pip install --upgrade pip --quiet 2>nul

:: Instaliraj PyQt5 (samo binary, bez build-a)
echo   📦 Proveravam PyQt5...
"!PYTHON_CMD!" -c "import PyQt5" >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo   ⚠️ PyQt5 nije instaliran. Instaliram...
    "!PYTHON_CMD!" -m pip install PyQt5 --quiet
    if !ERRORLEVEL! NEQ 0 (
        echo   ❌ Instalacija PyQt5 nije uspela!
        echo   Probam alternativni nacin (samo binary)...
        "!PYTHON_CMD!" -m pip install PyQt5 --only-binary :all: --quiet
        if !ERRORLEVEL! NEQ 0 (
            echo   ❌ Instalacija i dalje neuspesna.
            echo   Rucno pokreni: !PYTHON_CMD! -m pip install PyQt5
            echo.
            pause
            exit /b 1
        )
    )
    echo   ✅ PyQt5 instaliran.
) else (
    echo   ✅ PyQt5 vec instaliran.
)

:: Instaliraj requests
"!PYTHON_CMD!" -c "import requests" >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo   ⚠️ requests nije instaliran. Instaliram...
    "!PYTHON_CMD!" -m pip install requests --quiet
    if !ERRORLEVEL! NEQ 0 (
        echo   ❌ Instalacija requests nije uspela!
        echo   Rucno pokreni: !PYTHON_CMD! -m pip install requests
        echo.
        pause
        exit /b 1
    )
    echo   ✅ requests instaliran.
) else (
    echo   ✅ requests vec instaliran.
)

echo.
echo   =============================================
echo    🚀 Pokrecem DeepSeek Chatbot...
echo   =============================================
echo.

:: === POKRENI APLIKACIJU ===
"!PYTHON_CMD!" main.py

if !ERRORLEVEL! NEQ 0 (
    echo.
    echo   ❌ Doslo je do greske.
    echo.
    pause
)

endlocal