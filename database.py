import sqlite3
from datetime import datetime
import os
import sys

class NotesDB:
    def __init__(self, db_file="notes.db"):
        # Получаем путь к директории с exe-файлом
        if getattr(sys, 'frozen', False):
            # Если запущено как exe
            exe_dir = os.path.dirname(sys.executable)
        else:
            # Если запущено как скрипт
            exe_dir = os.getcwd()
            
        self.db_file = os.path.join(exe_dir, db_file)
        self._create_tables()

    def _create_tables(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Создаем таблицу заметок с поддержкой вложенности
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    parent_id INTEGER,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
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
                conn.commit()
                
                # Создаем первую заметку
                welcome_text = """SkimNote - это простой и удобный менеджер заметок.

Основные возможности:
- Создание и редактирование заметок
- Древовидная структура заметок
- Поиск по заметкам
- Настройка внешнего вида
- Поддержка горячих клавиш

Эту заметку можно удалить."""
                
                cursor.execute(
                    'INSERT INTO notes (title, content, parent_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                    ("Заметка", welcome_text, 1, now, now)
                )
                conn.commit()

    def add_note(self, title, content="", parent_id=1):
        now = datetime.now()
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO notes (title, content, parent_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                (title, content, parent_id, now, now)
            )
            return cursor.lastrowid

    def update_note(self, note_id, title, content):
        now = datetime.now()
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?',
                (title, content, now, note_id)
            )
            conn.commit()

    def get_notes(self, parent_id=None):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            if parent_id is None:
                cursor.execute('SELECT id, title, content, parent_id, created_at, updated_at FROM notes')
            else:
                cursor.execute('SELECT id, title, content, parent_id, created_at, updated_at FROM notes WHERE parent_id = ?', (parent_id,))
            return cursor.fetchall()

    def get_note(self, note_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, title, content, parent_id, created_at, updated_at FROM notes WHERE id = ?', (note_id,))
            return cursor.fetchone()

    def delete_note(self, note_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            # Рекурсивно удаляем все вложенные заметки
            cursor.execute('''
                WITH RECURSIVE children AS (
                    SELECT id FROM notes WHERE id = ?
                    UNION ALL
                    SELECT n.id FROM notes n JOIN children c ON n.parent_id = c.id
                )
                DELETE FROM notes WHERE id IN (SELECT id FROM children)
            ''', (note_id,))
            conn.commit()

    def get_all_notes(self):
        """Получение всех заметок"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, content, parent_id FROM notes ORDER BY id")
            return cursor.fetchall() 