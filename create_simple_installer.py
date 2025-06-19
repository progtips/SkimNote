#!/usr/bin/env python3
"""
Простой скрипт для создания установщика SkimNote
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_installer():
    """Создание простого установщика"""
    print("=== Создание простого установщика SkimNote ===")
    
    # Проверяем наличие исполняемого файла
    if not os.path.exists('dist/SkimNote.exe'):
        print("Ошибка: Файл dist/SkimNote.exe не найден!")
        print("Сначала запустите: python build_exe.py")
        return False
    
    # Создаем папку для установщика
    installer_dir = Path('installer')
    installer_dir.mkdir(exist_ok=True)
    
    # Создаем временную папку
    temp_dir = Path('temp_installer')
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    
    print("Копирование файлов...")
    
    # Копируем файлы
    shutil.copy2('dist/SkimNote.exe', temp_dir)
    shutil.copytree('icons', temp_dir / 'icons')
    shutil.copy2('LICENSE.txt', temp_dir)
    if os.path.exists('README.md'):
        shutil.copy2('README.md', temp_dir)
    
    # Создаем bat-файл для установки
    install_script = '''@echo off
chcp 65001 >nul
title Установка SkimNote v1.0

echo ========================================
echo    Установка SkimNote v1.0
echo ========================================
echo.

REM Показываем лицензию
echo Пожалуйста, прочитайте лицензионное соглашение:
echo.
type LICENSE.txt
echo.
set /p "accept=Принимаете ли вы условия лицензии? (y/n): "
if /i not "%accept%"=="y" (
    echo Установка отменена.
    pause
    exit /b 1
)

echo.
set /p "installDir=Введите путь для установки (по умолчанию: %%ProgramFiles%%\\SkimNote): "
if "%installDir%"=="" set "installDir=%ProgramFiles%\\SkimNote"

echo.
echo Установка в: %installDir%
echo.

if not exist "%installDir%" mkdir "%installDir%"

echo Копирование файлов...
copy "SkimNote.exe" "%installDir%\\"
xcopy "icons" "%installDir%\\icons\\" /E /I /Y
copy "LICENSE.txt" "%installDir%\\"
if exist "README.md" copy "README.md" "%installDir%\\"

echo.
echo Создание ярлыков...

REM Создание ярлыка в меню Пуск
set "startMenu=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\SkimNote"
if not exist "%startMenu%" mkdir "%startMenu%"

echo @echo off > "%startMenu%\\SkimNote.bat"
echo cd /d "%installDir%" >> "%startMenu%\\SkimNote.bat"
echo start "" "SkimNote.exe" >> "%startMenu%\\SkimNote.bat"

REM Создание ярлыка на рабочем столе
set "desktop=%USERPROFILE%\\Desktop"
echo @echo off > "%desktop%\\SkimNote.bat"
echo cd /d "%installDir%" >> "%desktop%\\SkimNote.bat"
echo start "" "SkimNote.exe" >> "%desktop%\\SkimNote.bat"

echo.
echo ========================================
echo    Установка завершена!
echo ========================================
echo.
echo Программа установлена в: %installDir%
echo Ярлыки созданы на рабочем столе и в меню Пуск
echo.
echo Для удаления программы запустите uninstall.bat
echo.
pause
'''
    
    with open(temp_dir / 'install.bat', 'w', encoding='utf-8') as f:
        f.write(install_script)
    
    # Создаем bat-файл для удаления
    uninstall_script = '''@echo off
chcp 65001 >nul
title Удаление SkimNote

echo ========================================
echo    Удаление SkimNote
echo ========================================
echo.

set "installDir=%ProgramFiles%\\SkimNote"

if not exist "%installDir%" (
    echo Программа не найдена в %installDir%
    echo Возможно, она была установлена в другую папку
    pause
    exit /b 1
)

echo Удаление файлов из: %installDir%
rmdir /s /q "%installDir%"

echo.
echo Удаление ярлыков...

REM Удаление ярлыка из меню Пуск
set "startMenu=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\SkimNote"
if exist "%startMenu%" rmdir /s /q "%startMenu%"

REM Удаление ярлыка с рабочего стола
set "desktop=%USERPROFILE%\\Desktop"
if exist "%desktop%\\SkimNote.bat" del "%desktop%\\SkimNote.bat"

echo.
echo ========================================
echo    Удаление завершено!
echo ========================================
echo.
pause
'''
    
    with open(temp_dir / 'uninstall.bat', 'w', encoding='utf-8') as f:
        f.write(uninstall_script)
    
    # Создаем архив
    print("Создание архива...")
    archive_path = installer_dir / 'SkimNote_Setup.zip'
    
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in temp_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(temp_dir)
                zipf.write(file_path, arcname)
    
    # Создаем основной установщик
    main_installer = '''@echo off
chcp 65001 >nul
title Установщик SkimNote v1.0

echo ========================================
echo    Установщик SkimNote v1.0
echo ========================================
echo.
echo Этот установщик распакует и установит
echo программу SkimNote на ваш компьютер.
echo.
echo Нажмите любую клавишу для начала установки...
pause >nul

REM Создаем временную папку
set "tempDir=%TEMP%\\SkimNote_Install"
if exist "%tempDir%" rmdir /s /q "%tempDir%"
mkdir "%tempDir%"

REM Распаковываем архив
echo Распаковка файлов...
powershell -command "Expand-Archive -Path '%~f0' -DestinationPath '%tempDir%' -Force"

REM Запускаем установку
cd /d "%tempDir%"
if exist "install.bat" (
    call install.bat
) else (
    echo Ошибка: Файл установки не найден
    pause
)

REM Очистка
cd /d "%~dp0"
rmdir /s /q "%tempDir%"

echo.
echo Установка завершена!
pause

'''
    
    # Создаем bat-файл с архивом
    installer_path = installer_dir / 'SkimNote_Setup.bat'
    
    with open(installer_path, 'w', encoding='utf-8') as f:
        f.write(main_installer)
    
    # Добавляем архив в конец bat-файла
    with open(archive_path, 'rb') as archive_file:
        archive_data = archive_file.read()
    
    with open(installer_path, 'ab') as f:
        f.write(archive_data)
    
    # Очистка
    shutil.rmtree(temp_dir)
    os.remove(archive_path)
    
    # Показываем результат
    file_size = installer_path.stat().st_size / (1024 * 1024)
    print(f"✓ Установщик создан успешно!")
    print(f"Файл: {installer_path}")
    print(f"Размер: {file_size:.1f} МБ")
    
    return True

def main():
    """Основная функция"""
    if create_installer():
        print("\nТеперь вы можете распространять файл installer/SkimNote_Setup.bat")
        print("Пользователи могут просто запустить этот файл для установки программы.")
    else:
        print("\nОшибка при создании установщика.")

if __name__ == '__main__':
    main() 