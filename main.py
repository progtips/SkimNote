import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTreeWidget, QTreeWidgetItem, QTextEdit,
                            QPushButton, QMenu, QMessageBox, QInputDialog, QToolBar,
                            QLabel, QSplitter, QDialog, QLineEdit, QFormLayout,
                            QCheckBox, QSpinBox, QComboBox, QFileDialog, QGroupBox,
                            QListWidget)
from PyQt6.QtCore import Qt, QSize, QSettings, QTimer
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFontDatabase, QFont, QGuiApplication
from PyQt6.QtGui import QTextCursor
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QUrl
import re
from database_manager import DatabaseManager
from config import Config
from settings_dialog import SettingsDialog
from toolbar_manager import ToolbarManager
import os
import configparser
import shutil
from datetime import datetime, timedelta
import socket
from translations import TRANSLATIONS
from backup_manager import BackupManager, init_backup_manager, register_exit_handler

# Определяем пути к файлам
if getattr(sys, 'frozen', False):
    # Если приложение запущено как exe (PyInstaller onefile)
    BASE_DIR = os.path.dirname(sys.executable)
    ICONS_DIR = os.path.join(sys._MEIPASS, 'icons')  # Иконки в временной папке PyInstaller
else:
    # Если приложение запущено из исходников
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ICONS_DIR = os.path.join(BASE_DIR, 'icons')

# Константы
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.ini')
DEFAULT_DB_PATH = os.path.join(BASE_DIR, 'notes.db')

# Инициализируем менеджер бэкапов и регистрируем обработчик завершения
init_backup_manager(BASE_DIR)
register_exit_handler()

class SearchDialog(QDialog):
    def __init__(self, parent=None, replace_mode=False, title=None):
        super().__init__(parent)
        
        # Получаем текущий язык из родительского окна
        current_language = parent.current_language if parent else 'Русский'
        
        if title:
            self.setWindowTitle(title)
        elif replace_mode:
            self.setWindowTitle(TRANSLATIONS[current_language]['search_replace'])
        else:
            self.setWindowTitle(TRANSLATIONS[current_language]['search_title'])
            
        self.setModal(True)
        
        layout = QFormLayout(self)
        
        # Поле поиска
        self.search_edit = QLineEdit()
        layout.addRow(TRANSLATIONS[current_language]['search_text'], self.search_edit)
        
        # Поле замены (только в режиме замены)
        if replace_mode:
            self.replace_edit = QLineEdit()
            layout.addRow(TRANSLATIONS[current_language]['search_replace_with'], self.replace_edit)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        self.find_button = QPushButton(TRANSLATIONS[current_language]['search_find'])
        self.find_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.find_button)
        
        if replace_mode:
            self.replace_button = QPushButton(TRANSLATIONS[current_language]['search_replace'])
            self.replace_button.clicked.connect(self.accept)
            buttons_layout.addWidget(self.replace_button)
        
        self.cancel_button = QPushButton(TRANSLATIONS[current_language]['settings_cancel'])
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addRow("", buttons_layout)
        
        # Устанавливаем фокус на поле поиска
        self.search_edit.setFocus()

class NotesApp(QMainWindow):
    SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.ini')

    class PlainTextPasteEdit(QTextEdit):
        """Редактор, который всегда вставляет простой текст."""
        def insertFromMimeData(self, source):
            # Если есть простой текст — вставляем его, игнорируя форматирование/HTML
            if source and source.hasText():
                self.insertPlainText(source.text())
                return
            # На всякий случай fallback к стандартному поведению
            super().insertFromMimeData(source)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Регулярка для URL (простая и быстрая)
            self._url_regex = re.compile(r"(https?://\S+|www\.[\w-]+\.[\w\.-]+\S*)", re.IGNORECASE)
            self.setMouseTracking(True)

        def _word_under_cursor(self, pos):
            cursor = self.cursorForPosition(pos)
            if cursor is None:
                return ""
            # Расширяем выделение до границ URL-подобного слова
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            text = cursor.selectedText()
            # Иногда WordUnderCursor обрезает URL по символам, попробуем расширить вручную
            if text and not self._is_url(text):
                # Попробуем захватить символы слева/справа, подходящие для URL
                text = self._expand_to_url(cursor)
            return text

        def _expand_to_url(self, cursor):
            # Расширяемся по символам URL (буквы, цифры, .:/?#@!$&'()*+,;=%- _)
            doc = self.document()
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            pos_left = start
            pos_right = end
            def char_at(i):
                c = doc.characterAt(i)
                return "" if c == "\uFFFF" else str(c)
            def is_url_char(c):
                return bool(re.match(r"[\w\-\.:/#?@!$&'()*+,;=%]", c))
            # расширяем влево
            i = start - 1
            while i >= 0 and is_url_char(char_at(i)):
                pos_left = i
                i -= 1
            # расширяем вправо
            j = end
            while is_url_char(char_at(j)):
                pos_right = j + 1
                j += 1
            c2 = QTextCursor(doc)
            c2.setPosition(pos_left)
            c2.setPosition(pos_right, QTextCursor.MoveMode.KeepAnchor)
            return c2.selectedText()

        def _is_url(self, text):
            return bool(self._url_regex.fullmatch(text)) or bool(self._url_regex.search(text))

        def _normalize_url(self, text):
            t = text.strip()
            # Снимаем возможные завершающие знаки пунктуации
            t = t.rstrip(').,;:!?>\']"')
            if t.lower().startswith('http://') or t.lower().startswith('https://'):
                return t
            if t.lower().startswith('www.'):
                return 'https://' + t
            return t

        def mouseReleaseEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                text = self._word_under_cursor(event.position().toPoint())
                if text and self._is_url(text):
                    url = QUrl(self._normalize_url(text))
                    if url.isValid():
                        QDesktopServices.openUrl(url)
                        return
            super().mouseReleaseEvent(event)

        def mouseMoveEvent(self, event):
            # Показываем курсор-ссылку при hover над URL (без Ctrl)
            text = self._word_under_cursor(event.position().toPoint())
            if text and self._is_url(text):
                self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.viewport().unsetCursor()
            super().mouseMoveEvent(event)

        def contextMenuEvent(self, event):
            menu = self.createStandardContextMenu()
            text = self._word_under_cursor(event.pos())
            if text and self._is_url(text):
                open_action_text = 'Открыть ссылку'  # локализацию можно добавить при необходимости
                action = menu.addAction(open_action_text)
                def _open():
                    url = QUrl(self._normalize_url(text))
                    if url.isValid():
                        QDesktopServices.openUrl(url)
                action.triggered.connect(_open)
            menu.exec(event.globalPos())

    class UrlHighlighter(QSyntaxHighlighter):
        """Подсветка URL: синий цвет и подчёркивание, как в браузере."""
        def __init__(self, parent):
            super().__init__(parent)
            self._url_regex = re.compile(r"(https?://\S+|www\.[\w-]+\.[\w\.-]+\S*)", re.IGNORECASE)
            self._format = QTextCharFormat()
            self._format.setForeground(QColor(0, 102, 204))
            self._format.setFontUnderline(True)

        def highlightBlock(self, text):
            for match in self._url_regex.finditer(text):
                start, end = match.start(), match.end()
                self.setFormat(start, end - start, self._format)

    def __init__(self):
        super().__init__()
        
        # Инициализация основных переменных
        self.init_ui()
        
        # Загружаем текущий язык интерфейса
        config = Config()
        if os.path.exists(self.SETTINGS_FILE):
            try:
                # Загружаем настройки из файла
                config_parser = configparser.ConfigParser()
                config_parser.read(self.SETTINGS_FILE, encoding='utf-8')
                
                # Загружаем язык интерфейса
                if config_parser.has_section('Interface'):
                    self.current_language = config_parser.get('Interface', 'language', fallback='Русский')
                else:
                    self.current_language = config.get('language', 'Русский')
                
                # Загружаем размеры и позицию окна
                x = config_parser.getint('Window', 'x', fallback=100)
                y = config_parser.getint('Window', 'y', fallback=100)
                width = config_parser.getint('Window', 'width', fallback=800)
                height = config_parser.getint('Window', 'height', fallback=600)
                
                # Устанавливаем позицию и размер окна
                self.move(x, y)
                self.resize(width, height)
                
                # Загружаем остальные настройки
                self.font_size = config_parser.getint('Font', 'size', fallback=12)
                self.font_family = config_parser.get('Font', 'family', fallback='Segoe UI')
                db_path = config_parser.get('Database', 'path', fallback=DEFAULT_DB_PATH)
                
                # Сохраняем путь к базе данных для последующей инициализации
                self.db_path = db_path
            except Exception as e:
                print(f"DEBUG: Ошибка при загрузке настроек: {str(e)}")
                self.set_default_settings()
        else:
            self.current_language = config.get('language', 'Русский')
            self.set_default_settings()
        
        # Загружаем состояние дерева (раскрытые узлы)
        try:
            config_parser = configparser.ConfigParser()
            if os.path.exists(self.SETTINGS_FILE):
                config_parser.read(self.SETTINGS_FILE, encoding='utf-8')
                if config_parser.has_section('Tree'):
                    raw = config_parser.get('Tree', 'expanded_ids', fallback='')
                    ids = [s for s in raw.split(',') if s.strip()]
                    self.expanded_note_ids = set(int(s) for s in ids)
        except Exception:
            self.expanded_note_ids = set()

        # Настройка интерфейса
        self.create_actions()
        self.setup_ui()
        
        # Инициализируем базу данных после создания интерфейса
        if not hasattr(self, 'db_manager') or self.db_manager is None:
            db_path = getattr(self, 'db_path', DEFAULT_DB_PATH)
            self.init_db(db_path)
        
        # Загружаем заметки
        self.load_notes()
        
        # Устанавливаем заголовок окна
        self.setWindowTitle(TRANSLATIONS[self.current_language]['window_title'])
        self.setWindowIcon(QIcon(os.path.join(ICONS_DIR, 'app.ico')))
        
        # Применяем тему
        self.apply_theme()
        
        # Показываем окно
        self.show()
        
        # После показа окна гарантируем видимость в рабочих пределах экрана
        QTimer.singleShot(0, self.ensure_window_visible)

        # Принудительно показываем панель инструментов после отображения окна
        QTimer.singleShot(100, self.show_toolbar)

    def init_ui(self):
        """Инициализация основных переменных и настроек интерфейса"""
        # Инициализация основных переменных
        self.default_width = 800
        self.default_height = 600
        self.font_size = 12
        self.font_family = "Segoe UI"
        self.db_manager = None  # Инициализация будет в load_settings
        self.current_language = "Русский"  # Значение по умолчанию

        # Инициализация переменных состояния
        self.current_note_id = None
        self.current_parent_id = 1
        self.content_modified = False
        self.editing_title = False
        self.last_search_text = ""
        self.last_replace_text = ""
        self.restored_geometry = False
        self.programmatic_load = False  # Флаг для предотвращения срабатывания textChanged
        
        # Инициализация менеджера панели инструментов
        self.toolbar_manager = None
        # Состояние развёрнутости дерева заметок (множество note_id)
        self.expanded_note_ids = set()

    def init_db(self, db_path='notes.db'):
        """Инициализация базы данных"""
        # Убеждаемся, что current_language инициализирован
        if not hasattr(self, 'current_language') or self.current_language is None:
            self.current_language = "Русский"
            
        self.db_manager = DatabaseManager(BASE_DIR, self.current_language)
        self.db_manager.init_database(db_path)
        self.db = self.db_manager.db  # Для обратной совместимости

    def load_settings(self):
        """Загрузка настроек из файла"""
        import configparser
        config = configparser.ConfigParser()
        
        if os.path.exists(self.SETTINGS_FILE):
            config.read(self.SETTINGS_FILE, encoding='utf-8')
            self.font_size = int(config.get('main', 'font_size', fallback='12'))
            self.font_family = config.get('main', 'font_family', fallback='Segoe UI')
            db_path = config.get('main', 'db_path', fallback=DEFAULT_DB_PATH)
            
            # Инициализируем базу данных с путем из настроек
            if self.db_manager is None or self.db_manager.db_path != db_path:
                self.init_db(db_path)
        else:
            # Используем значения по умолчанию
            self.font_size = 12
            self.font_family = "Segoe UI"
            self.init_db(DEFAULT_DB_PATH)

    def create_actions(self):
        """Создание действий меню и панели инструментов"""
        # Файл
        self.new_action = QAction(QIcon(os.path.join(ICONS_DIR, 'new_note.svg')), 
            TRANSLATIONS[self.current_language]['action_new'], self)
        self.new_action.setShortcut('Ctrl+N')
        self.new_action.triggered.connect(self.new_note)
        
        self.new_subnote_action = QAction(QIcon(os.path.join(ICONS_DIR, 'new_subnote.svg')), 
            TRANSLATIONS[self.current_language]['action_new_subnote'], self)
        self.new_subnote_action.setShortcut('Ctrl+Shift+N')
        self.new_subnote_action.triggered.connect(self.new_subnote)
        
        self.delete_action = QAction(QIcon(os.path.join(ICONS_DIR, 'delete.svg')), 
            TRANSLATIONS[self.current_language]['action_delete'], self)
        self.delete_action.setShortcut('Delete')
        self.delete_action.triggered.connect(self.delete_note)
        
        self.rename_action = QAction(TRANSLATIONS[self.current_language]['action_rename'], self)
        self.rename_action.setShortcut('F2')
        self.rename_action.triggered.connect(self.start_rename)
        
        self.settings_action = QAction(TRANSLATIONS[self.current_language]['action_settings'], self)
        self.settings_action.triggered.connect(self.show_settings)
        
        self.about_action = QAction(TRANSLATIONS[self.current_language]['action_about'], self)
        self.about_action.triggered.connect(self.show_about)
        
        self.exit_action = QAction(TRANSLATIONS[self.current_language]['action_exit'], self)
        self.exit_action.setShortcut('Alt+F4')
        self.exit_action.triggered.connect(self.close)
        
        # Правка
        self.cut_action = QAction(TRANSLATIONS[self.current_language]['action_cut'], self)
        self.cut_action.setShortcut('Ctrl+X')
        self.cut_action.triggered.connect(lambda: self.editor.cut())
        
        self.copy_action = QAction(TRANSLATIONS[self.current_language]['action_copy'], self)
        self.copy_action.setShortcut('Ctrl+C')
        self.copy_action.triggered.connect(lambda: self.editor.copy())
        
        self.paste_action = QAction(TRANSLATIONS[self.current_language]['action_paste'], self)
        self.paste_action.setShortcut('Ctrl+V')
        self.paste_action.triggered.connect(lambda: self.editor.paste())
        
        self.find_action = QAction(TRANSLATIONS[self.current_language]['action_find'], self)
        self.find_action.setShortcut('Ctrl+F')
        self.find_action.triggered.connect(self.show_search_dialog)
        
        self.replace_action = QAction(TRANSLATIONS[self.current_language]['action_replace'], self)
        self.replace_action.setShortcut('Ctrl+H')
        self.replace_action.triggered.connect(self.show_replace_dialog)
        
        self.replace_all_action = QAction(TRANSLATIONS[self.current_language]['action_replace_all'], self)
        self.replace_all_action.setShortcut('Ctrl+Shift+H')
        self.replace_all_action.triggered.connect(self.show_replace_all_dialog)

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
        file_menu = menubar.addMenu(TRANSLATIONS[self.current_language]['menu_file'])
        
        # --- Новый пункт ---
        change_db_action = QAction(TRANSLATIONS[self.current_language]['action_change_db'], self)
        change_db_action.triggered.connect(self.change_db)
        file_menu.addAction(change_db_action)
        # --- Конец нового пункта ---
        
        # --- Новый пункт для восстановления базы данных ---
        restore_db_action = QAction(TRANSLATIONS[self.current_language]['action_restore_db'], self)
        restore_db_action.triggered.connect(self.restore_db)
        file_menu.addAction(restore_db_action)
        # --- Конец нового пункта ---
        
        file_menu.addSeparator()
        
        exit_action = QAction(TRANSLATIONS[self.current_language]['action_exit'], self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Заметки"
        notes_menu = menubar.addMenu(TRANSLATIONS[self.current_language]['menu_notes'])
        
        # Переносим сюда пункты создания заметок
        new_note_action = QAction(TRANSLATIONS[self.current_language]['action_new'], self)
        new_note_action.setShortcut("Insert")
        new_note_action.triggered.connect(self.new_note)
        notes_menu.addAction(new_note_action)
        
        new_subnote_action = QAction(TRANSLATIONS[self.current_language]['action_new_subnote'], self)
        new_subnote_action.setShortcut("Alt+Insert")
        new_subnote_action.triggered.connect(self.new_subnote)
        notes_menu.addAction(new_subnote_action)
        
        notes_menu.addSeparator()

        # --- Новый пункт: Переместить вверх ---
        move_up_action = QAction(TRANSLATIONS[self.current_language]['action_move_up'], self)
        move_up_action.setShortcut("Ctrl+Up")
        move_up_action.triggered.connect(self.move_note_up)
        notes_menu.addAction(move_up_action)

        # --- Новый пункт: Переместить вниз ---
        move_down_action = QAction(TRANSLATIONS[self.current_language]['action_move_down'], self)
        move_down_action.setShortcut("Ctrl+Down")
        move_down_action.triggered.connect(self.move_note_down)
        notes_menu.addAction(move_down_action)

        notes_menu.addSeparator()

        find_action = QAction(TRANSLATIONS[self.current_language]['action_find'], self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.show_search_dialog)
        notes_menu.addAction(find_action)
        
        find_next_action = QAction(TRANSLATIONS[self.current_language]['action_find_next'], self)
        find_next_action.setShortcut("F3")
        find_next_action.triggered.connect(self.handle_f3)
        notes_menu.addAction(find_next_action)
        
        replace_action = QAction(TRANSLATIONS[self.current_language]['action_replace'], self)
        replace_action.setShortcut("Alt+F3")
        replace_action.triggered.connect(self.show_replace_dialog)
        notes_menu.addAction(replace_action)
        
        replace_all_action = QAction(TRANSLATIONS[self.current_language]['action_replace_all'], self)
        replace_all_action.triggered.connect(self.show_replace_all_dialog)
        notes_menu.addAction(replace_all_action)
        
        notes_menu.addSeparator()
        
        delete_action = QAction(TRANSLATIONS[self.current_language]['action_delete'], self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_note)
        notes_menu.addAction(delete_action)
        
        # Меню "Настройки"
        settings_menu = menubar.addMenu(TRANSLATIONS[self.current_language]['menu_settings'])
        
        settings_action = QAction(TRANSLATIONS[self.current_language]['action_settings'], self)
        settings_action.triggered.connect(self.show_settings)
        settings_menu.addAction(settings_action)
        
        # Меню "Справка"
        help_menu = menubar.addMenu(TRANSLATIONS[self.current_language]['menu_help'])
        about_action = QAction(TRANSLATIONS[self.current_language]['action_about'], self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """Создание панели инструментов через менеджер"""
        # Создаем менеджер панели инструментов
        self.toolbar_manager = ToolbarManager(self, ICONS_DIR, self.current_language)
        
        # Создаем панель инструментов
        self.toolbar = self.toolbar_manager.create_toolbar()
        
        # Подключаем обработчики к действиям
        handlers = {
            'new_note': self.new_note,
            'new_subnote': self.new_subnote,
            'delete': self.delete_note,
            'cut': lambda: self.editor.cut(),
            'copy': lambda: self.editor.copy(),
            'paste': lambda: self.editor.paste(),
            'find': self.show_search_dialog,
            'replace': self.show_replace_dialog,
            'replace_all': self.show_replace_all_dialog
        }
        
        self.toolbar_manager.connect_actions(handlers)

    def show_toolbar(self):
        """Принудительное отображение панели инструментов"""
        if hasattr(self, 'toolbar') and self.toolbar:
            self.toolbar.setVisible(True)

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
        self.tree.currentItemChanged.connect(self.on_current_item_changed)
        self.tree.itemChanged.connect(self.on_item_changed)
        # Отслеживаем разворачивание/сворачивание веток
        self.tree.itemExpanded.connect(self.on_item_expanded)
        self.tree.itemCollapsed.connect(self.on_item_collapsed)
        left_layout.addWidget(self.tree)
        
        # Добавляем левую панель в главный layout
        layout.addWidget(left_panel, 1)
        
        # Создаем правую панель с редактором
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Создаем редактор (вставка только простого текста)
        self.editor = self.PlainTextPasteEdit()
        # Включаем подсветку URL
        self.url_highlighter = self.UrlHighlighter(self.editor.document())
        self.editor.textChanged.connect(self.on_text_changed)
        right_layout.addWidget(self.editor)
        
        # Добавляем правую панель в главный layout
        layout.addWidget(right_panel, 2)
        
        # Создаем меню
        self.create_menu()
        
        # Создаем панель инструментов через менеджер
        self.create_toolbar()

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
        
        # Применяем сохранённое состояние раскрытия
        def apply_expand_state(item):
            note_id = item.data(0, Qt.ItemDataRole.UserRole)
            if note_id in self.expanded_note_ids:
                self.tree.expandItem(item)
            for idx in range(item.childCount()):
                apply_expand_state(item.child(idx))

        # По умолчанию сворачиваем всё
        self.tree.collapseAll()
        # Применяем состояние для каждого верхнего уровня
        for i in range(self.tree.topLevelItemCount()):
            apply_expand_state(self.tree.topLevelItem(i))
        
        # Выбираем первую заметку, если она есть
        if self.tree.topLevelItemCount() > 0:
            first_item = self.tree.topLevelItem(0)
            self.programmatic_load = True  # Устанавливаем флаг перед программным выбором
            self.tree.setCurrentItem(first_item)
            self.programmatic_load = False  # Сбрасываем флаг после программного выбора
            self.on_note_selected(first_item)

    def select_note_by_id(self, note_id):
        """Выбор заметки по ID (ищет во всём дереве, включая вложенные)."""
        def find_in_subtree(root_item):
            if root_item.data(0, Qt.ItemDataRole.UserRole) == note_id:
                return root_item
            for idx in range(root_item.childCount()):
                found = find_in_subtree(root_item.child(idx))
                if found is not None:
                    return found
            return None

        found_item = None
        for i in range(self.tree.topLevelItemCount()):
            top_item = self.tree.topLevelItem(i)
            found_item = find_in_subtree(top_item)
            if found_item is not None:
                break

        if found_item is not None:
            self.programmatic_load = True
            self.tree.setCurrentItem(found_item)
            self.tree.scrollToItem(found_item)
            self.programmatic_load = False
            # Явно загружаем содержимое выбранной заметки
            self.on_note_selected(found_item)

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
            print(f"DEBUG: Ошибка при создании заметки: {str(e)}")

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
            print(f"DEBUG: Ошибка при создании вложенной заметки: {str(e)}")

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
            QMessageBox.critical(self, TRANSLATIONS[self.current_language]['error_title'], 
                               TRANSLATIONS[self.current_language]['error_save_note'] + f": {str(e)}")

    def delete_note(self):
        """Удаление заметки"""
        current_item = self.tree.currentItem()
        if not current_item:
            return
            
        note_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        # Не позволяем удалить корневую заметку
        if note_id == 1:
            QMessageBox.warning(self, TRANSLATIONS[self.current_language]['warning_title'],
                              TRANSLATIONS[self.current_language]['cannot_delete_root'])
            return
        
        # Определяем, кого выделить после удаления: предыдущего соседа, иначе родителя
        target_note_id = None
        parent_item = current_item.parent()
        if parent_item:
            idx = parent_item.indexOfChild(current_item)
            if idx > 0:
                prev_sibling = parent_item.child(idx - 1)
                target_note_id = prev_sibling.data(0, Qt.ItemDataRole.UserRole)
            else:
                target_note_id = parent_item.data(0, Qt.ItemDataRole.UserRole)
        else:
            # Верхний уровень
            idx = self.tree.indexOfTopLevelItem(current_item)
            if idx > 0:
                prev_top = self.tree.topLevelItem(idx - 1)
                target_note_id = prev_top.data(0, Qt.ItemDataRole.UserRole)
            else:
                # Нет предыдущего сверху — попробуем выбрать следующий после удаления
                if self.tree.topLevelItemCount() > 1:
                    next_top = self.tree.topLevelItem(idx + 1)
                    target_note_id = next_top.data(0, Qt.ItemDataRole.UserRole)
                else:
                    target_note_id = None

        # Готовим текст подтверждения с учётом наличия подзаметок
        has_children = current_item.childCount() > 0
        confirm_text = TRANSLATIONS[self.current_language]['confirm_delete']
        if has_children:
            confirm_text = (confirm_text + "\n\n" +
                TRANSLATIONS[self.current_language]['confirm_delete_with_children'])

        reply = QMessageBox.question(self, TRANSLATIONS[self.current_language]['confirm_title'],
                                   confirm_text,
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_note(note_id)
                self.load_notes()
                # Выполняем выбор рассчитанной заметки, если есть
                if target_note_id:
                    self.select_note_by_id(target_note_id)
            except Exception as e:
                print(f"DEBUG: Ошибка при удалении заметки: {str(e)}")

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
        self.programmatic_load = True  # Устанавливаем флаг перед загрузкой
        self.editor.setPlainText(note[2])  # content
        self.programmatic_load = False  # Сбрасываем флаг после загрузки
        
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
        if self.programmatic_load:
            return
            
        self.content_modified = True

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        # Сохраняем текущую заметку
        self.save_current_note()
        
        # Сохраняем настройки
        self.save_window_settings()
        
        # Закрываем соединение с базой данных
        if hasattr(self, 'db_manager') and self.db_manager:
            self.db_manager.close_database()
        
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
        # Используем переводы в зависимости от текущего языка
        about_text = TRANSLATIONS[self.current_language]['about_text']
        
        msg = QMessageBox(self)
        msg.setWindowTitle(TRANSLATIONS[self.current_language]['about_title'])
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
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_settings = dialog.get_settings()
            
            # Применяем и сохраняем новые настройки
            self.font_size = new_settings['font_size']
            self.apply_theme()
            
            # Проверяем, изменился ли путь к БД
            new_db_path = new_settings['db_path']
            if new_db_path != self.db.db_path:
                # Закрываем старую БД
                self.db_manager.close_database()
                # Инициализируем новую
                self.db_manager.init_database(new_db_path)
                self.db = self.db_manager.db
                # Перезагружаем заметки
                self.load_notes()

            # Проверяем, изменился ли язык
            new_language = new_settings['language']
            language_changed = new_language != self.current_language
            self.current_language = new_language
            
            # Сохраняем все настройки в файл
            self.save_window_settings()

            if language_changed:
                self.reload_interface()

    def reload_interface(self):
        """Перезагрузка интерфейса при смене языка"""
        try:
            # Сохраняем текущие размеры и позицию окна
            geometry = self.geometry()
            
            # Сохраняем текущее состояние
            current_note_id = self.current_note_id
            current_content = self.editor.toPlainText() if hasattr(self, 'editor') else ""
            
            # Сохраняем текущую заметку перед перезагрузкой
            if self.current_note_id and self.content_modified:
                self.save_current_note()
            
            # Очищаем только дерево заметок, но не редактор
            self.tree.clear()
            
            # Удаляем старую панель инструментов через менеджер
            if hasattr(self, 'toolbar_manager') and self.toolbar_manager:
                self.toolbar_manager.remove_toolbar()
            
            # Пересоздаем действия с новым языком
            self.create_actions()
            
            # Пересоздаем меню и панель инструментов
            self.menuBar().clear()
            self.create_menu()
            self.create_toolbar()
            
            # Обновляем язык в менеджере панели инструментов
            if hasattr(self, 'toolbar_manager') and self.toolbar_manager:
                self.toolbar_manager.update_language(self.current_language)
            
            # Обновляем язык в менеджере базы данных
            if hasattr(self, 'db_manager') and self.db_manager:
                self.db_manager.current_language = self.current_language
            
            # Обновляем заголовок окна
            self.setWindowTitle(TRANSLATIONS[self.current_language]['window_title'])
            
            # Применяем тему
            self.apply_theme()
            
            # Загружаем заметки заново
            self.load_notes()
            
            # Восстанавливаем выбранную заметку
            if current_note_id:
                self.select_note_by_id(current_note_id)
                # Восстанавливаем содержимое редактора, если оно было изменено
                if current_content and not self.content_modified:
                    self.programmatic_load = True  # Устанавливаем флаг перед восстановлением
                    self.editor.setPlainText(current_content)
                    self.programmatic_load = False  # Сбрасываем флаг после восстановления
            
        except Exception as e:
            QMessageBox.critical(self, TRANSLATIONS[self.current_language]['error_title'], f"Не удалось перезагрузить интерфейс: {str(e)}")

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
        
        # Получаем все заметки из базы данных
        notes = self.db.get_all_notes()
        
        for note in notes:
            note_id, title, content, parent_id, order_index = note
            if note_id == 1:  # Пропускаем корневую заметку
                continue
            if content is None:
                content = ""
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
                QMessageBox.information(self, TRANSLATIONS[self.current_language]['search_title'],
                                      TRANSLATIONS[self.current_language]['no_search_results'])
                return
        if not self.search_results:
            QMessageBox.information(self, TRANSLATIONS[self.current_language]['search_title'],
                                  TRANSLATIONS[self.current_language]['text_not_found'])
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
            QMessageBox.information(self, TRANSLATIONS[self.current_language]['replace_title'],
                                  TRANSLATIONS[self.current_language]['text_not_found'])
            return
        note_id, start, end = self.search_results[0]
        self.select_note_by_id(note_id)
        # заменяем текст
        content = self.editor.toPlainText()
        new_content = content[:start] + replace_text + content[end:]
        self.programmatic_load = True  # Устанавливаем флаг перед заменой
        self.editor.setPlainText(new_content)
        self.programmatic_load = False  # Сбрасываем флаг после замены
        self.on_text_changed()  # Явно вызываем обработчик
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
            QMessageBox.information(self, TRANSLATIONS[self.current_language]['replace_title'],
                                  TRANSLATIONS[self.current_language]['text_not_found'])
            return
        # Сортируем результаты по note_id и индексу, чтобы заменять с конца
        self.search_results.sort(key=lambda x: (x[0], -x[1]), reverse=True)
        for note_id, start, end in self.search_results:
            self.select_note_by_id(note_id)
            content = self.editor.toPlainText()
            new_content = content[:start] + replace_text + content[end:]
            self.programmatic_load = True  # Устанавливаем флаг перед заменой
            self.editor.setPlainText(new_content)
            self.programmatic_load = False  # Сбрасываем флаг после замены
            self.on_text_changed()  # Явно вызываем обработчик
        QMessageBox.information(self, TRANSLATIONS[self.current_language]['replace_title'],
                              TRANSLATIONS[self.current_language]['replace_count'] + str(len(self.search_results)))

    def show_replace_all_dialog(self):
        """Показать диалог замены всех вхождений"""
        dialog = SearchDialog(self, replace_mode=True, title=TRANSLATIONS[self.current_language]['action_replace_all'])
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

    def ensure_window_visible(self):
        """Делает окно видимым в границах рабочего стола, учитывая рамки и активный экран."""
        try:
            screen_obj = self.screen() or QApplication.primaryScreen()
            if not screen_obj:
                self.center_on_screen()
                return
            screen_geom = screen_obj.availableGeometry()
            win_frame = self.frameGeometry()

            # Если окно вообще вне экрана — центрируем
            if not screen_geom.intersects(win_frame):
                self.center_on_screen()
                return

            # Подрезаем позицию так, чтобы окно точно помещалось в рабочую область
            new_x = win_frame.left()
            new_y = win_frame.top()
            if win_frame.right() > screen_geom.right():
                new_x = max(screen_geom.left(), screen_geom.right() - win_frame.width())
            if win_frame.left() < screen_geom.left():
                new_x = screen_geom.left()
            if win_frame.bottom() > screen_geom.bottom():
                new_y = max(screen_geom.top(), screen_geom.bottom() - win_frame.height())
            if win_frame.top() < screen_geom.top():
                new_y = screen_geom.top()
            if (new_x, new_y) != (win_frame.left(), win_frame.top()):
                self.move(new_x, new_y)
        except Exception:
            self.center_on_screen()

    def change_db(self):
        new_db_path = self.db_manager.change_database(self)
        if new_db_path:
            self.save_current_note()
            self.db_manager.close_database()
            self.db_manager.init_database(new_db_path)
            self.db = self.db_manager.db
            self.save_window_settings()
            self.load_notes()

    def save_settings_dialog_db_path(self, db_path):
        # Сохраняем только путь к базе данных, остальные настройки не трогаем
        config = configparser.ConfigParser()
        config.read(self.SETTINGS_FILE, encoding='utf-8')
        if 'main' not in config:
            config['main'] = {}
        config['main']['db_path'] = db_path
        with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
            config.write(f)
        self.db_manager.close_database()
        self.db_manager.init_database(db_path)
        self.db = self.db_manager.db
        self.load_notes()

    def backup_db(self):
        """Регулярный бэкап базы данных"""
        backup_manager = BackupManager(BASE_DIR)
        backup_manager.create_backup(self.db.db_path)

    def restore_db(self):
        """Восстановление базы данных из бэкапа"""
        backup_manager = BackupManager(BASE_DIR)
        
        if self.db_manager.restore_database(self, backup_manager):
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
            print(f"DEBUG: Ошибка при сохранении заголовка: {str(e)}")

    def on_item_expanded(self, item):
        """Сохраняем ID узла как раскрытый"""
        note_id = item.data(0, Qt.ItemDataRole.UserRole)
        if note_id:
            self.expanded_note_ids.add(int(note_id))
            self.save_window_settings()

    def on_item_collapsed(self, item):
        """Удаляем ID узла из раскрытых"""
        note_id = item.data(0, Qt.ItemDataRole.UserRole)
        if note_id and int(note_id) in self.expanded_note_ids:
            self.expanded_note_ids.remove(int(note_id))
            self.save_window_settings()

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
        try:
            # Создаем директорию для настроек, если она не существует
            os.makedirs(os.path.dirname(self.SETTINGS_FILE), exist_ok=True)
            
            # Сохраняем настройки
            config = configparser.ConfigParser()
            config.read(self.SETTINGS_FILE, encoding='utf-8')
            
            if not config.has_section('Window'):
                config.add_section('Window')
            
            # Сохраняем размеры и позицию окна, не допуская отрицательных значений
            config['Window']['x'] = str(max(0, self.x()))
            config['Window']['y'] = str(max(0, self.y()))
            config['Window']['width'] = str(self.width())
            config['Window']['height'] = str(self.height())
            
            # Сохраняем язык интерфейса
            if not config.has_section('Interface'):
                config.add_section('Interface')
            config['Interface']['language'] = self.current_language
            
            # Сохраняем путь к базе данных
            if not config.has_section('Database'):
                config.add_section('Database')
            if hasattr(self, 'db') and self.db:
                config['Database']['path'] = self.db.db_path
            
            # Сохраняем состояние раскрытых узлов
            if not config.has_section('Tree'):
                config.add_section('Tree')
            config['Tree']['expanded_ids'] = ','.join(str(i) for i in sorted(self.expanded_note_ids))

            # Сохраняем настройки шрифта
            if not config.has_section('Font'):
                config.add_section('Font')
            config['Font']['size'] = str(self.font_size)
            config['Font']['family'] = self.font_family
            
            # Сохраняем настройки в файл
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                config.write(f)
                
        except Exception as e:
            QMessageBox.critical(self, TRANSLATIONS[self.current_language]['error_title'], 
                               TRANSLATIONS[self.current_language]['error_save_settings'] + f"\n{str(e)}")

    def set_default_settings(self):
        """Установка настроек по умолчанию"""
        # Устанавливаем значения по умолчанию
        self.setGeometry(100, 100, 800, 600)
        self.center_on_screen()
        self.font_size = 12
        self.font_family = 'Segoe UI'
        
        # Создаем файл настроек со значениями по умолчанию
        self.save_window_settings()

    def on_current_item_changed(self, current, previous):
        """Обработка изменения текущего элемента дерева"""
        # Этот обработчик нужен для корректной работы с клавиатурой
        # но мы не хотим, чтобы он вызывал сохранение при программном изменении
        if current and not self.programmatic_load:
            # Только если это не программное изменение
            self.on_note_selected(current)

def main():
    app = QApplication(sys.argv)
    
    # Проверяем, не запущено ли уже приложение
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', 12345))
    except socket.error:
        QMessageBox.critical(None, TRANSLATIONS['Русский']['error_title'], 
                           TRANSLATIONS['Русский']['app_already_running'])
        sys.exit(1)
    
    window = NotesApp()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 