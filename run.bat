@echo off
REM Quick run script for Windows - Auto setup and run
echo Starting Acx Shell...
python main.py
if errorlevel 1 (
    echo.
    echo Setup failed! Please check the errors above.
    pause
)
