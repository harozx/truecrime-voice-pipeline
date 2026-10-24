@echo off
REM Tao voice tu file da dich - Vira-TTS

echo ============================================================
echo     TAO VOICE - VIRA-TTS (Clone giong)
echo ============================================================
echo.
echo Lay file da dich tu processed_stories
echo Clone giong tu voicegoc.MP3
echo Xuat ra: output_voice\
echo.
echo ============================================================
echo.

cd /d "%~dp0"
python voice_generator.py

pause
