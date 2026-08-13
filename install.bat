@echo off
chcp 65001 >nul
echo ==========================================
echo   PC Health Guardian v2.0 Installer
echo   Для системы Intel Celeron N4120
echo ==========================================
echo.

:: Проверка прав администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Требуемые права администратора!
    pause
    exit /b
)

:: Создание папки программы
set APP_DIR=%ProgramFiles%\PCHealthGuardian
if not exist "%APP_DIR%" mkdir "%APP_DIR%"

:: Копирование файлов (предполагается, что скрипт запущен из папки с файлами)
copy "%~dp0pc_health_guardian.py" "%APP_DIR%" /Y
copy "%~dp0requirements.txt" "%APP_DIR%" /Y

:: Установка зависимостей
echo [1/3] Установка библиотек...
pip install -r "%APP_DIR%\requirements.txt" --quiet

:: Создание ярлыка для скрытого запуска (pythonw)
echo [2/3] Создание ярлыка автозагрузки...
set SCRIPT_PATH="%APP_DIR%\pc_health_guardian.py"
set LINK_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\PCGuardian.vbs

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%LINK_PATH%"
echo sLinkFile = oWS.SpecialFolders("Startup") ^& "\PCGuardian.vbs" >> "%LINK_PATH%"
echo oWS.Run "pythonw.exe %SCRIPT_PATH%", 0, False >> "%LINK_PATH%"

:: Регистрация в реестре (альтернативный метод)
echo [3/3] Настройка реестра...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "PCHealthGuardian" /t REG_SZ /d "pythonw.exe \"%APP_DIR%\pc_health_guardian.py\"" /f

echo.
echo ==========================================
echo   УСПЕШНО УСТАНОВЛЕНО!
echo   Программа запустится после перезагрузки.
echo   Или запустите файл run_guardian.vbs сейчас.
echo ==========================================
pause
