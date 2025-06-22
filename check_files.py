#!/usr/bin/env python3
"""
Скрипт для проверки занятых файлов перед сборкой
"""

import os
import sys
from pathlib import Path

def check_file_access(file_path):
    """Проверяет, доступен ли файл для записи"""
    try:
        # Пытаемся открыть файл для записи
        with open(file_path, 'a'):
            pass
        return True
    except PermissionError:
        return False
    except FileNotFoundError:
        # Файл не существует, значит можно создать
        return True

def main():
    """Основная функция"""
    print("=== Проверка доступности файлов ===")
    
    # Файлы для проверки
    files_to_check = [
        'dist/SkimNote.exe',
        'installer/SkimNote_Setup.exe',
        'build',
        'dist',
        '__pycache__'
    ]
    
    all_ok = True
    
    for file_path in files_to_check:
        path = Path(file_path)
        
        if path.exists():
            if path.is_file():
                if check_file_access(path):
                    print(f"✓ {file_path} - доступен")
                else:
                    print(f"✗ {file_path} - занят другим процессом")
                    all_ok = False
            else:
                # Это папка
                print(f"✓ {file_path} - папка существует")
        else:
            print(f"✓ {file_path} - не существует (можно создать)")
    
    if not all_ok:
        print("\n⚠ Рекомендации:")
        print("1. Закройте все программы, которые могут использовать эти файлы")
        print("2. Закройте проводник Windows в папке проекта")
        print("3. Перезапустите IDE или редактор кода")
        print("4. Попробуйте запустить сборку снова")
        return False
    
    print("\n✓ Все файлы доступны для работы")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 