# SkimNote

![SkimNote Icon](icons/app.svg)

**SkimNote** - это легкий и удобный иерархический менеджер заметок, написанный на Python с использованием PyQt6. Он идеально подходит для организации мыслей, ведения проектной документации и хранения любой текстовой информации в древовидной структуре.

Приложение является портативным: база данных (`notes.db`), файл настроек (`settings.ini`) и резервные копии (`backup/`) хранятся в той же папке, где находится исполняемый файл.

---

**SkimNote** is a lightweight and convenient hierarchical note manager written in Python using PyQt6. It is ideal for organizing thoughts, maintaining project documentation, and storing any text-based information in a tree-like structure.

The application is portable: the database (`notes.db`), settings file (`settings.ini`), and backups (`backup/`) are stored in the same folder as the executable file.

## Возможности / Features

-   **Иерархическая структура**: Организуйте заметки в виде дерева с неограниченной вложенностью.
    -   *Hierarchical structure*: Organize notes in a tree with unlimited nesting.
-   **Портативность**: Храните приложение и все его данные на флешке или в облаке.
    -   *Portability*: Keep the application and all its data on a flash drive or in the cloud.
-   **Настройки интерфейса**: Настраивайте язык (Русский/Английский) и размер шрифта.
    -   *Interface settings*: Customize language (Russian/English) and font size.
-   **Управление базами данных**: Создавайте новые или переключайтесь между разными файлами баз данных.
    -   *Database management*: Create new databases or switch between different database files.
-   **Резервное копирование и восстановление**: Автоматическое создание бэкапов и простое восстановление из них.
    -   *Backup and restore*: Automatic creation of backups and easy restoration from them.
-   **Поиск и замена**: Полнотекстовый поиск и замена по всем заметкам.
    -   *Search and replace*: Full-text search and replace across all notes.
-   **Горячие клавиши**: Удобное управление с помощью клавиатуры.
    -   *Hotkeys*: Convenient keyboard control.

## Установка и запуск / Installation and Launch

### Windows (исполняемый файл) / Windows (Executable)

1.  Перейдите в раздел [Releases](https://github.com/your_username/SkimNote/releases).
2.  Скачайте последнюю версию `SkimNote_Setup.exe`.
3.  Запустите установщик и следуйте инструкциям.

## Структура проекта / Project Structure

-   `main.py`: Основной файл приложения с логикой интерфейса.
-   `database_manager.py`: Модуль для работы с базой данных SQLite.
-   `settings_dialog.py`: Диалоговое окно настроек.
-   `toolbar_manager.py`: Модуль для создания и управления панелью инструментов.
-   `backup_manager.py`: Логика резервного копирования и восстановления.
-   `config.py`: Управление конфигурацией (файл `settings.ini`).
-   `translations.py`: Тексты для локализации интерфейса.
-   `icons/`: Иконки приложения.
-   `build.bat`: Скрипт для сборки exe-файла под Windows.
-   `installer.iss`: Скрипт для создания установщика с помощью Inno Setup.
-   `requirements.txt`: Список зависимостей Python.

## Лицензия / License

[MIT License](LICENSE.txt) 