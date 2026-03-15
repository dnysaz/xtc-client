@echo off
:: ─────────────────────────────────────────────────────────────
:: XtermChat — Windows Installer
:: install.bat
::
:: Usage:
::   Double-click install.bat
::   OR run in Command Prompt / PowerShell:
::   .\install.bat
:: ─────────────────────────────────────────────────────────────

title XtermChat Installer
color 0B

echo.
echo  ┌──────────────────────────────────────┐
echo  │   XTERMCHAT  ·  WINDOWS INSTALLER    │
echo  └──────────────────────────────────────┘
echo.

:: ── Check Python ─────────────────────────────────────────────
echo  [*] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] Python not found.
    echo      Download from: https://python.org
    echo      Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYVER=%%i
echo  [OK] %PYVER% found.

:: ── Install Python dependencies ───────────────────────────────
echo.
echo  [*] Installing Python dependencies...
pip install --quiet prompt_toolkit requests flask
if %errorlevel% neq 0 (
    echo  [!] pip install failed. Try running as Administrator.
    pause
    exit /b 1
)
echo  [OK] Dependencies installed: prompt_toolkit, requests, flask

:: ── Check Windows Terminal ────────────────────────────────────
echo.
echo  [*] Checking Windows Terminal...
where wt >nul 2>&1
if %errorlevel% equ 0 (
    echo  [OK] Windows Terminal found.
) else (
    echo  [!] Windows Terminal not found.
    echo      Recommended for best emoji and Unicode support.
    echo      Install from Microsoft Store: "Windows Terminal"
    echo      You can continue without it, but display may vary.
)

:: ── Create xtc.bat wrapper ────────────────────────────────────
echo.
echo  [*] Creating xtc command...

:: Dapatkan path folder ini (xtc-client)
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
set XTC_SCRIPT=%SCRIPT_DIR%\xtc.py

:: Buat xtc.bat di folder yang sama
echo @echo off > "%SCRIPT_DIR%\xtc.bat"
echo python "%XTC_SCRIPT%" %%* >> "%SCRIPT_DIR%\xtc.bat"

echo  [OK] Created: %SCRIPT_DIR%\xtc.bat

:: ── Tambahkan ke PATH (user-level, tidak perlu admin) ─────────
echo.
echo  [*] Adding to PATH...

:: Cek apakah sudah ada di PATH
echo %PATH% | findstr /i "%SCRIPT_DIR%" >nul 2>&1
if %errorlevel% equ 0 (
    echo  [OK] Already in PATH.
) else (
    :: Tambahkan ke user PATH (persistent, tidak perlu admin)
    setx PATH "%PATH%;%SCRIPT_DIR%" >nul 2>&1
    if %errorlevel% equ 0 (
        echo  [OK] Added to PATH. Restart terminal to apply.
    ) else (
        echo  [!] Could not add to PATH automatically.
        echo      Add this folder to PATH manually:
        echo      %SCRIPT_DIR%
    )
)

:: ── Clipboard support ─────────────────────────────────────────
echo.
echo  [*] Checking clipboard support...
where clip >nul 2>&1
if %errorlevel% equ 0 (
    echo  [OK] clip.exe found ^(Windows built-in^) — copy feature ready.
) else (
    echo  [!] clip.exe not found ^(unusual^). Copy feature may not work.
)

:: ── Done ─────────────────────────────────────────────────────
echo.
echo  ┌──────────────────────────────────────┐
echo  │   DONE! XtermChat is ready.          │
echo  └──────────────────────────────────────┘
echo.
echo  Run in a NEW terminal window:
echo.
echo    xtc connect @your-server-ip:8080
echo    xtc status
echo    xtc start:chat @general
echo.
echo  Or if PATH not applied yet, run directly:
echo.
echo    python xtc.py connect @your-server-ip:8080
echo.
pause