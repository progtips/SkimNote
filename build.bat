@echo off
chcp 65001 >nul
echo ========================================
echo    Сборка установщика SkimNote
echo ========================================
echo.

echo Запуск автоматической сборки...
python build_installer.py

echo.
echo Нажмите любую клавишу для выхода...
pause >nul 