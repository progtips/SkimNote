import sqlite3
from datetime import datetime
import os
import sys
import configparser
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QDialog, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton
from translations import TRANSLATIONS

class NotesDB:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = 'notes.db'
        self.db_path = db_path
        # Если файл базы данных не существует, создаём его
        if not os.path.exists(self.db_path):
            open(self.db_path, 'a').close()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Получаем путь к директории с exe-файлом
        if getattr(sys, 'frozen', False):
            # Если запущено как exe
            exe_dir = os.path.dirname(sys.executable)
        else:
            # Если запущено как скрипт
            exe_dir = os.getcwd()
            
        self.db_file = os.path.join(exe_dir, self.db_path)
        with self.conn:
            cursor = self.conn.cursor()
            
            # Создаем таблицу заметок с поддержкой вложенности
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    parent_id INTEGER,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    order_index INTEGER DEFAULT 0,
                    FOREIGN KEY (parent_id) REFERENCES notes (id)
                )
            ''')
            
            # Создаем корневую заметку, если её нет
            cursor.execute('SELECT id FROM notes WHERE id = 1')
            if not cursor.fetchone():
                now = datetime.now()
                cursor.execute(
                    'INSERT INTO notes (id, title, content, parent_id, created_at, updated_at) VALUES (1, "Все заметки", "", NULL, ?, ?)',
                    (now, now)
                )
                self.conn.commit()
                
                # Создаем первую заметку
                welcome_text = """SkimNote - это простой и удобный менеджер заметок.\n\nОсновные возможности:\n- Создание и редактирование заметок\n- Древовидная структура заметок\n- Поиск по заметкам\n- Поддержка горячих клавиш\n\nЭту заметку можно удалить."""
                
                cursor.execute(
                    'INSERT INTO notes (title, content, parent_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                    ("Заметка", welcome_text, 1, now, now)
                )
                self.conn.commit()

    def add_note(self, title, content="", parent_id=1):
        now = datetime.now()
        with self.conn:
            # Получаем максимальный порядок для заметок с таким же parent_id
            self.cursor.execute('SELECT MAX(order_index) FROM notes WHERE parent_id = ?', (parent_id,))
            max_order = self.cursor.fetchone()[0] or 0
            
            self.cursor.execute(
                'INSERT INTO notes (title, content, parent_id, created_at, updated_at, order_index) VALUES (?, ?, ?, ?, ?, ?)',
                (title, content, parent_id, now, now, max_order + 1)
            )
            return self.cursor.lastrowid

    def update_note(self, note_id, title, content):
        now = datetime.now()
        with self.conn:
            self.cursor.execute(
                'UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?',
                (title, content, now, note_id)
            )
            self.conn.commit()

    def update_note_order(self, note_id, new_order):
        """Обновляет порядок заметки"""
        with self.conn:
            self.cursor.execute(
                'UPDATE notes SET order_index = ? WHERE id = ?',
                (new_order, note_id)
            )
            self.conn.commit()

    def get_notes(self, parent_id=None):
        with self.conn:
            if parent_id is None:
                self.cursor.execute('SELECT id, title, content, parent_id, created_at, updated_at, order_index FROM notes ORDER BY order_index, id')
            else:
                self.cursor.execute('SELECT id, title, content, parent_id, created_at, updated_at, order_index FROM notes WHERE parent_id = ? ORDER BY order_index, id', (parent_id,))
            return self.cursor.fetchall()

    def get_note(self, note_id):
        """Получение заметки по ID"""
        with self.conn:
            self.cursor.execute("SELECT id, title, content, parent_id, order_index FROM notes WHERE id = ?", (note_id,))
            return self.cursor.fetchone()

    def delete_note(self, note_id):
        with self.conn:
            # Рекурсивно удаляем все вложенные заметки
            self.cursor.execute('''
                WITH RECURSIVE children AS (
                    SELECT id FROM notes WHERE id = ?
                    UNION ALL
                    SELECT n.id FROM notes n JOIN children c ON n.parent_id = c.id
                )
                DELETE FROM notes WHERE id IN (SELECT id FROM children)
            ''', (note_id,))
            self.conn.commit()

    def get_all_notes(self):
        """Получение всех заметок"""
        with self.conn:
            self.cursor.execute("SELECT id, title, content, parent_id, order_index FROM notes ORDER BY order_index, id")
            return self.cursor.fetchall()

    def save_note(self, note_id, title, content):
        """Сохранение заметки"""
        print(f"DEBUG: NotesDB.save_note called")
        print(f"DEBUG: note_id = {note_id}")
        print(f"DEBUG: title = {title}")
        print(f"DEBUG: content length = {len(content) if content else 0}")
        
        now = datetime.now()
        with self.conn:
            self.cursor.execute(
                'UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?',
                (title, content, now, note_id)
            )
            print(f"DEBUG: SQL executed, rows affected = {self.cursor.rowcount}")
            self.conn.commit()
            print(f"DEBUG: Transaction committed")

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()


class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self, base_dir, current_language='Русский'):
        self.base_dir = base_dir
        self.current_language = current_language
        self.settings_file = os.path.join(base_dir, 'settings.ini')
        self.db = None
        self.db_path = None
        
    def init_database(self, db_path=None):
        """Инициализация базы данных"""
        if db_path is None:
            db_path = self.get_db_path_from_settings()
        
        self.db_path = db_path
        self.db = NotesDB(db_path)
        return self.db
        
    def get_db_path_from_settings(self):
        """Получение пути к базе данных из настроек"""
        if os.path.exists(self.settings_file):
            try:
                config = configparser.ConfigParser()
                config.read(self.settings_file, encoding='utf-8')
                return config.get('Database', 'path', fallback='notes.db')
            except Exception:
                return 'notes.db'
        return 'notes.db'
        
    def save_db_path_to_settings(self, db_path):
        """Сохранение пути к базе данных в настройки"""
        try:
            config = configparser.ConfigParser()
            if os.path.exists(self.settings_file):
                config.read(self.settings_file, encoding='utf-8')
            
            if 'Database' not in config:
                config.add_section('Database')
            
            config['Database']['path'] = db_path
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                config.write(f)
                
            return True
        except Exception as e:
            print(f"Ошибка при сохранении пути к БД: {e}")
            return False
            
    def change_database(self, parent_widget):
        """Смена базы данных"""
        file_name, _ = QFileDialog.getOpenFileName(
            parent_widget, 
            TRANSLATIONS[self.current_language]['action_change_db'], 
            "", 
            "SQLite Database (*.db);;All Files (*.*)"
        )
        
        if file_name:
            return self.switch_to_database(file_name)
        return False
        
    def switch_to_database(self, db_path):
        """Переключение на новую базу данных"""
        try:
            # Закрываем текущее соединение
            if self.db:
                self.db.close()
            
            # Сохраняем новый путь в настройки
            if self.save_db_path_to_settings(db_path):
                # Инициализируем новую базу данных
                self.init_database(db_path)
                return True
            return False
        except Exception as e:
            print(f"Ошибка при переключении БД: {e}")
            return False
            
    def restore_database(self, parent_widget, backup_manager):
        """Восстановление базы данных из бэкапа"""
        backup_files = backup_manager.get_backup_list()
        
        if not backup_files:
            QMessageBox.warning(
                parent_widget, 
                TRANSLATIONS[self.current_language]['restore_title'],
                TRANSLATIONS[self.current_language]['no_backups_found']
            )
            return False
        
        # Создаем диалог выбора файла
        dialog = QDialog(parent_widget)
        dialog.setWindowTitle(TRANSLATIONS[self.current_language]['restore_title'])
        layout = QVBoxLayout(dialog)
        
        list_widget = QListWidget()
        for file_path in backup_files:
            filename = os.path.basename(file_path)
            list_widget.addItem(filename)
        layout.addWidget(list_widget)
        
        buttons = QHBoxLayout()
        ok_button = QPushButton(TRANSLATIONS[self.current_language]['restore'])
        cancel_button = QPushButton(TRANSLATIONS[self.current_language]['settings_cancel'])
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_index = list_widget.currentRow()
            if selected_index >= 0:
                selected_backup_path = backup_files[selected_index]
                
                # Выдаем предупреждение перед восстановлением
                reply = QMessageBox.question(
                    parent_widget, 
                    TRANSLATIONS[self.current_language]['restore_title'],
                    TRANSLATIONS[self.current_language]['confirm_restore'],
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return False
                
                # Получаем путь к основной базе данных из настроек
                main_db_path = self.get_db_path_from_settings()
                
                # Закрываем текущее соединение с базой данных
                if self.db:
                    self.db.close()
                
                # Восстанавливаем базу данных
                if backup_manager.restore_backup(selected_backup_path, main_db_path):
                    # Пересоздаем соединение с базой данных
                    self.init_database(main_db_path)
                    
                    QMessageBox.information(
                        parent_widget, 
                        TRANSLATIONS[self.current_language]['restore_title'],
                        TRANSLATIONS[self.current_language]['restore_success']
                    )
                    return True
                else:
                    QMessageBox.critical(
                        parent_widget, 
                        TRANSLATIONS[self.current_language]['restore_title'],
                        "Ошибка при восстановлении базы данных"
                    )
                    return False
        return False
        
    def close_database(self):
        """Закрытие соединения с базой данных"""
        if self.db:
            self.db.close()
            self.db = None 