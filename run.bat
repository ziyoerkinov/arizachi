@echo off
chcp 65001 >nul
echo =======================================
echo     Uch Oyoq Bot Ishga Tushirilmoqda...
echo =======================================

python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Xatolik: Python kompyuteringizda o'rnatilmagan yoki muhit o'zgaruvchilariga PATH ro'yxatiga qo'shilmagan.
    echo Iltimos, python.org saytidan Python ni yuklab oling va o'rnating.
    echo O'rnatayotganda "Add python to PATH" degan katakchani belgilashni unutmang!
    pause
    exit /b
)

echo Kutubxonalar tekshirilmoqda...
pip install -r requirements.txt --quiet

echo.
echo Bot ishga tushirildi! Qora oyna ochiq turguncha bot ishlab turadi.
echo To'xtatish uchun bu oynani yoping yoki Ctrl+C bosing.
echo.
python bot.py
pause
