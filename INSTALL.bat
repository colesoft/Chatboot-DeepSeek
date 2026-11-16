@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title DeepSeek Code Assistant - Instalacija
cd /d "%~dp0"

echo.
echo   ============================================
echo    DeepSeek Code Assistant - Instalacija
echo   ============================================
echo.
echo   1/3  Provera i instalacija zavisnosti...
echo.

call "%~dp0install_deps.bat"
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo   [X] Instalacija zavisnosti nije uspela.
    echo       Pokreni rucno: install_deps.bat
    echo.
    pause
    exit /b 1
)

echo.
echo   2/3  Pravim precicu na Desktopu...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s=(New-Object -ComObject WScript.Shell); $lnk=$s.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\DeepSeek Code Assistant.lnk'); $lnk.TargetPath='%~dp0DeepSeek Chatbot.vbs'; $lnk.WorkingDirectory='%~dp0'; $lnk.IconLocation='%~dp0deepseek.ico'; $lnk.Description='DeepSeek Code Assistant'; $lnk.Save()" >nul 2>&1
if exist "%USERPROFILE%\Desktop\DeepSeek Code Assistant.lnk" (
    echo         [OK] Precica napravljena na Desktopu.
) else (
    echo         [-] Precica nije napravljena (nije kriticno).
)

echo.
echo   3/3  Pokrecem aplikaciju...
echo.
start "" "%~dp0DeepSeek Chatbot.vbs"

echo   ============================================
echo    Instalacija zavrsena!
echo   ============================================
echo.
echo    Aplikaciju pokreces:
echo      - precica "DeepSeek Code Assistant" na Desktopu
echo      - ili dvoklik na "DeepSeek Chatbot.vbs"
echo      - ili run.bat
echo.
timeout /t 5 >nul
endlocal
exit /b 0
