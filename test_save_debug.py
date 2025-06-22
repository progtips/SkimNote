#!/usr/bin/env python3
"""
Тест для проверки сохранения с отладкой
"""

import sys
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLabel, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt, QTimer
from database_manager import DatabaseManager

class TestSaveDebugApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тест сохранения с отладкой")
        self.setGeometry(100, 100, 800, 600)
        
        # Инициализация
        self.current_note_id = None
        self.content_modified = False
        self.programmatic_load = False
        
        # Инициализация базы данных
        self.db_manager = DatabaseManager(".", "Русский")
        self.db_manager.init_database("test_debug.db")
        self.db = self.db_manager.db
        
        # Создание UI
        self.setup_ui()
        
        # Создание тестовых заметок
        self.create_test_notes()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Информация
        info_label = QLabel("Редактируйте текст и переключайтесь между заметками")
        layout.addWidget(info_label)
        
        # Дерево заметок
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self.on_note_selected)
        layout.addWidget(self.tree)
        
        # Редактор
        self.editor = QTextEdit()
        self.editor.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.editor)
        
        # Кнопки
        save_button = QPushButton("Сохранить вручную")
        save_button.clicked.connect(self.save_note)
        layout.addWidget(save_button)
        
        status_label = QLabel("Статус: Готов")
        layout.addWidget(status_label)
        self.status_label = status_label
        
    def create_test_notes(self):
        """Создание тестовых заметок"""
        try:
            # Создаем заметки
            note1_id = self.db.add_note("Заметка 1", "Содержимое заметки 1", 1)
            note2_id = self.db.add_note("Заметка 2", "Содержимое заметки 2", 1)
            
            # Загружаем заметки в дерево
            self.load_notes()
            
            # Выбираем первую заметку
            if self.tree.topLevelItemCount() > 0:
                first_item = self.tree.topLevelItem(0)
                self.tree.setCurrentItem(first_item)
                self.on_note_selected(first_item)
                
        except Exception as e:
            self.status_label.setText(f"Ошибка создания заметок: {e}")
            
    def load_notes(self):
        """Загрузка заметок в дерево"""
        self.tree.clear()
        notes = self.db.get_all_notes()
        
        for note in notes:
            note_id, title, content, parent_id, order_index = note
            if parent_id == 1:  # Только заметки верхнего уровня
                item = QTreeWidgetItem(self.tree, [title])
                item.setData(0, Qt.ItemDataRole.UserRole, note_id)
                self.tree.addTopLevelItem(item)
        
        self.tree.expandAll()
            
    def on_text_changed(self):
        """Обработчик изменения текста"""
        if self.programmatic_load:
            print(f"DEBUG: on_text_changed ignored (programmatic load)")
            return
            
        print(f"DEBUG: on_text_changed called - content_modified set to True")
        self.content_modified = True
        self.status_label.setText("Статус: Изменено (не сохранено)")
        
    def on_note_selected(self, item):
        """Обработка выбора заметки"""
        print(f"DEBUG: on_note_selected called")
        print(f"DEBUG: current_note_id = {self.current_note_id}")
        print(f"DEBUG: content_modified = {self.content_modified}")
        
        # Сохраняем предыдущую заметку
        if self.current_note_id and self.content_modified:
            print(f"DEBUG: Saving previous note before switching")
            self.save_current_note()
        
        if not item:
            print(f"DEBUG: No item selected")
            return
            
        note_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not note_id:
            print(f"DEBUG: No note_id in item")
            return
            
        print(f"DEBUG: Loading note with ID: {note_id}")
        
        # Получаем данные заметки из базы
        note = self.db.get_note(note_id)
        if not note:
            print(f"DEBUG: Note not found in DB")
            return
            
        # Отображаем текст заметки
        self.programmatic_load = True  # Устанавливаем флаг перед загрузкой
        self.editor.setPlainText(note[2])  # content
        self.programmatic_load = False  # Сбрасываем флаг после загрузки
        
        # Сохраняем ID текущей заметки и родителя
        self.current_note_id = note_id
        self.current_parent_id = note[3]  # parent_id
        
        # Сбрасываем флаг изменения
        self.content_modified = False
        print(f"DEBUG: Note loaded, content_modified set to False")
        self.status_label.setText(f"Статус: Загружена заметка {note_id}")
        
    def save_current_note(self):
        """Сохранение текущей заметки"""
        print(f"DEBUG: save_current_note called")
        print(f"DEBUG: current_note_id = {self.current_note_id}")
        print(f"DEBUG: content_modified = {self.content_modified}")
        
        if not self.current_note_id or not self.content_modified:
            print(f"DEBUG: Early return - no note_id or not modified")
            return
            
        content = self.editor.toPlainText()
        print(f"DEBUG: content length = {len(content)}")
        
        try:
            # Получаем текущую заметку
            note = self.db.get_note(self.current_note_id)
            print(f"DEBUG: note from DB = {note}")
            if note:
                # Сохраняем с тем же заголовком
                self.db.save_note(self.current_note_id, note[1], content)
                print(f"DEBUG: Note saved successfully")
                self.content_modified = False
                self.status_label.setText("Статус: Сохранено")
            else:
                print(f"DEBUG: Note not found in DB")
                self.status_label.setText("Статус: Заметка не найдена")
        except Exception as e:
            print(f"DEBUG: Exception during save: {e}")
            self.status_label.setText(f"Статус: Ошибка сохранения - {e}")
            
    def save_note(self):
        """Ручное сохранение заметки"""
        self.save_current_note()

def main():
    app = QApplication(sys.argv)
    window = TestSaveDebugApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 