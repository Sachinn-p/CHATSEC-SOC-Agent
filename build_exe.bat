@echo off
REM ============================================================
REM  build_exe.bat – One-click Windows build for CHATSEC-SOC-Agent
REM
REM  Usage:
REM    build_exe.bat           – standard build
REM    build_exe.bat --clean   – remove previous build first
REM    build_exe.bat --help    – show all options
REM
REM  Requirements:
REM    - Python 3.10 or later must be on the PATH
REM    - Internet access to download PyInstaller if not present
REM ============================================================

SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

REM ── Working directory ──────────────────────────────────────
CD /D "%~dp0"

REM ── Banner ─────────────────────────────────────────────────
ECHO.
ECHO  =====================================================
ECHO   CHATSEC-SOC-Agent  ^|  Windows .EXE Build Script
ECHO  =====================================================
ECHO.

REM ── Python availability check ──────────────────────────────
WHERE python >NUL 2>&1
IF ERRORLEVEL 1 (
    ECHO [ERROR] Python was not found on the PATH.
    ECHO         Please install Python 3.10 or later from https://www.python.org/
    ECHO         and make sure "Add Python to PATH" is checked during installation.
    PAUSE
    EXIT /B 1
)

REM ── Python version check (requires 3.10+) ──────────────────
FOR /F "tokens=2 delims= " %%V IN ('python --version 2^>^&1') DO SET PY_VER=%%V
ECHO [INFO]  Python version: %PY_VER%

REM Extract major.minor for comparison
FOR /F "tokens=1,2 delims=." %%A IN ("%PY_VER%") DO (
    SET PY_MAJOR=%%A
    SET PY_MINOR=%%B
)

IF %PY_MAJOR% LSS 3 (
    ECHO [ERROR] Python 3.10 or later is required.
    PAUSE
    EXIT /B 1
)
IF %PY_MAJOR% EQU 3 IF %PY_MINOR% LSS 10 (
    ECHO [ERROR] Python 3.10 or later is required (found %PY_VER%).
    PAUSE
    EXIT /B 1
)

REM ── Upgrade pip (best-effort, non-fatal) ───────────────────
ECHO [INFO]  Upgrading pip…
python -m pip install --upgrade pip --quiet
IF ERRORLEVEL 1 (
    ECHO [WARN]  pip upgrade failed – continuing with existing version.
)

REM ── Install / upgrade PyInstaller ──────────────────────────
ECHO [INFO]  Checking for PyInstaller…
python -m pip show pyinstaller >NUL 2>&1
IF ERRORLEVEL 1 (
    ECHO [INFO]  Installing PyInstaller…
    python -m pip install pyinstaller
    IF ERRORLEVEL 1 (
        ECHO [ERROR] Failed to install PyInstaller.
        PAUSE
        EXIT /B 1
    )
)

REM ── Install project requirements ───────────────────────────
IF EXIST requirements.txt (
    ECHO [INFO]  Installing project requirements…
    python -m pip install -r requirements.txt
    IF ERRORLEVEL 1 (
        ECHO [ERROR] Failed to install requirements.
        PAUSE
        EXIT /B 1
    )
) ELSE (
    ECHO [WARN]  requirements.txt not found – skipping.
)

REM ── Delegate to build_exe.py ───────────────────────────────
ECHO [INFO]  Running build_exe.py %*
ECHO.
python build_exe.py %*
SET BUILD_EXIT=%ERRORLEVEL%

ECHO.
IF %BUILD_EXIT% EQU 0 (
    ECHO  =====================================================
    ECHO   Build succeeded!
    ECHO   Output: dist\CHATSEC-SOC-Agent\CHATSEC-SOC-Agent.exe
    ECHO  =====================================================
) ELSE (
    ECHO  =====================================================
    ECHO   Build FAILED ^(exit code %BUILD_EXIT%^).
    ECHO   Check the output above for details.
    ECHO  =====================================================
)

ECHO.
PAUSE
EXIT /B %BUILD_EXIT%
