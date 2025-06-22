#!/usr/bin/env python3
"""
Упрощенный скрипт для автоматизации процесса сборки установщика SkimNote
Без capture_output для избежания проблем с кодировкой
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    """Проверка необходимых компонентов"""
    print("=== Проверка требований ===")
    
    # Проверяем Python
    print(f"Python версия: {sys.version}")
    
    # Проверяем PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller найден: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller не найден. Устанавливаем...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        print("✓ PyInstaller установлен")
    
    # Проверяем Inno Setup
    inno_compiler = None
    possible_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            inno_compiler = path
            break
    
    if inno_compiler:
        print(f"✓ Inno Setup найден: {inno_compiler}")
    else:
        print("✗ Inno Setup не найден!")
        print("Пожалуйста, установите Inno Setup с сайта: https://jrsoftware.org/isinfo.php")
        print("После установки запустите этот скрипт снова.")
        return False
    
    return True

def build_executable():
    """Сборка исполняемого файла"""
    print("\n=== Сборка исполняемого файла ===")
    
    # Запускаем скрипт сборки без capture_output
    try:
        result = subprocess.run([sys.executable, 'build_exe.py'], check=True)
        print("✓ Сборка исполняемого файла завершена")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Ошибка при сборке: {e}")
        return False

def create_installer():
    """Создание установщика"""
    print("\n=== Создание установщика ===")
    
    # Проверяем наличие исполняемого файла
    if not os.path.exists('dist/SkimNote.exe'):
        print("✗ Исполняемый файл не найден. Сначала выполните сборку.")
        return False
    
    # Создаем папку для установщика
    installer_dir = Path('installer')
    installer_dir.mkdir(exist_ok=True)
    
    # Находим компилятор Inno Setup
    inno_compiler = None
    possible_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            inno_compiler = path
            break
    
    if not inno_compiler:
        print("✗ Компилятор Inno Setup не найден!")
        return False
    
    # Проверяем, не занят ли файл
    installer_output = Path('installer/SkimNote_Setup.exe')
    if installer_output.exists():
        try:
            # Пытаемся удалить существующий файл
            installer_output.unlink()
            print("Удален существующий установщик")
        except PermissionError:
            print("⚠ Предупреждение: Не удалось удалить существующий установщик.")
            print("Пожалуйста, закройте все программы, которые могут использовать этот файл.")
            return False
    
    # Компилируем установщик без capture_output
    try:
        cmd = [inno_compiler, 'installer.iss']
        result = subprocess.run(cmd, check=True)
        print("✓ Установщик создан успешно!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Ошибка при создании установщика: {e}")
        return False

def cleanup():
    """Очистка временных файлов"""
    print("\n=== Очистка временных файлов ===")
    
    # Удаляем папки сборки PyInstaller
    dirs_to_clean = ['build', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Удаляем папку {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Удаляем .spec файлы
    for spec_file in Path('.').glob('*.spec'):
        print(f"Удаляем файл {spec_file}...")
        spec_file.unlink()

def main():
    """Основная функция"""
    print("=== Автоматическая сборка установщика SkimNote (упрощенная версия) ===")
    print("Этот скрипт создаст полный установщик для вашей программы.")
    print()
    
    # Проверяем требования
    if not check_requirements():
        print("\n✗ Не все требования выполнены. Сборка прервана.")
        sys.exit(1)
    
    # Собираем исполняемый файл
    if not build_executable():
        print("\n✗ Ошибка при сборке исполняемого файла. Сборка прервана.")
        sys.exit(1)
    
    # Создаем установщик
    if not create_installer():
        print("\n✗ Ошибка при создании установщика. Сборка прервана.")
        sys.exit(1)
    
    # Очищаем временные файлы
    cleanup()
    
    print("\n=== Сборка завершена успешно! ===")
    print("Установщик находится в папке: installer/SkimNote_Setup.exe")
    print("Размер установщика:", end=" ")
    
    installer_path = Path('installer/SkimNote_Setup.exe')
    if installer_path.exists():
        size_mb = installer_path.stat().st_size / (1024 * 1024)
        print(f"{size_mb:.1f} МБ")
    else:
        print("файл не найден")
    
    print("\nТеперь вы можете распространять установщик пользователям!")

if __name__ == '__main__':
    main() 