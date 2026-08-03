@echo off
title Git Push - DeepSeek Chatbot
setlocal enabledelayedexpansion
color 0B

echo.
echo   =============================================
echo    🚀 Git Push - DeepSeek Chatbot
echo   =============================================
echo.

:: === 1) PITAJ ZA OPIS IZMENE ===
set /p COMMIT_MSG="   Opis izmene (Enter za auto): "
if "!COMMIT_MSG!"=="" (
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value ^| find "="') do set DT=%%I
    set COMMIT_MSG=Update !DT:~8,2!.!DT:~5,2!.!DT:~0,4! - !DT:~2,2!:!DT:~4,2!
)

:: === 2) DODAJ SVE ===
echo.
echo   📦 Dodajem fajlove...
git add -A
if errorlevel 1 (
    echo   ❌ Greska pri dodavanju!
    pause
    exit /b 1
)

:: === 3) PROVERI STA SE MENJA ===
git status --short
echo.

:: === 4) COMMIT ===
echo   ✏️  Commit: "!COMMIT_MSG!"
git commit -m "!COMMIT_MSG!" 2>nul
if errorlevel 1 (
    :: Ako nema promena, commit ne uspe - to je OK
    echo   ℹ️  Nema izmena za commit (ili nista novo).
) else (
    echo   ✅ Commit uspeo!
)

:: === 5) PUSH ===
echo.
echo   📤 Push na GitHub...
git push origin main
if errorlevel 1 (
    echo.
    echo   ❌ Push nije uspeo!
    echo   Proveri internet ili kredencijale.
) else (
    echo.
    echo   ✅ Push uspeo! Sve je na GitHub-u!
)

echo.
pause
endlocal
