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
if not "!COMMIT_MSG!"=="" goto :skip_date
for /f %%I in ('powershell -Command "Get-Date -Format yyyy-MM-dd"') do set COMMIT_MSG=Update %%I
:skip_date

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
git commit -m "!COMMIT_MSG!"
if errorlevel 1 (
    :: Ako nema promena, commit ne uspe - to je OK
    echo   ℹ️  Nema izmena za commit (ili nista novo).
    echo.
    echo   ✅ Sve je vec na GitHub-u!
    pause
    exit /b 0
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
