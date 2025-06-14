import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTreeWidget, QTreeWidgetItem, QTextEdit,
                            QPushButton, QMenu, QMessageBox, QInputDialog, QToolBar,
                            QLabel, QSplitter, QDialog, QLineEdit, QFormLayout,
                            QCheckBox, QSpinBox, QComboBox, QFileDialog)
from PyQt6.QtCore import Qt, QSize, QSettings
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFontDatabase
from database import NotesDB
from config import Config
from settings_dialog import SettingsDialog
import os
import sqlite3

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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SkimNote")
        self.setWindowIcon(QIcon(os.path.join("icons", "app.ico")))
        self.setMinimumSize(800, 600)
        
        # Загружаем настройки
        self.settings = QSettings("SkimNote", "SkimNote")
        self.load_settings()
        
        # Инициализируем базу данных
        self.db = NotesDB()
        self.current_note_id = None
        self.current_parent_id = 1
        self.content_modified = False
        self.editing_title = False
        self.last_search_text = ""
        self.last_replace_text = ""
        
        # Применяем тему
        self.apply_theme()
        
        # Создаем UI элементы
        self.setup_ui()
        self.create_toolbar()  # Создаем панель инструментов до настройки горячих клавиш
        self.setup_shortcuts()  # Настраиваем горячие клавиши после создания действий
        
        # Загружаем заметки
        self.load_notes()

    def load_settings(self):
        """Загрузка настроек"""
        self.dark_theme = self.settings.value("dark_theme", False, type=bool)
        self.font_size = self.settings.value("font_size", 12, type=int)
        self.font_family = self.settings.value("font_family", "Segoe UI", type=str)

    def apply_theme(self):
        """Применение темы"""
        if self.dark_theme:
            # Темная тема
            self.setStyleSheet("""
                QMainWindow, QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTreeWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #3f3f3f;
                }
                QTreeWidget::item {
                    padding: 4px;
                }
                QTreeWidget::item:selected {
                    background-color: #3f3f3f;
                }
                QTextEdit {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #3f3f3f;
                }
                QToolBar {
                    background-color: #2b2b2b;
                    border: none;
                }
                QToolButton {
                    background-color: transparent;
                    border: none;
                    padding: 4px;
                }
                QToolButton:hover {
                    background-color: #3f3f3f;
                }
                QMenuBar {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMenuBar::item {
                    background-color: transparent;
                }
                QMenuBar::item:selected {
                    background-color: #3f3f3f;
                }
                QMenu {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMenu::item {
                    background-color: transparent;
                }
                QMenu::item:selected {
                    background-color: #3f3f3f;
                }
                QPushButton {
                    background-color: #3f3f3f;
                    color: #ffffff;
                    border: 1px solid #5f5f5f;
                    padding: 5px 15px;
                }
                QPushButton:hover {
                    background-color: #4f4f4f;
                }
                QLineEdit {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #3f3f3f;
                    padding: 4px;
                }
                QLabel {
                    color: #ffffff;
                }
            """)
        else:
            # Светлая тема
            self.setStyleSheet("")

    def setup_shortcuts(self):
        """Настройка горячих клавиш"""
        self.new_note_action.setShortcut("Insert")
        self.new_subnote_action.setShortcut("Alt+Insert")
        self.delete_note_action.setShortcut("Delete")
        self.find_action.setShortcut("Ctrl+F")
        self.find_next_action.setShortcut("F3")
        self.replace_action.setShortcut("Alt+F3")

    def create_menu(self):
        """Создание меню"""
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu("Файл")
        
        new_note_action = QAction("Новая заметка", self)
        new_note_action.setShortcut("Insert")
        new_note_action.triggered.connect(self.new_note)
        file_menu.addAction(new_note_action)
        
        new_subnote_action = QAction("Новая вложенная заметка", self)
        new_subnote_action.setShortcut("Alt+Insert")
        new_subnote_action.triggered.connect(self.new_subnote)
        file_menu.addAction(new_subnote_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Заметки"
        notes_menu = menubar.addMenu("Заметки")
        
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
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)  # Показывать только иконки
        self.addToolBar(toolbar)
        
        # Новая заметка
        self.new_note_action = QAction(QIcon(os.path.join("icons", "new_note.svg")), "Новая заметка", self)
        self.new_note_action.setToolTip("Новая заметка (Insert)")
        self.new_note_action.triggered.connect(self.new_note)
        toolbar.addAction(self.new_note_action)
        
        # Новая вложенная заметка
        self.new_subnote_action = QAction(QIcon(os.path.join("icons", "new_subnote.svg")), "Новая вложенная заметка", self)
        self.new_subnote_action.setToolTip("Новая вложенная заметка (Alt+Insert)")
        self.new_subnote_action.triggered.connect(self.new_subnote)
        toolbar.addAction(self.new_subnote_action)
        
        # Удалить заметку
        self.delete_note_action = QAction(QIcon(os.path.join("icons", "delete_note.svg")), "Удалить заметку", self)
        self.delete_note_action.setToolTip("Удалить заметку (Delete)")
        self.delete_note_action.triggered.connect(self.delete_note)
        toolbar.addAction(self.delete_note_action)
        
        toolbar.addSeparator()
        
        # Найти
        self.find_action = QAction(QIcon(os.path.join("icons", "find.svg")), "Найти", self)
        self.find_action.setToolTip("Найти (Ctrl+F)")
        self.find_action.triggered.connect(self.show_search_dialog)
        toolbar.addAction(self.find_action)
        
        # Найти далее
        self.find_next_action = QAction(QIcon(os.path.join("icons", "find_next.svg")), "Найти далее", self)
        self.find_next_action.setToolTip("Найти далее (F3)")
        self.find_next_action.triggered.connect(self.handle_f3)
        toolbar.addAction(self.find_next_action)
        
        # Найти и заменить
        self.replace_action = QAction(QIcon(os.path.join("icons", "replace.svg")), "Найти и заменить", self)
        self.replace_action.setToolTip("Найти и заменить (Alt+F3)")
        self.replace_action.triggered.connect(self.show_replace_dialog)
        toolbar.addAction(self.replace_action)
        
        # Заменить все
        self.replace_all_action = QAction(QIcon(os.path.join("icons", "replace_all.svg")), "Заменить все", self)
        self.replace_all_action.setToolTip("Заменить все")
        self.replace_all_action.triggered.connect(self.show_replace_all_dialog)
        toolbar.addAction(self.replace_all_action)

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Создаем главный layout
        main_layout = QVBoxLayout(central_widget)
        
        # Создаем меню
        self.create_menu()
        
        # Создаем сплиттер для разделения дерева и редактора
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Создаем дерево заметок
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)  # Скрываем заголовок
        self.tree.setMinimumWidth(200)
        self.tree.itemClicked.connect(self.on_note_selected)
        self.tree.itemDoubleClicked.connect(self.on_note_double_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        splitter.addWidget(self.tree)
        
        # Создаем редактор
        editor_layout = QVBoxLayout()
        self.editor = QTextEdit()
        self.editor.textChanged.connect(self.on_content_changed)
        editor_layout.addWidget(self.editor)
        
        # Создаем контейнер для редактора
        editor_container = QWidget()
        editor_container.setLayout(editor_layout)
        splitter.addWidget(editor_container)
        
        # Устанавливаем соотношение размеров
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        # Создаем панель инструментов
        self.create_toolbar()

    def load_notes(self):
        """Загрузка заметок из базы данных"""
        self.tree.clear()
        
        # Получаем все заметки из БД
        notes = self.db.get_all_notes()
        
        # Создаем словарь для быстрого доступа к элементам дерева
        tree_items = {}
        
        # Сначала создаем все элементы дерева
        for note in notes:
            note_id, title, content, parent_id = note
            
            if parent_id == 1:  # Если это заметка верхнего уровня
                item = QTreeWidgetItem(self.tree, [title])
                item.setData(0, Qt.ItemDataRole.UserRole, note_id)
                tree_items[note_id] = item
        
        # Затем добавляем дочерние элементы
        for note in notes:
            note_id, title, content, parent_id = note
            
            if parent_id != 1:  # Если это вложенная заметка
                parent_item = tree_items.get(parent_id)
                if parent_item:
                    item = QTreeWidgetItem(parent_item, [title])
                    item.setData(0, Qt.ItemDataRole.UserRole, note_id)
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
        if self.current_note_id and self.content_modified:
            content = self.editor.toPlainText()
            try:
                note = self.db.get_note(self.current_note_id)
                if note:
                    self.db.update_note(self.current_note_id, note[1], content)
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
        self.save_current_note()
        
        note_id = item.data(0, Qt.ItemDataRole.UserRole)
        if note_id:
            note = self.db.get_note(note_id)
            if note:
                self.current_note_id = note_id
                self.current_parent_id = note[3]
                self.editor.setPlainText(note[2])
                self.content_modified = False
                
    def on_note_double_clicked(self, item):
        """Обработка двойного клика по заметке"""
        self.start_rename()

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
        
        menu.exec(self.tree.mapToGlobal(position))

    def on_content_changed(self):
        """Обработка изменения содержимого заметки"""
        if not self.editing_title:
            self.content_modified = True

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.save_current_note()
        event.accept()

    def start_rename(self):
        """Начало переименования заметки"""
        current_item = self.tree.currentItem()
        if not current_item:
            return
            
        self.editing_title = True
        current_item.setFlags(current_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.tree.editItem(current_item, 0)

    def show_about(self):
        """Показ информации о программе"""
        QMessageBox.about(self, "О программе",
                         "SkimNote - Менеджер заметок\n\n"
                         "Версия 1.0\n\n"
                         "Простой и удобный менеджер заметок с поддержкой "
                         "иерархической структуры.")

    def show_settings(self):
        """Показать окно настроек"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        # Настройки базы данных
        db_path = QLineEdit()
        db_path.setText(self.settings.value("db_path", "notes.db"))
        db_path.setReadOnly(True)
        db_browse = QPushButton("Обзор...")
        db_layout = QHBoxLayout()
        db_layout.addWidget(db_path)
        db_layout.addWidget(db_browse)
        layout.addRow("Файл базы данных:", db_layout)
        
        # Настройки шрифта
        font_size = QSpinBox()
        font_size.setRange(8, 72)
        font_size.setValue(self.settings.value("font_size", 12, type=int))
        layout.addRow("Размер шрифта:", font_size)
        
        # Настройки темы
        theme_combo = QComboBox()
        theme_combo.addItems(["Светлая", "Темная"])
        current_theme = self.settings.value("theme", "Светлая")
        theme_combo.setCurrentText(current_theme)
        layout.addRow("Тема:", theme_combo)
        
        # Кнопки
        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Отмена")
        
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow("", buttons)
        
        def browse_db():
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Выберите файл базы данных",
                "",
                "SQLite Database (*.db);;All Files (*.*)"
            )
            if file_name:
                db_path.setText(file_name)
        
        db_browse.clicked.connect(browse_db)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Сохраняем настройки
            self.settings.setValue("db_path", db_path.text())
            self.settings.setValue("font_size", font_size.value())
            self.settings.setValue("theme", theme_combo.currentText())
            
            # Применяем настройки
            self.apply_theme()
            self.apply_font()
            
            # Перезагружаем базу данных
            self.db = NotesDB(db_path.text())
            self.load_notes()
            
    def apply_font(self):
        """Применение шрифта"""
        # Здесь можно добавить применение шрифта к различным элементам интерфейса
        pass

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
        self.on_content_changed()
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
            self.on_content_changed()
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NotesApp()
    window.show()
    sys.exit(app.exec()) 