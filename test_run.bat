@echo off
title DeepSeek Chatbot - TEST (brzo pokretanje)
setlocal enabledelayedexpansion
color 0A

echo.
echo   =============================================
echo    TEST POKRETANJE - DeepSeek Chatbot
echo   =============================================
echo.

cd /d "%~dp0"

:: === PRONADJI PYTHON ===
set PYTHON_CMD=
py --version >nul 2>nul
if !ERRORLEVEL! EQU 0 set PYTHON_CMD=py -3

if "!PYTHON_CMD!"=="" (
    python --version >nul 2>nul
    if !ERRORLEVEL! EQU 0 set PYTHON_CMD=python
)

if "!PYTHON_CMD!"=="" (
    echo   [X] Python nije pronadjen u PATH-u.
    echo       Instaliraj Python 3.9+ ili pokreni run.bat
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('!PYTHON_CMD! --version 2^>^&1') do set PY_VER_STR=%%v
echo   [OK] Python: !PY_VER_STR!  (komanda: !PYTHON_CMD!)

:: === PROVERA BIBLIOTEKA ===
echo.
echo   --- Provera biblioteka ---
!PYTHON_CMD! -c "import PyQt5" >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo   [!] PyQt5 NIJE instaliran - instaliram...
    !PYTHON_CMD! -m pip install PyQt5 --quiet
) else (
    echo   [OK] PyQt5
)

!PYTHON_CMD! -c "import requests" >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo   [!] requests NIJE instaliran - instaliram...
    !PYTHON_CMD! -m pip install requests --quiet
) else (
    echo   [OK] requests
)

:: === SYNTAX CHECK ===
echo.
echo   --- Sintaksna provera (py_compile) ---
!PYTHON_CMD! -m py_compile main.py deepseek_chatbot.py chatbot_app\__init__.py chatbot_app\config.py chatbot_app\api_client.py chatbot_app\api_tools.py chatbot_app\tools.py chatbot_app\history.py chatbot_app\i18n.py chatbot_app\logger.py chatbot_app\models_catalog.py chatbot_app\ocr.py chatbot_app\pricing.py chatbot_app\utils.py chatbot_app\vision.py chatbot_app\widgets.py chatbot_app\ui\__init__.py chatbot_app\ui\dialogs.py chatbot_app\ui\project_context.py chatbot_app\ui\theme.py
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo   [X] GRESKA U SINTAKSI! Vidi poruke gore.
    echo.
    pause
    exit /b 1
)
echo   [OK] Svi moduli se kompajliraju bez greske.

:: === POKRENI APLIKACIJU ===
echo.
echo   =============================================
echo    Pokrecem aplikaciju (console ostaje otvoren)...
echo   =============================================
echo.

!PYTHON_CMD! main.py
set APP_RC=!ERRORLEVEL!

echo.
if !APP_RC! NEQ 0 (
    echo   [X] Aplikacija se zatvorila sa greskom (exit code = !APP_RC!).
    echo       Kopiraj poruku gore ako ti treba pomoc.
) else (
    echo   [OK] Aplikacija se zatvorila normalno (exit code = 0).
)
echo.
pause
endlocal
