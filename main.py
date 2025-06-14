import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTreeWidget, QTreeWidgetItem, QTextEdit,
                            QPushButton, QMenu, QMessageBox, QInputDialog, QToolBar,
                            QLabel, QSplitter)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon
from database import NotesDB
from config import Config
from settings_dialog import SettingsDialog
import os
import sqlite3

class NotesApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SkimNote - Менеджер заметок")
        self.resize(1000, 600)
        
        # Устанавливаем иконку приложения
        app_icon = QIcon(os.path.join("icons", "app.svg"))
        self.setWindowIcon(app_icon)
        
        # Центрируем окно на экране
        self.center_window()
        
        # Загружаем настройки
        self.config = Config()
        
        # Используем путь к базе данных из настроек
        self.db = NotesDB(self.config.get_db_path())
        self.current_note_id = None
        self.current_parent_id = 1
        self.content_modified = False
        self.editing_title = False

        self.create_menu()
        self.create_toolbar()
        self.setup_ui()
        self.load_notes()
        self.setup_shortcuts()
        self.apply_settings()

    def center_window(self):
        """Центрирование окна на экране"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def setup_shortcuts(self):
        """Настройка горячих клавиш"""
        self.new_note_action.setShortcut("Insert")
        self.new_subnote_action.setShortcut("Alt+Insert")
        self.delete_note_action.setShortcut("Delete")

    def create_menu(self):
        """Создание главного меню"""
        menubar = self.menuBar()

        # Меню "Файл"
        file_menu = menubar.addMenu("Файл")
        
        self.new_note_action = QAction(QIcon(os.path.join("icons", "new_note.svg")), "Новая заметка (Insert)", self)
        self.new_note_action.triggered.connect(self.new_note)
        file_menu.addAction(self.new_note_action)
        
        self.new_subnote_action = QAction(QIcon(os.path.join("icons", "new_subnote.svg")), "Новая вложенная заметка (Alt+Insert)", self)
        self.new_subnote_action.triggered.connect(self.new_subnote)
        file_menu.addAction(self.new_subnote_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню "Настройки"
        settings_menu = menubar.addMenu("Настройки")
        settings_action = QAction("Параметры...", self)
        settings_action.triggered.connect(self.show_settings)
        settings_menu.addAction(settings_action)

        # Меню "Справка"
        help_menu = menubar.addMenu("Справка")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Создаем действия с иконками
        self.new_note_action = QAction(QIcon(os.path.join("icons", "new_note.svg")), "Новая заметка", self)
        self.new_note_action.setToolTip("Новая заметка (Insert)")
        self.new_note_action.triggered.connect(self.new_note)
        toolbar.addAction(self.new_note_action)

        self.new_subnote_action = QAction(QIcon(os.path.join("icons", "new_subnote.svg")), "Новая вложенная заметка", self)
        self.new_subnote_action.setToolTip("Новая вложенная заметка (Alt+Insert)")
        self.new_subnote_action.triggered.connect(self.new_subnote)
        toolbar.addAction(self.new_subnote_action)

        self.delete_note_action = QAction(QIcon(os.path.join("icons", "delete.svg")), "Удалить заметку", self)
        self.delete_note_action.setToolTip("Удалить заметку (Delete)")
        self.delete_note_action.triggered.connect(self.delete_note)
        toolbar.addAction(self.delete_note_action)

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Создаем главный layout
        main_layout = QHBoxLayout(central_widget)
        
        # Создаем сплиттер
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Создаем дерево заметок
        self.notes_tree = QTreeWidget()
        self.notes_tree.setHeaderHidden(True)  # Скрываем заголовок полностью
        self.notes_tree.itemSelectionChanged.connect(self.on_note_select)
        self.notes_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.notes_tree.customContextMenuRequested.connect(self.show_context_menu)
        splitter.addWidget(self.notes_tree)
        
        # Создаем правую панель
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Создаем заголовок заметки
        self.note_title = QLabel()
        self.note_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(self.note_title)
        
        # Создаем редактор заметки
        self.note_content = QTextEdit()
        self.note_content.textChanged.connect(self.on_content_modified)
        right_layout.addWidget(self.note_content)
        
        splitter.addWidget(right_panel)
        
        # Устанавливаем соотношение размеров
        splitter.setSizes([300, 700])

    def load_notes(self):
        """Загрузка заметок из базы данных"""
        self.notes_tree.clear()
        
        # Получаем все заметки из БД
        notes = self.db.get_notes(None)
        self.notes_dict = {note[0]: note for note in notes}
        
        # Создаем словарь для хранения элементов дерева
        tree_items = {}
        
        # Добавляем заметки в дерево
        for note in notes:
            note_id, title, content, parent_id, created_at, updated_at = note
            if note_id == 1:  # Пропускаем корневую заметку
                continue
                
            if parent_id == 1:  # Если это заметка верхнего уровня
                item = QTreeWidgetItem(self.notes_tree, [title])
                item.setData(0, Qt.ItemDataRole.UserRole, note_id)
                tree_items[note_id] = item
            elif parent_id in tree_items:  # Если это вложенная заметка
                item = QTreeWidgetItem(tree_items[parent_id], [title])
                item.setData(0, Qt.ItemDataRole.UserRole, note_id)
                tree_items[note_id] = item

    def select_note_by_id(self, note_id):
        def recursive_search(item):
            if item.data(0, Qt.ItemDataRole.UserRole) == note_id:
                self.notes_tree.setCurrentItem(item)
                self.notes_tree.scrollToItem(item)
                return True
            for i in range(item.childCount()):
                if recursive_search(item.child(i)):
                    return True
            return False

        for i in range(self.notes_tree.topLevelItemCount()):
            item = self.notes_tree.topLevelItem(i)
            if recursive_search(item):
                break

    def new_note(self):
        """Создать новую заметку"""
        try:
            note_id = self.db.add_note("Новая заметка", "", self.current_parent_id)
            self.load_notes()
            self.select_note_by_id(note_id)
            self.start_rename()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать заметку: {str(e)}")

    def new_subnote(self):
        """Создать новую вложенную заметку"""
        current_item = self.notes_tree.currentItem()
        if not current_item:
            return
        parent_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        try:
            note_id = self.db.add_note("Новая заметка", "", parent_id)
            self.load_notes()
            self.select_note_by_id(note_id)
            self.start_rename()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать заметку: {str(e)}")

    def save_current_note(self):
        """Сохранение текущей заметки"""
        if self.current_note_id and self.content_modified:
            content = self.note_content.toPlainText()
            try:
                note = self.db.get_note(self.current_note_id)
                if note:
                    self.db.update_note(self.current_note_id, note[1], content)
                    self.content_modified = False
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить заметку: {str(e)}")

    def delete_note(self):
        """Удаление заметки"""
        current_item = self.notes_tree.currentItem()
        if not current_item:
            return
            
        note_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        # Не позволяем удалить корневую заметку
        if note_id == 1:
            QMessageBox.warning(self, "Предупреждение", "Нельзя удалить корневую заметку")
            return
        
        reply = QMessageBox.question(self, "Подтверждение",
                                   "Вы уверены, что хотите удалить эту заметку?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_note(note_id)
                self.load_notes()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить заметку: {str(e)}")

    def on_note_select(self):
        """Обработка выбора заметки"""
        self.save_current_note()
        
        current_item = self.notes_tree.currentItem()
        if not current_item:
            return
            
        note_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        note = self.db.get_note(note_id)
        
        if note:
            self.current_note_id = note_id
            self.current_parent_id = note[3]
            self.note_title.setText(note[1])
            self.note_content.setPlainText(note[2])
            self.content_modified = False

    def show_context_menu(self, position):
        """Показ контекстного меню"""
        menu = QMenu()
        
        new_note_action = menu.addAction(QIcon(os.path.join("icons", "new_note.svg")), "Новая заметка")
        new_note_action.triggered.connect(self.new_note)
        
        new_subnote_action = menu.addAction(QIcon(os.path.join("icons", "new_subnote.svg")), "Новая вложенная заметка")
        new_subnote_action.triggered.connect(self.new_subnote)
        
        menu.addSeparator()
        
        delete_action = menu.addAction(QIcon(os.path.join("icons", "delete.svg")), "Удалить")
        delete_action.triggered.connect(self.delete_note)
        
        menu.exec(self.notes_tree.mapToGlobal(position))

    def on_content_modified(self):
        """Обработка изменения содержимого заметки"""
        self.content_modified = True

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.save_current_note()
        event.accept()

    def start_rename(self):
        """Начало переименования заметки"""
        current_item = self.notes_tree.currentItem()
        if not current_item:
            return
            
        self.editing_title = True
        current_item.setFlags(current_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.notes_tree.editItem(current_item, 0)

    def show_about(self):
        """Показ информации о программе"""
        QMessageBox.about(self, "О программе",
                         "SkimNote - Менеджер заметок\n\n"
                         "Версия 1.0\n\n"
                         "Простой и удобный менеджер заметок с поддержкой "
                         "иерархической структуры.")

    def show_settings(self):
        """Показ диалога настроек"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.apply_settings()

    def apply_settings(self):
        """Применение настроек"""
        # Если путь к базе данных изменился, пересоздать NotesDB
        db_path = self.config.get_db_path()
        if self.db and getattr(self.db, 'db_path', None) != db_path:
            self.db = NotesDB(db_path)
            self.load_notes()
        # Здесь можно добавить применение других настроек к интерфейсу
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NotesApp()
    window.show()
    sys.exit(app.exec()) 