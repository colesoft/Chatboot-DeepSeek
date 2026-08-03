@echo off
title Git Push - DeepSeek Chatbot
setlocal enabledelayedexpansion
color 0B

echo.
echo   =============================================
echo    Git Push - DeepSeek Chatbot
echo   =============================================
echo.

:: === 1) PITAJ ZA OPIS IZMENE ===
set /p COMMIT_MSG="Opis izmene (Enter za auto): "
if not "!COMMIT_MSG!"=="" goto :skip_date
for /f %%I in ('powershell -Command "Get-Date -Format yyyy-MM-dd"') do set COMMIT_MSG=Update %%I
:skip_date

:: === 2) DODAJ SVE ===
echo.
echo Dodajem fajlove...
git add -A
if errorlevel 1 goto :err_add

:: === 3) PROVERI STA SE MENJA ===
git status --short
echo.

:: === 4) COMMIT ===
echo Commit: "!COMMIT_MSG!"
git commit -m "!COMMIT_MSG!"
if errorlevel 1 goto :no_changes

echo.
echo Commit uspeo!
goto :do_push

:no_changes
echo.
echo Nema izmena za commit - sve je vec na GitHub-u!
pause
exit /b 0

:err_add
echo.
echo Greska pri dodavanju fajlova!
pause
exit /b 1

:: === 5) PUSH ===
:do_push
echo.
echo Push na GitHub...
git push origin main
if errorlevel 1 goto :err_push

echo.
echo Push uspeo! Sve je na GitHub-u!
pause
exit /b 0

:err_push
echo.
echo Push nije uspeo! Proveri internet ili kredencijale.
pause
exit /b 1

endlocal
