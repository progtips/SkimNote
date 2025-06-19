from PyQt6.QtWidgets import QToolBar
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon, QAction
import os
from translations import TRANSLATIONS

class ToolbarManager:
    """Менеджер панели инструментов"""
    
    def __init__(self, parent, icons_dir, current_language='Русский'):
        self.parent = parent
        self.icons_dir = icons_dir
        self.current_language = current_language
        self.toolbar = None
        self.actions = {}
        
    def create_toolbar(self):
        """Создание панели инструментов"""
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(24, 24))  # Устанавливаем размер иконок 24x24
        self.parent.addToolBar(self.toolbar)
        
        # Создаем действия
        self.create_actions()
        
        # Добавляем действия на панель
        self.add_actions_to_toolbar()
        
        return self.toolbar
    
    def create_actions(self):
        """Создание действий для панели инструментов"""
        # Новый заметка
        self.actions['new'] = QAction(
            QIcon(os.path.join(self.icons_dir, 'new_note.svg')), 
            TRANSLATIONS[self.current_language]['action_new'], 
            self.parent
        )
        self.actions['new'].setShortcut('Ctrl+N')
        
        # Новая подзаметка
        self.actions['new_subnote'] = QAction(
            QIcon(os.path.join(self.icons_dir, 'new_subnote.svg')), 
            TRANSLATIONS[self.current_language]['action_new_subnote'], 
            self.parent
        )
        self.actions['new_subnote'].setShortcut('Ctrl+Shift+N')
        
        # Удалить
        self.actions['delete'] = QAction(
            QIcon(os.path.join(self.icons_dir, 'delete.svg')), 
            TRANSLATIONS[self.current_language]['action_delete'], 
            self.parent
        )
        self.actions['delete'].setShortcut('Delete')
        
        # Вырезать
        self.actions['cut'] = QAction(
            TRANSLATIONS[self.current_language]['action_cut'], 
            self.parent
        )
        self.actions['cut'].setShortcut('Ctrl+X')
        
        # Копировать
        self.actions['copy'] = QAction(
            TRANSLATIONS[self.current_language]['action_copy'], 
            self.parent
        )
        self.actions['copy'].setShortcut('Ctrl+C')
        
        # Вставить
        self.actions['paste'] = QAction(
            TRANSLATIONS[self.current_language]['action_paste'], 
            self.parent
        )
        self.actions['paste'].setShortcut('Ctrl+V')
        
        # Найти
        self.actions['find'] = QAction(
            TRANSLATIONS[self.current_language]['action_find'], 
            self.parent
        )
        self.actions['find'].setShortcut('Ctrl+F')
        
        # Заменить
        self.actions['replace'] = QAction(
            TRANSLATIONS[self.current_language]['action_replace'], 
            self.parent
        )
        self.actions['replace'].setShortcut('Ctrl+H')
        
        # Заменить все
        self.actions['replace_all'] = QAction(
            TRANSLATIONS[self.current_language]['action_replace_all'], 
            self.parent
        )
        self.actions['replace_all'].setShortcut('Ctrl+Shift+H')
    
    def add_actions_to_toolbar(self):
        """Добавление действий на панель инструментов"""
        # Добавляем только основные действия
        self.toolbar.addAction(self.actions['new'])
        self.toolbar.addAction(self.actions['new_subnote'])
        self.toolbar.addAction(self.actions['delete'])
        
        # Закомментированные действия для возможного использования в будущем
        # self.toolbar.addSeparator()
        # self.toolbar.addAction(self.actions['cut'])
        # self.toolbar.addAction(self.actions['copy'])
        # self.toolbar.addAction(self.actions['paste'])
        # self.toolbar.addSeparator()
        # self.toolbar.addAction(self.actions['find'])
        # self.toolbar.addAction(self.actions['replace'])
        # self.toolbar.addAction(self.actions['replace_all'])
    
    def connect_actions(self, handlers):
        """Подключение обработчиков к действиям"""
        if 'new_note' in handlers:
            self.actions['new'].triggered.connect(handlers['new_note'])
        if 'new_subnote' in handlers:
            self.actions['new_subnote'].triggered.connect(handlers['new_subnote'])
        if 'delete' in handlers:
            self.actions['delete'].triggered.connect(handlers['delete'])
        if 'cut' in handlers:
            self.actions['cut'].triggered.connect(handlers['cut'])
        if 'copy' in handlers:
            self.actions['copy'].triggered.connect(handlers['copy'])
        if 'paste' in handlers:
            self.actions['paste'].triggered.connect(handlers['paste'])
        if 'find' in handlers:
            self.actions['find'].triggered.connect(handlers['find'])
        if 'replace' in handlers:
            self.actions['replace'].triggered.connect(handlers['replace'])
        if 'replace_all' in handlers:
            self.actions['replace_all'].triggered.connect(handlers['replace_all'])
    
    def update_language(self, new_language):
        """Обновление языка интерфейса"""
        self.current_language = new_language
        
        # Обновляем тексты действий
        for action_name, action in self.actions.items():
            if f'action_{action_name}' in TRANSLATIONS[new_language]:
                action.setText(TRANSLATIONS[new_language][f'action_{action_name}'])
    
    def remove_toolbar(self):
        """Удаление панели инструментов"""
        if self.toolbar:
            self.parent.removeToolBar(self.toolbar)
            self.toolbar.deleteLater()
            self.toolbar = None
    
    def get_action(self, action_name):
        """Получение действия по имени"""
        return self.actions.get(action_name)
    
    def get_all_actions(self):
        """Получение всех действий"""
        return self.actions 