@echo off
REM PC Health Guardian - Быстрый запуск для Windows
REM Оптимизировано для слабых ПК

echo ============================================
echo PC Health Guardian v1.0
echo Запуск модуля защиты ПК
echo ============================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Пожалуйста, установите Python 3.8+ с https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Установка зависимостей (если нужно)
echo Проверка зависимостей...
pip show psutil >nul 2>&1
if errorlevel 1 (
    echo Установка psutil...
    pip install -r requirements.txt
)

REM Запуск программы
echo.
echo Запуск PC Health Guardian...
echo Программа будет работать в фоновом режиме.
echo Для управления используйте меню.
echo.

python "%~dp0pc_health_guardian.py"

pause
