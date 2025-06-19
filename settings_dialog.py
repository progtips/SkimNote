from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QSpinBox, QLineEdit, QFileDialog)
from PyQt6.QtCore import Qt
from config import Config
from translations import TRANSLATIONS

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.current_language = self.config.get('language', 'Русский')
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        
        # Язык интерфейса
        lang_layout = QHBoxLayout()
        lang_label = QLabel(TRANSLATIONS[self.current_language]['settings_language'])
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Русский", "English"])
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)
        
        # Путь к базе данных
        db_layout = QHBoxLayout()
        db_label = QLabel(TRANSLATIONS[self.current_language]['settings_db_path'])
        self.db_path_edit = QLineEdit()
        self.db_browse_btn = QPushButton(TRANSLATIONS[self.current_language]['settings_browse'])
        self.db_browse_btn.clicked.connect(self.browse_db_path)
        db_layout.addWidget(db_label)
        db_layout.addWidget(self.db_path_edit)
        db_layout.addWidget(self.db_browse_btn)
        layout.addLayout(db_layout)
        
        # Размер шрифта
        font_layout = QHBoxLayout()
        font_label = QLabel(TRANSLATIONS[self.current_language]['settings_font_size'])
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(12)
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_size)
        layout.addLayout(font_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        save_button = QPushButton(TRANSLATIONS[self.current_language]['settings_save'])
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton(TRANSLATIONS[self.current_language]['settings_cancel'])
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Устанавливаем заголовок окна
        self.setWindowTitle(TRANSLATIONS[self.current_language]['settings_title'])
        
    def browse_db_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            TRANSLATIONS[self.current_language]['settings_db_path'],
            "", 
            "Базы данных (*.db);;Все файлы (*)"
        )
        if file_path:
            self.db_path_edit.setText(file_path)
        
    def load_settings(self):
        """Загрузка настроек"""
        settings = self.config.get_settings()
        
        # Загружаем язык интерфейса
        lang_index = self.lang_combo.findText(settings.get('language', 'Русский'))
        if lang_index >= 0:
            self.lang_combo.setCurrentIndex(lang_index)
        
        # Загружаем путь к базе данных
        self.db_path_edit.setText(settings.get('db_path', 'notes.db'))
        
        # Загружаем размер шрифта
        self.font_size.setValue(settings.get('font_size', 12))
        
    def save_settings(self):
        """Сохранение настроек"""
        settings = {
            'language': self.lang_combo.currentText(),
            'db_path': self.db_path_edit.text(),
            'font_size': self.font_size.value()
        }
        
        self.config.save_settings(settings)
        self.accept() 