@echo off
REM Quick Start Menu - Auto Content Workflow
cd /d "%~dp0"

:menu
cls
echo ============================================================
echo          AUTO CONTENT WORKFLOW - QUICK START
echo ============================================================
echo.
echo Chon che do chay:
echo.
echo   1. FULL AUTOMATION (Khuyến nghị)
echo      - Tai, Transcribe, Dich tu dong
echo      - Xu ly 10 videos moi lan
echo.
echo   2. CHI AUTO PROCESSOR
echo      - Chi xu ly MP3 co san trong folder
echo      - Khong tai video moi
echo.
echo   3. MANUAL CONTROL (Menu tuong tac)
echo      - Chon tung buoc thu cong
echo.
echo   4. TAO VOICE (Vira-TTS)
echo      - Clone giong tu voicegoc.MP3
echo      - Tao voice tu file da dich
echo.
echo   5. TAO KICH BAN VIDEO (Gemini AI)
echo      - Tao prompt True Crime cho AI video
echo      - 15-25 canh/truyen
echo.
echo   0. Thoat
echo.
echo ============================================================
choice /C 123450 /N /M "Nhap lua chon cua ban (1-5 hoac 0): "

if errorlevel 6 goto :end
if errorlevel 5 goto :script
if errorlevel 4 goto :voice
if errorlevel 3 goto :manual
if errorlevel 2 goto :processor
if errorlevel 1 goto :full

:full
cls
echo Khoi dong FULL AUTOMATION...
echo.
python run_full_automation.py
pause
goto :menu

:processor
cls
echo Khoi dong AUTO PROCESSOR...
echo.
python auto_processor.py
pause
goto :menu

:manual
cls
echo Khoi dong MANUAL CONTROL...
echo.
python run_workflow.py
pause
goto :menu

:voice
cls
echo Khoi dong VOICE GENERATOR (Vira-TTS)...
echo.
python voice_generator.py
pause
goto :menu

:script
cls
echo Khoi dong SCRIPT GENERATOR (True Crime Prompts)...
echo.
python script_generator.py
pause
goto :menu

:end
echo.
echo Tam biet!
exit /b
