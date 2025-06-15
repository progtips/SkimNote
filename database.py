import sqlite3
from datetime import datetime
import os
import sys

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
        with self.conn:
            self.cursor.execute('SELECT id, title, content, parent_id, created_at, updated_at FROM notes WHERE id = ?', (note_id,))
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

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close() 