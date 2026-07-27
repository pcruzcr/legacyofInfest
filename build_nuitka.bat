@echo off
REM Nuitka build script for Legacy of InFest
REM Requirements: pip install nuitka ordered-set
REM
REM Usage:
REM   build_nuitka.bat          (standalone folder)
REM   build_nuitka.bat --onefile  (single .exe)

setlocal enabledelayedexpansion

set "NUITKA_OPTS=--standalone --enable-plugin=pygame-ce --enable-plugin=numpy --enable-plugin=pydantic --enable-plugin=multiprocessing --follow-import-to=src --noinclude-default-mode=error --include-data-dir=assets=assets --output-dir=build"

if "%1"=="--onefile" (
    set "NUITKA_OPTS=!NUITKA_OPTS! --onefile"
)

python -m nuitka %NUITKA_OPTS% main.py
