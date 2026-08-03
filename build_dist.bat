@echo off
title Build DeepSeek Chatbot Distribution
setlocal enabledelayedexpansion
color 0B

echo.
echo   =============================================
echo    🚀 DeepSeek Chatbot - Build Distribution
echo   =============================================
echo.

:: === KONFIGURACIJA ===
set APP_NAME=DeepSeek Chatbot
set DIST_DIR=%CD%\dist
set BUILD_DIR=%CD%\build_temp
set ICO_FILE=%CD%\deepseek.ico

:: === 1. Provera ikonice ===
echo   [1/6] Provera ikonice...
if not exist "%ICO_FILE%" (
    echo   ❌ Ikonica ne postoji! Pokreni create_icon.py.
    pause
    exit /b 1
)
echo   ✅ Ikonica: %ICO_FILE%
echo.

:: === 2. Provera fajlova ===
echo   [2/6] Provera fajlova za distribuciju...
set FILES=deepseek_chatbot.py run.bat deepseek.ico requirements.txt README.md LICENSE .gitignore
for %%f in (%FILES%) do (
    if not exist "%CD%\%%f" (
        echo   ❌ Nedostaje: %%f
        set MISSING=1
    ) else (
        echo   ✅ %%f
    )
)
if defined MISSING (
    echo.
    pause
    exit /b 1
)
echo.

:: === 3. Priprema build foldera ===
echo   [3/6] Kopiranje fajlova...

if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%" 2>nul
if not exist "%BUILD_DIR%\%APP_NAME%" mkdir "%BUILD_DIR%\%APP_NAME%"

for %%f in (%FILES%) do (
    copy /Y "%CD%\%%f" "%BUILD_DIR%\%APP_NAME%\%%f" >nul
    echo   📄 %%f
)
copy /Y "%CD%\create_icon.py" "%BUILD_DIR%\%APP_NAME%\create_icon.py" >nul 2>nul
echo   📄 create_icon.py
echo.

:: === 4. Pravljenje ZIP arhive ===
echo   [4/6] Pravljenje ZIP portable verzije...

if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"

set ZIP_FILE=%DIST_DIR%\%APP_NAME%_Portable.zip
if exist "%ZIP_FILE%" del "%ZIP_FILE%"

powershell -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory('%BUILD_DIR%\%APP_NAME%', '%ZIP_FILE%', [System.IO.Compression.CompressionLevel]::Optimal, $false); Write-Host 'OK'"

if not exist "%ZIP_FILE%" (
    echo   ❌ Greska pri pravljenju ZIP-a!
    pause
    exit /b 1
)

for %%F in ("%ZIP_FILE%") do (
    set ZIP_SIZE=%%~zF
    set /A "ZIP_SIZE_KB=!ZIP_SIZE! / 1024"
)
echo   ✅ ZIP: %ZIP_FILE% (!ZIP_SIZE_KB! KB)
echo.

:: === 5. Probaj da napravis SFX (ako ima 7z) ===
echo   [5/6] Provera 7-Zip za SFX...

set SEVENZIP=
if exist "C:\Program Files\7-Zip\7z.exe" set SEVENZIP=C:\Program Files\7-Zip\7z.exe
if exist "C:\Program Files (x86)\7-Zip\7z.exe" set SEVENZIP=C:\Program Files (x86)\7-Zip\7z.exe

if not defined SEVENZIP (
    echo   ⚠️ 7-Zip nije instaliran - pravim samo ZIP
    echo   Za SFX installer, instaliraj 7-Zip pa pokreni ponovo.
    goto :skip_sfx
)

echo   ✅ 7z pronadjen: %SEVENZIP%
echo.
echo   [6/6] Pravljenje SFX instalera...

:: Napravi 7z arhivu
"%SEVENZIP%" a -t7z -mx=9 "%DIST_DIR%\deepseek.7z" "%BUILD_DIR%\%APP_NAME%\*" >nul 2>nul

:: Pronadji SFX modul
set SFX_MODULE=
for %%p in ("C:\Program Files\7-Zip\7z.sfx" "C:\Program Files (x86)\7-Zip\7z.sfx") do (
    if exist %%p set SFX_MODULE=%%p
)
for %%p in ("C:\Program Files\7-Zip\7zSD.sfx" "C:\Program Files (x86)\7-Zip\7zSD.sfx") do (
    if exist %%p set SFX_MODULE=%%p
)

if not defined SFX_MODULE (
    echo   ⚠️ SFX modul nije pronadjen!
    goto :skip_sfx
)

echo   ✅ SFX modul: %SFX_MODULE%

:: Konfiguracija
(
    echo ; SFX konfiguracija za %APP_NAME%
    echo Title=%APP_NAME%
    echo BeginPrompt=Instalacija %APP_NAME% asistenta
    echo FinishPrompt=Aplikacija je spremna! Pokreni?
    echo ExtractPath=%%USERPROFILE%%\Desktop\%APP_NAME%
    echo ExtractPathTitle=Odaberi destinaciju
    echo ExtractPathText=Gde zelis da instaliras?
    echo RunProgram=run.bat
    echo OverwriteMode=a
) > "%BUILD_DIR%\sfx_config.txt"

:: Spoji SFX + config + 7z
copy /B "%SFX_MODULE%" + "%BUILD_DIR%\sfx_config.txt" + "%DIST_DIR%\deepseek.7z" "%DIST_DIR%\%APP_NAME%_Setup.exe" >nul

if exist "%DIST_DIR%\%APP_NAME%_Setup.exe" (
    for %%F in ("%DIST_DIR%\%APP_NAME%_Setup.exe") do (
        set EXE_SIZE=%%~zF
        set /A "EXE_SIZE_MB=!EXE_SIZE! / 1048576"
    )
    echo   ✅ SFX: %DIST_DIR%\%APP_NAME%_Setup.exe (!EXE_SIZE_MB! MB)
    
    :: Dodaj ikonu ako imamo Resource Hacker
    if exist "%CD%\reshacker.exe" (
        "%CD%\reshacker.exe" -add "%DIST_DIR%\%APP_NAME%_Setup.exe", "%DIST_DIR%\%APP_NAME%_Setup.exe", "%ICO_FILE%", ICONGROUP, MAINICON, 0
        echo   🎨 Ikonica dodata!
    ) else (
        echo   ⚠️ Resource Hacker nije pronadjen
        echo   Skini ga: http://www.angusj.com/resourcehacker/
    )
) else (
    echo   ❌ Greska pri pravljenju SFX!
)

:skip_sfx

:: Skip ako nemamo 7z
:skip_sfx
echo.
echo   🧹 Cistim temp...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"

echo.
echo   =============================================
echo    ✅ DISTRIBUCIJA KREIRANA!
echo   =============================================
echo.
echo   📁 Izlazni folder: %DIST_DIR%
echo.
dir "%DIST_DIR%" /o:s
echo.
echo   🚀 Pokreni Setup.exe da instaliras aplikaciju!
echo.
pause
endlocal
