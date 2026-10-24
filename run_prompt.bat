@echo off
REM Tao prompt anh True Crime tu file da dich

echo ============================================================
echo     TAO PROMPT ANH - TRUE CRIME (Gemini AI)
echo ============================================================
echo.
echo Doc file da dich va tao prompt anh sieu that
echo Co tham tu noir trong moi canh
echo Xuat ra: output_voice\
echo.
echo ============================================================
echo.

cd /d "%~dp0"
python script_generator.py

pause
