@echo off
title Instalacija DeepSeek Assistant - zavisnosti

echo.
echo   ⏳ Instaliram potrebne zavisnosti...
echo.
echo   PyQt5 (GUI biblioteka)...
pip install PyQt5
if %ERRORLEVEL% NEQ 0 (
    echo   ❌ Greska pri instalaciji PyQt5!
    pause
    exit /b 1
)

echo.
echo   ✅ Zavisnosti uspesno instalirane!
echo.
echo   Sada mozes pokrenuti aplikaciju preko run.bat
echo.
pause