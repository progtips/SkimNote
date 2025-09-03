#!/usr/bin/env python3
"""
Скрипт для сборки исполняемого файла SkimNote с помощью PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build_dirs():
    """Очистка папок сборки"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Удаляем папку {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Удаляем .spec файлы
    for spec_file in Path('.').glob('*.spec'):
        print(f"Удаляем файл {spec_file}...")
        spec_file.unlink()

def build_executable():
    """Сборка исполняемого файла"""
    print("Начинаем сборку исполняемого файла...")
    
    # Команда для PyInstaller через модуль (устойчиво к путям)
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',                    # Один файл
        '--windowed',                   # Без консольного окна
        '--name=SkimNote',              # Имя исполняемого файла
        '--icon=icons/app.ico',         # Иконка
        '--add-data=icons;icons',       # Добавляем папку с иконками
        '--add-data=translations.py;.', # Добавляем файл переводов
        '--add-data=config.py;.',       # Добавляем файл конфигурации
        '--add-data=database_manager.py;.',     # Добавляем файл менеджера базы данных
        '--add-data=settings_dialog.py;.', # Добавляем диалог настроек
        '--add-data=toolbar_manager.py;.', # Добавляем менеджер панели инструментов
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=sqlite3',
        '--hidden-import=configparser',
        '--hidden-import=datetime',
        '--hidden-import=shutil',
        '--hidden-import=socket',
        'main.py'
    ]
    
    try:
        # Используем encoding='utf-8' для правильной обработки кодировки
        result = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            encoding='utf-8',
            errors='replace'  # Заменяем проблемные символы
        )
        print("Сборка завершена успешно!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при сборке: {e}")
        print(f"Вывод ошибки: {e.stderr}")
        return False

def main():
    """Основная функция"""
    print("=== Сборка SkimNote ===")
    
    # Проверяем наличие PyInstaller
    try:
        import PyInstaller
        print(f"PyInstaller найден: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller не найден. Устанавливаем...")
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'pyinstaller'], 
            check=True,
            encoding='utf-8',
            errors='replace'
        )
    
    # Очищаем предыдущие сборки
    clean_build_dirs()
    
    # Собираем исполняемый файл
    if build_executable():
        print("\n=== Сборка завершена успешно! ===")
        print("Исполняемый файл находится в папке dist/SkimNote.exe")
        print("Теперь можно создать установщик с помощью Inno Setup")
    else:
        print("\n=== Ошибка при сборке ===")
        sys.exit(1)

if __name__ == '__main__':
    main() 