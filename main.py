import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTreeWidget, QTreeWidgetItem, QTextEdit,
                            QPushButton, QMenu, QMessageBox, QInputDialog, QToolBar,
                            QLabel, QSplitter, QDialog, QLineEdit, QFormLayout,
                            QCheckBox, QSpinBox, QComboBox, QFileDialog, QGroupBox,
                            QListWidget)
from PyQt6.QtCore import Qt, QSize, QSettings
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFontDatabase, QFont
from database import NotesDB
from config import Config
from settings_dialog import SettingsDialog
import os
import sqlite3
import configparser
import shutil
from datetime import datetime, timedelta
import socket

# Константы
ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons')
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.ini')

class SearchDialog(QDialog):
    def __init__(self, parent=None, replace_mode=False, title=None):
        super().__init__(parent)
        self.setWindowTitle(title if title else ("Найти и заменить" if replace_mode else "Найти"))
        self.setModal(True)
        
        layout = QFormLayout(self)
        
        # Поле поиска
        self.search_edit = QLineEdit()
        layout.addRow("Найти:", self.search_edit)
        
        # Поле замены (только в режиме замены)
        if replace_mode:
            self.replace_edit = QLineEdit()
            layout.addRow("Заменить на:", self.replace_edit)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        self.find_button = QPushButton("Найти")
        self.find_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.find_button)
        
        if replace_mode:
            self.replace_button = QPushButton("Заменить")
            self.replace_button.clicked.connect(self.accept)
            buttons_layout.addWidget(self.replace_button)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addRow("", buttons_layout)
        
        # Устанавливаем фокус на поле поиска
        self.search_edit.setFocus()

class NotesApp(QMainWindow):
    SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.ini')

    def __init__(self):
        super().__init__()
        
        # Инициализация основных переменных
        self.init_ui()
        
        # Определяем путь к файлу настроек
        if getattr(sys, 'frozen', False):
            # Если приложение запущено как exe
            self.SETTINGS_FILE = os.path.join(os.path.dirname(sys.executable), 'settings.ini')
        else:
            # Если приложение запущено из исходников
            self.SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.ini')
        
        # Загружаем текущий язык интерфейса
        config = Config()
        self.current_language = config.get('language', 'Русский')
        
        # Проверяем наличие файла настроек и устанавливаем размеры окна
        if os.path.exists(self.SETTINGS_FILE):
            try:
                # Загружаем настройки из файла
                config = configparser.ConfigParser()
                config.read(self.SETTINGS_FILE, encoding='utf-8')
                
                # Загружаем размеры и позицию окна
                x = config.getint('Window', 'x', fallback=100)
                y = config.getint('Window', 'y', fallback=100)
                width = config.getint('Window', 'width', fallback=800)
                height = config.getint('Window', 'height', fallback=600)
                
                # Устанавливаем позицию и размер окна
                self.setGeometry(x, y, width, height)
                
                # Загружаем остальные настройки
                self.font_size = config.getint('Font', 'size', fallback=12)
                self.font_family = config.get('Font', 'family', fallback='Segoe UI')
                db_path = config.get('Database', 'path', fallback='notes.db')
                
                # Инициализируем базу данных
                self.init_db(db_path)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить настройки!\n{str(e)}")
                self.set_default_settings()
        else:
            self.set_default_settings()
        
        # Настройка интерфейса
        self.create_actions()
        self.setup_ui()
        
        # Устанавливаем заголовок окна в зависимости от языка
        if self.current_language == 'English':
            self.setWindowTitle('SkimNote')
        else:
            self.setWindowTitle('SkimNote')
            
        self.setWindowIcon(QIcon(os.path.join(ICONS_DIR, 'app.ico')))
        
        # Применяем тему
        self.apply_theme()
        
        # Показываем окно
        self.show()

    def init_ui(self):
        """Инициализация основных переменных и настроек интерфейса"""
        # Инициализация основных переменных
        self.default_width = 800
        self.default_height = 600
        self.font_size = 12
        self.font_family = "Segoe UI"
        self.db = None  # Инициализация будет в load_settings

        # Инициализация переменных состояния
        self.current_note_id = None
        self.current_parent_id = 1
        self.content_modified = False
        self.editing_title = False
        self.last_search_text = ""
        self.last_replace_text = ""
        self.restored_geometry = False

    def init_db(self, db_path='notes.db'):
        """Инициализация базы данных"""
        self.db = NotesDB(db_path)

    def load_settings(self):
        """Загрузка настроек из файла"""
        import configparser
        config = configparser.ConfigParser()
        
        if os.path.exists(self.SETTINGS_FILE):
            config.read(self.SETTINGS_FILE, encoding='utf-8')
            self.font_size = int(config.get('main', 'font_size', fallback='12'))
            self.font_family = config.get('main', 'font_family', fallback='Segoe UI')
            db_path = config.get('main', 'db_path', fallback='notes.db')
            
            # Инициализируем базу данных с путем из настроек
            if self.db is None or self.db.db_path != db_path:
                self.init_db(db_path)
        else:
            # Используем значения по умолчанию
            self.font_size = 12
            self.font_family = "Segoe UI"
            self.init_db('notes.db')

    def create_actions(self):
        """Создание действий для меню и панели инструментов"""
        # Действия для файлового меню
        self.change_db_action = QAction("Сменить базу данных", self)
        self.change_db_action.triggered.connect(self.change_db)
        
        self.restore_db_action = QAction("Восстановление базы данных", self)
        self.restore_db_action.triggered.connect(self.restore_db)
        
        self.exit_action = QAction("Выход", self)
        self.exit_action.setShortcut("Alt+F4")
        self.exit_action.triggered.connect(self.close)
        
        # Действия для меню заметок
        self.new_note_action = QAction("Новая заметка", self)
        icon_path = os.path.join(ICONS_DIR, "new_note.svg")
        if os.path.exists(icon_path):
            self.new_note_action.setIcon(QIcon(icon_path))
        self.new_note_action.setShortcut("Insert")
        self.new_note_action.triggered.connect(self.new_note)
        
        self.new_subnote_action = QAction("Новая вложенная заметка", self)
        icon_path = os.path.join(ICONS_DIR, "new_subnote.svg")
        if os.path.exists(icon_path):
            self.new_subnote_action.setIcon(QIcon(icon_path))
        self.new_subnote_action.setShortcut("Alt+Insert")
        self.new_subnote_action.triggered.connect(self.new_subnote)
        
        self.delete_note_action = QAction("Удалить заметку", self)
        icon_path = os.path.join(ICONS_DIR, "delete.svg")
        if os.path.exists(icon_path):
            self.delete_note_action.setIcon(QIcon(icon_path))
        self.delete_note_action.setShortcut("Delete")
        self.delete_note_action.triggered.connect(self.delete_note)
        
        # Действия для поиска
        self.find_action = QAction("Найти", self)
        self.find_action.setShortcut("Ctrl+F")
        self.find_action.triggered.connect(self.show_search_dialog)
        
        self.find_next_action = QAction("Найти далее", self)
        self.find_next_action.setShortcut("F3")
        self.find_next_action.triggered.connect(self.find_next)
        
        self.replace_action = QAction("Заменить", self)
        self.replace_action.setShortcut("Ctrl+H")
        self.replace_action.triggered.connect(self.show_replace_dialog)
        
        # Действия для перемещения заметок
        self.move_up_action = QAction("Переместить вверх", self)
        self.move_up_action.setShortcut("Ctrl+Up")
        self.move_up_action.triggered.connect(self.move_note_up)
        
        self.move_down_action = QAction("Переместить вниз", self)
        self.move_down_action.setShortcut("Ctrl+Down")
        self.move_down_action.triggered.connect(self.move_note_down)

    def apply_font(self):
        """Применение шрифта ко всем основным элементам интерфейса"""
        font = QFont(self.font_family, self.font_size)
        if hasattr(self, 'editor'):
            self.editor.setFont(font)
        if hasattr(self, 'tree'):
            self.tree.setFont(font)
        if hasattr(self, 'db_path_edit'):
            self.db_path_edit.setFont(font)

    def apply_theme(self):
        """Применение темы к элементам интерфейса"""
        # Применяем шрифт
        self.apply_font()
        
        # Если в будущем потребуется добавить другие настройки темы,
        # их можно будет добавить здесь (цвета, стили и т.д.)

    def setup_shortcuts(self):
        """Настройка горячих клавиш"""
        # self.new_note_action.setShortcut("Insert")
        # self.new_subnote_action.setShortcut("Alt+Insert")
        # self.delete_note_action.setShortcut("Delete")
        # self.find_action.setShortcut("Ctrl+F")
        # self.find_next_action.setShortcut("F3")
        # self.replace_action.setShortcut("Alt+F3")

    def create_menu(self):
        """Создание меню"""
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu("Файл")
        
        # --- Новый пункт ---
        change_db_action = QAction("Сменить базу данных", self)
        change_db_action.triggered.connect(self.change_db)
        file_menu.addAction(change_db_action)
        # --- Конец нового пункта ---
        
        # --- Новый пункт для восстановления базы данных ---
        restore_db_action = QAction("Восстановление базы данных", self)
        restore_db_action.triggered.connect(self.restore_db)
        file_menu.addAction(restore_db_action)
        # --- Конец нового пункта ---
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Заметки"
        notes_menu = menubar.addMenu("Заметки")
        
        # Переносим сюда пункты создания заметок
        new_note_action = QAction("Новая заметка", self)
        new_note_action.setShortcut("Insert")
        new_note_action.triggered.connect(self.new_note)
        notes_menu.addAction(new_note_action)
        
        new_subnote_action = QAction("Новая вложенная заметка", self)
        new_subnote_action.setShortcut("Alt+Insert")
        new_subnote_action.triggered.connect(self.new_subnote)
        notes_menu.addAction(new_subnote_action)
        
        notes_menu.addSeparator()

        # --- Новый пункт: Переместить вверх ---
        move_up_action = QAction("Переместить вверх", self)
        move_up_action.setShortcut("Ctrl+Up")
        move_up_action.triggered.connect(self.move_note_up)
        notes_menu.addAction(move_up_action)

        # --- Новый пункт: Переместить вниз ---
        move_down_action = QAction("Переместить вниз", self)
        move_down_action.setShortcut("Ctrl+Down")
        move_down_action.triggered.connect(self.move_note_down)
        notes_menu.addAction(move_down_action)

        notes_menu.addSeparator()

        find_action = QAction("Найти", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.show_search_dialog)
        notes_menu.addAction(find_action)
        
        find_next_action = QAction("Найти далее", self)
        find_next_action.setShortcut("F3")
        find_next_action.triggered.connect(self.handle_f3)
        notes_menu.addAction(find_next_action)
        
        replace_action = QAction("Найти и заменить", self)
        replace_action.setShortcut("Alt+F3")
        replace_action.triggered.connect(self.show_replace_dialog)
        notes_menu.addAction(replace_action)
        
        replace_all_action = QAction("Заменить все", self)
        replace_all_action.triggered.connect(self.show_replace_all_dialog)
        notes_menu.addAction(replace_all_action)
        
        notes_menu.addSeparator()
        
        delete_action = QAction("Удалить заметку", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_note)
        notes_menu.addAction(delete_action)
        
        # Меню "Настройки"
        settings_menu = menubar.addMenu("Настройки")
        
        settings_action = QAction("Настройки", self)
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
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.addToolBar(toolbar)
        
        # Новая заметка
        new_note_action = QAction("Новая заметка", self)
        icon_path = os.path.join(ICONS_DIR, "new_note.png")
        if os.path.exists(icon_path):
            new_note_action.setIcon(QIcon(icon_path))
        new_note_action.triggered.connect(self.new_note)
        toolbar.addAction(new_note_action)
        
        # Новая вложенная заметка
        new_subnote_action = QAction("Новая вложенная заметка", self)
        icon_path = os.path.join(ICONS_DIR, "new_subnote.png")
        if os.path.exists(icon_path):
            new_subnote_action.setIcon(QIcon(icon_path))
        new_subnote_action.triggered.connect(self.new_subnote)
        toolbar.addAction(new_subnote_action)
        
        # Удалить заметку
        delete_action = QAction("Удалить заметку", self)
        icon_path = os.path.join(ICONS_DIR, "delete.png")
        if os.path.exists(icon_path):
            delete_action.setIcon(QIcon(icon_path))
        delete_action.triggered.connect(self.delete_note)
        toolbar.addAction(delete_action)

    def setup_ui(self):
        """Настройка интерфейса"""
        # Создаем главный виджет и layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Создаем левую панель с деревом заметок
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Создаем дерево заметок
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)  # Скрываем заголовок
        self.tree.itemClicked.connect(self.on_note_selected)
        self.tree.itemDoubleClicked.connect(self.on_note_double_clicked)
        self.tree.currentItemChanged.connect(self.on_note_selected)
        self.tree.itemChanged.connect(self.on_item_changed)
        left_layout.addWidget(self.tree)
        
        # Добавляем левую панель в главный layout
        layout.addWidget(left_panel, 1)
        
        # Создаем правую панель с редактором
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Создаем редактор
        self.editor = QTextEdit()
        self.editor.textChanged.connect(self.on_text_changed)
        right_layout.addWidget(self.editor)
        
        # Добавляем правую панель в главный layout
        layout.addWidget(right_panel, 2)
        
        # Создаем меню
        self.create_menu()
        
        # Создаем панель инструментов
        self.create_toolbar()
        
        # Загружаем заметки
        self.load_notes()

    def load_notes(self):
        """Загрузка заметок из базы данных"""
        self.tree.clear()
        
        # Получаем все заметки из БД
        notes = self.db.get_all_notes()
        
        # Создаем словарь для быстрого доступа к элементам дерева
        tree_items = {}
        
        # Сначала создаем все элементы дерева верхнего уровня
        for note in notes:
            note_id, title, content, parent_id, order_index = note
            
            if parent_id == 1:  # Если это заметка верхнего уровня
                item = QTreeWidgetItem(self.tree, [title])
                item.setData(0, Qt.ItemDataRole.UserRole, note_id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)  # Делаем элемент редактируемым
                tree_items[note_id] = item
        
        # Затем добавляем дочерние элементы
        for note in notes:
            note_id, title, content, parent_id, order_index = note
            
            if parent_id != 1:  # Если это вложенная заметка
                parent_item = tree_items.get(parent_id)
                if parent_item:
                    item = QTreeWidgetItem(parent_item, [title])
                    item.setData(0, Qt.ItemDataRole.UserRole, note_id)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)  # Делаем элемент редактируемым
                    tree_items[note_id] = item
        
        # Раскрываем все элементы дерева
        self.tree.expandAll()
        
        # Выбираем первую заметку, если она есть
        if self.tree.topLevelItemCount() > 0:
            first_item = self.tree.topLevelItem(0)
            self.tree.setCurrentItem(first_item)
            self.on_note_selected(first_item)

    def select_note_by_id(self, note_id):
        def recursive_search(item):
            if item.data(0, Qt.ItemDataRole.UserRole) == note_id:
                self.tree.setCurrentItem(item)
                self.tree.scrollToItem(item)
                return True
            for i in range(item.childCount()):
                if recursive_search(item.child(i)):
                    return True
            return False

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if recursive_search(item):
                break

    def new_note(self):
        """Создать новую заметку"""
        try:
            note_id = self.db.add_note("Новая заметка", "", self.current_parent_id)
            self.load_notes()
            self.select_note_by_id(note_id)
            self.current_note_id = note_id  # Явно устанавливаем текущий note_id
            self.editor.clear()
            self.content_modified = False
            self.start_rename()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать заметку: {str(e)}")

    def new_subnote(self):
        """Создать новую вложенную заметку"""
        current_item = self.tree.currentItem()
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
        if not self.current_note_id or not self.content_modified:
            return
            
        content = self.editor.toPlainText()
        
        try:
            # Получаем текущую заметку
            note = self.db.get_note(self.current_note_id)
            if note:
                # Сохраняем с тем же заголовком
                self.db.save_note(self.current_note_id, note[1], content)
                self.content_modified = False
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить заметку: {str(e)}")

    def delete_note(self):
        """Удаление заметки"""
        current_item = self.tree.currentItem()
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

    def on_note_selected(self, item):
        """Обработка выбора заметки"""
        # Сохраняем предыдущую заметку
        if self.current_note_id and self.content_modified:
            self.save_current_note()
        
        if not item:
            return
            
        note_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not note_id:
            return
            
        # Получаем данные заметки из базы
        note = self.db.get_note(note_id)
        if not note:
            return
            
        # Отображаем текст заметки
        self.editor.setPlainText(note[2])  # content
        
        # Сохраняем ID текущей заметки и родителя
        self.current_note_id = note_id
        self.current_parent_id = note[3]  # parent_id
        
        # Сбрасываем флаг изменения
        self.content_modified = False

    def on_note_double_clicked(self, item, column):
        """Обработка двойного клика по заметке"""
        if column == 0:  # Только для заголовка
            self.tree.editItem(item, column)

    def show_context_menu(self, position):
        """Показ контекстного меню"""
        menu = QMenu()
        
        new_note_action = menu.addAction(QIcon(os.path.join(ICONS_DIR, "new_note.png")), "Новая заметка")
        new_note_action.triggered.connect(self.new_note)
        
        new_subnote_action = menu.addAction(QIcon(os.path.join(ICONS_DIR, "new_subnote.png")), "Новая вложенная заметка")
        new_subnote_action.triggered.connect(self.new_subnote)
        
        menu.addSeparator()
        
        delete_action = menu.addAction(QIcon(os.path.join(ICONS_DIR, "delete.png")), "Удалить")
        delete_action.triggered.connect(self.delete_note)
        
        menu.exec(self.tree.mapToGlobal(position))

    def on_text_changed(self):
        """Обработчик изменения текста"""
        self.content_modified = True

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        # Сохраняем текущую заметку
        self.save_current_note()
        
        # Сохраняем настройки
        self.save_window_settings()
        
        event.accept()

    def start_rename(self):
        """Начать редактирование заголовка"""
        current_item = self.tree.currentItem()
        if current_item:
            self.tree.setEditTriggers(QTreeWidget.EditTrigger.DoubleClicked | QTreeWidget.EditTrigger.EditKeyPressed)
            self.tree.editItem(current_item, 0)
            self.tree.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)

    def show_about(self):
        """Показать информацию о программе"""
        about_text = (
            "SkimNote - программа для создания заметок<br><br>"
            "Версия 1.0<br><br>"
            "Сайт:<br>"
            "<a href='https://progtips.ru/skimnote'>https://progtips.ru/skimnote</a><br><br>"
            "© 2025 Все права защищены"
        )
        msg = QMessageBox(self)
        msg.setWindowTitle("О программе")
        msg.setText(about_text)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def select_db_file(self, dialog):
        """Выбор файла базы данных"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл базы данных",
            "",
            "SQLite Database (*.db);;All Files (*.*)"
        )
        if file_name:
            self.db_path_edit.setText(file_name)
            
    def show_settings(self):
        """Показать диалог настроек"""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Применяем новые настройки
            self.font_size = dialog.font_size.value()
            self.font_family = 'Segoe UI'  # Можно добавить выбор шрифта в настройки
            self.apply_font()
            
            # Проверяем, изменился ли язык
            config = Config()
            new_language = config.get('language', 'Русский')
            if new_language != self.current_language:
                self.current_language = new_language
                QMessageBox.information(self, "Изменение языка", 
                    "Для применения нового языка интерфейса необходимо перезапустить приложение.")
            
            # Применяем тему
            self.apply_theme()

    def handle_f3(self):
        """Обработка нажатия F3"""
        if not hasattr(self, 'search_results') or not self.search_results:
            self.show_search_dialog()
        else:
            self.find_next()

    def show_search_dialog(self):
        """Показать диалог поиска"""
        dialog = SearchDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            search_text = dialog.search_edit.text()
            if search_text:
                self.last_search_text = search_text
                self.collect_search_results(search_text)
                self.find_next()
        else:
            if hasattr(self, 'search_results'):
                delattr(self, 'search_results')

    def collect_search_results(self, text):
        """Собирает все вхождения текста по всем заметкам"""
        self.search_results = []  # (note_id, start, end)
        for note_id, note in self.notes_dict.items():
            if note_id == 1:
                continue
            content = note[2]  # content
            idx = 0
            while True:
                idx = content.find(text, idx)
                if idx == -1:
                    break
                self.search_results.append((note_id, idx, idx+len(text)))
                idx += len(text) if len(text) > 0 else 1
        self.search_result_index = -1

    def find_next(self):
        """Переходит к следующему найденному вхождению"""
        if not hasattr(self, 'search_results') or not self.search_results:
            if hasattr(self, 'last_search_text') and self.last_search_text:
                self.collect_search_results(self.last_search_text)
            else:
                QMessageBox.information(self, "Поиск", "Нет результатов поиска")
                return
        if not self.search_results:
            QMessageBox.information(self, "Поиск", "Текст не найден")
            return
        self.search_result_index = (getattr(self, 'search_result_index', -1) + 1) % len(self.search_results)
        note_id, start, end = self.search_results[self.search_result_index]
        self.select_note_by_id(note_id)
        # выделяем найденный текст
        self.highlight_in_note(start, end)

    def highlight_in_note(self, start, end):
        cursor = self.editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, cursor.MoveMode.KeepAnchor)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def find_text(self, text):
        """Поиск текста по всем заметкам и переход к первому вхождению"""
        self.collect_search_results(text)
        self.find_next()

    def replace_text(self, search_text, replace_text):
        """Замена первого найденного вхождения по всем заметкам"""
        self.collect_search_results(search_text)
        if not self.search_results:
            QMessageBox.information(self, "Замена", "Текст не найден")
            return
        note_id, start, end = self.search_results[0]
        self.select_note_by_id(note_id)
        # заменяем текст
        content = self.editor.toPlainText()
        new_content = content[:start] + replace_text + content[end:]
        self.editor.setPlainText(new_content)
        self.on_text_changed()
        # после замены обновляем результаты поиска
        self.collect_search_results(search_text)

    def show_replace_dialog(self):
        """Показать диалог замены"""
        dialog = SearchDialog(self, replace_mode=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            search_text = dialog.search_edit.text()
            replace_text = dialog.replace_edit.text()
            if search_text:
                self.last_search_text = search_text
                self.last_replace_text = replace_text
                self.replace_text(search_text, replace_text)

    def replace_all(self, search_text, replace_text):
        """Заменяет все вхождения текста по всем заметкам"""
        self.collect_search_results(search_text)
        if not self.search_results:
            QMessageBox.information(self, "Замена", "Текст не найден")
            return
        # Сортируем результаты по note_id и индексу, чтобы заменять с конца
        self.search_results.sort(key=lambda x: (x[0], -x[1]), reverse=True)
        for note_id, start, end in self.search_results:
            self.select_note_by_id(note_id)
            content = self.editor.toPlainText()
            new_content = content[:start] + replace_text + content[end:]
            self.editor.setPlainText(new_content)
            self.on_text_changed()
        QMessageBox.information(self, "Замена", "Заменено вхождений: " + str(len(self.search_results)))

    def show_replace_all_dialog(self):
        """Показать диалог замены всех вхождений"""
        dialog = SearchDialog(self, replace_mode=True, title="Заменить все")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            search_text = dialog.search_edit.text()
            replace_text = dialog.replace_edit.text()
            if search_text:
                self.last_search_text = search_text
                self.last_replace_text = replace_text
                self.collect_search_results(search_text)
                self.replace_all(search_text, replace_text)

    def get_all_notes(self):
        """Получение всех заметок"""
        self.cursor.execute("SELECT id, title, content, parent_id FROM notes ORDER BY id")
        return self.cursor.fetchall()
        
    def get_note(self, note_id):
        """Получение заметки по ID"""
        self.cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        return self.cursor.fetchone()

    def center_on_screen(self):
        """Центрирование окна на экране"""
        # Получаем геометрию основного экрана
        screen = QApplication.primaryScreen().geometry()
        # Получаем размеры окна
        size = self.geometry()
        # Вычисляем позицию для центрирования
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        # Перемещаем окно
        self.move(x, y)

    def change_db(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите файл базы данных", "", "SQLite Database (*.db);;All Files (*.*)")
        if file_name:
            self.save_settings_dialog_db_path(file_name)

    def save_settings_dialog_db_path(self, db_path):
        # Сохраняем только путь к базе данных, остальные настройки не трогаем
        config = configparser.ConfigParser()
        config.read(self.SETTINGS_FILE, encoding='utf-8')
        if 'main' not in config:
            config['main'] = {}
        config['main']['db_path'] = db_path
        with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
            config.write(f)
        self.db.close()
        self.db = NotesDB(db_path)
        self.load_notes()

    def backup_db(self):
        """Регулярный бэкап базы данных"""
        # Изменяем путь к папке backup, чтобы она всегда создавалась в папке с файлом exe
        if getattr(sys, 'frozen', False):
            backup_dir = os.path.join(os.path.dirname(sys.executable), "backup")
        else:
            backup_dir = os.path.join(os.path.dirname(sys.executable), "backup")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        db_path = self.db.db_path
        db_name = os.path.basename(db_path)
        today_str = datetime.now().strftime("%Y%m%d")
        # Проверяем, есть ли уже бэкап за сегодня
        for filename in os.listdir(backup_dir):
            if filename.startswith(db_name) and filename.endswith(".db") and today_str in filename:
                # Уже есть бэкап за сегодня
                break
        else:
            # Нет бэкапа за сегодня — создаём
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{db_name}_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            if not os.path.exists(backup_path):
                shutil.copy2(db_path, backup_path)
        # Удаляем бэкапы старше 10 дней
        for filename in os.listdir(backup_dir):
            if filename.startswith(db_name) and filename.endswith(".db"):
                file_path = os.path.join(backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if datetime.now() - file_time > timedelta(days=10):
                    os.remove(file_path)
    
    def restore_db(self):
        """Восстановление базы данных из бэкапа"""
        # Изменяем путь к папке backup, чтобы она всегда создавалась в папке с файлом exe
        if getattr(sys, 'frozen', False):
            # Если программа собрана в exe, используем папку, откуда запущен exe
            backup_dir = os.path.join(os.path.dirname(sys.executable), "backup")
        else:
            # Если программа запущена из исходников, используем папку, откуда запущен exe
            backup_dir = os.path.join(os.path.dirname(sys.executable), "backup")
        
        if not os.path.exists(backup_dir):
            QMessageBox.warning(self, "Восстановление", "Папка с бэкапами не найдена.")
            return
        
        # Получаем список файлов бэкапов
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith(".db")]
        if not backup_files:
            QMessageBox.warning(self, "Восстановление", "Бэкапы не найдены.")
            return
        
        # Сортируем файлы по дате создания (от новых к старым)
        backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
        
        # Создаем диалог выбора файла
        dialog = QDialog(self)
        dialog.setWindowTitle("Выберите бэкап для восстановления")
        layout = QVBoxLayout(dialog)
        
        list_widget = QListWidget()
        for file in backup_files:
            list_widget.addItem(file)
        layout.addWidget(list_widget)
        
        buttons = QHBoxLayout()
        ok_button = QPushButton("Восстановить")
        cancel_button = QPushButton("Отмена")
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_file = list_widget.currentItem().text()
            backup_path = os.path.join(backup_dir, selected_file)
            
            # Выдаем предупреждение перед восстановлением
            reply = QMessageBox.question(self, "Восстановление", "Текущая база данных будет удалена. Продолжать восстановление?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
            
            # Получаем путь к основной базе данных из настроек
            import configparser
            config = configparser.ConfigParser()
            config.read(self.SETTINGS_FILE, encoding='utf-8')
            main_db_path = config.get('main', 'db_path', fallback=self.db.db_path)
            QMessageBox.information(self, "Отладка", f"Путь к базе данных: {main_db_path}")
            
            # Закрываем текущее соединение с базой данных
            self.db.close()
            
            # Копируем выбранный бэкап на место основной базы данных
            shutil.copy2(backup_path, main_db_path)
            
            # Пересоздаем соединение с базой данных
            self.db = NotesDB(main_db_path)
            
            # Сброс состояния и очистка интерфейса
            self.current_note_id = None
            self.current_parent_id = 1
            self.content_modified = False
            self.editing_title = False
            self.last_search_text = ""
            self.last_replace_text = ""
            self.editor.clear()
            self.tree.clear()
            self.load_notes()
            
            QMessageBox.information(self, "Восстановление", "База данных успешно восстановлена.")

    def keyPressEvent(self, event):
        """Обработка нажатия клавиш"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Up and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.move_note_up()
        elif event.key() == Qt.Key.Key_Down and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.move_note_down()
        elif event.key() == Qt.Key.Key_F2:
            current_item = self.tree.currentItem()
            if current_item:
                self.tree.editItem(current_item, 0)
        else:
            super().keyPressEvent(event)

    def on_item_changed(self, item, column):
        """Обработка изменения элемента дерева"""
        if not item or column != 0:
            return
            
        note_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not note_id:
            return
            
        new_title = item.text(0)
        try:
            # Получаем текущую заметку
            note = self.db.get_note(note_id)
            if note:
                # Сохраняем с новым заголовком
                self.db.save_note(note_id, new_title, note[2])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить заголовок: {str(e)}")

    def move_note_up(self):
        """Переместить заметку вверх среди соседей"""
        item = self.tree.currentItem()
        if not item:
            return
        parent = item.parent() or self.tree.invisibleRootItem()
        index = parent.indexOfChild(item)
        if index > 0:
            # Получаем ID заметок для обновления порядка
            current_id = item.data(0, Qt.ItemDataRole.UserRole)
            prev_item = parent.child(index - 1)
            prev_id = prev_item.data(0, Qt.ItemDataRole.UserRole)
            
            # Обновляем порядок в базе данных
            self.db.update_note_order(current_id, index - 1)
            self.db.update_note_order(prev_id, index)
            
            # Обновляем отображение
            parent.takeChild(index)
            parent.insertChild(index - 1, item)
            self.tree.setCurrentItem(item)

    def move_note_down(self):
        """Переместить заметку вниз среди соседей"""
        item = self.tree.currentItem()
        if not item:
            return
        parent = item.parent() or self.tree.invisibleRootItem()
        index = parent.indexOfChild(item)
        if 0 <= index < parent.childCount() - 1:
            # Получаем ID заметок для обновления порядка
            current_id = item.data(0, Qt.ItemDataRole.UserRole)
            next_item = parent.child(index + 1)
            next_id = next_item.data(0, Qt.ItemDataRole.UserRole)
            
            # Обновляем порядок в базе данных
            self.db.update_note_order(current_id, index + 1)
            self.db.update_note_order(next_id, index)
            
            # Обновляем отображение
            parent.takeChild(index)
            parent.insertChild(index + 1, item)
            self.tree.setCurrentItem(item)

    def on_title_changed(self):
        """Обработчик изменения заголовка"""
        if not self.current_note_id:
            return
            
        # Обновляем заголовок в дереве
        current_item = self.tree.currentItem()
        if current_item:
            current_item.setText(0, self.title_input.text())
            self.content_modified = True
            # Сохраняем изменения в базу данных
            self.save_current_note()

    def save_window_settings(self):
        """Сохранение настроек окна и других параметров в файл"""
        config = configparser.ConfigParser()
        
        # Сохраняем размеры и позицию окна
        config['Window'] = {
            'x': str(self.x()),
            'y': str(self.y()),
            'width': str(self.width()),
            'height': str(self.height())
        }
        
        # Сохраняем настройки шрифта
        config['Font'] = {
            'size': str(self.font_size),
            'family': self.font_family
        }
        
        # Сохраняем путь к базе данных
        config['Database'] = {
            'path': self.db.db_path
        }
        
        # Создаем директорию для файла настроек, если она не существует
        settings_dir = os.path.dirname(self.SETTINGS_FILE)
        if not os.path.exists(settings_dir):
            try:
                os.makedirs(settings_dir)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать директорию для настроек!\n{str(e)}")
                return
        
        # Сохраняем файл
        try:
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                config.write(f)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить настройки!\n{str(e)}")

    def set_default_settings(self):
        """Установка настроек по умолчанию"""
        # Устанавливаем значения по умолчанию
        self.setGeometry(100, 100, 800, 600)
        self.center_on_screen()
        self.font_size = 12
        self.font_family = 'Segoe UI'
        self.init_db('notes.db')
        
        # Создаем файл настроек со значениями по умолчанию
        self.save_window_settings()

if __name__ == '__main__':
    # Проверка на единственный экземпляр программы
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', 12345))
    except socket.error:
        QMessageBox.critical(None, "Ошибка", "Программа уже запущена")
        sys.exit(1)
        
    app = QApplication(sys.argv)
    window = NotesApp()
    window.show()
    sys.exit(app.exec()) 