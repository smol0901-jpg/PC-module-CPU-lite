@echo off
chcp 65001 >nul
echo ==========================================
echo PC Health Guardian - Установка
echo ==========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Установите Python с https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Установка зависимостей...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ОШИБКА при установке зависимостей!
    pause
    exit /b 1
)

echo [2/3] Создание ярлыка для автозагрузки...
set SCRIPT_DIR=%~dp0
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

REM Создаем ярлык в автозагрузке
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_DIR%\PC Health Guardian.lnk'); $Shortcut.TargetPath = '%SCRIPT_DIR%run_guardian.vbs'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Description = 'PC Health Guardian - Защита вашего ПК'; $Shortcut.Save()"

echo [3/3] Настройка завершена!
echo.
echo Программа будет запускаться автоматически при входе в Windows.
echo Значок появится в системном трее (возле часов).
echo.
pause

REM Запуск программы
echo Запуск PC Health Guardian...
start "" "%SCRIPT_DIR%run_guardian.vbs"
