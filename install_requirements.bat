chcp 65001
@echo off
::echo Создание requirements.txt...
::pipreqs . --encoding=utf-8 --force
echo Создание виртуальной среды...
python -m venv venv

echo Активация виртуальной среды...
call venv\Scripts\activate.bat

echo Установка зависимостей...
pip install -r requirements.txt

echo.
echo Установка успешна!
echo Теперь можете запустить проект:
call python main.py
pause