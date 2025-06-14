from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QCheckBox, QSpinBox, QLineEdit, QFileDialog)
from PyQt6.QtCore import Qt
from config import Config

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setModal(True)
        
        self.config = Config()
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        
        # Путь к базе данных
        db_layout = QHBoxLayout()
        db_label = QLabel("Путь к базе данных:")
        self.db_path_edit = QLineEdit()
        self.db_browse_btn = QPushButton("...")
        self.db_browse_btn.clicked.connect(self.browse_db_path)
        db_layout.addWidget(db_label)
        db_layout.addWidget(self.db_path_edit)
        db_layout.addWidget(self.db_browse_btn)
        layout.addLayout(db_layout)
        
        # Тема оформления
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Тема оформления:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Темная", "Системная"])
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)
        
        # Размер шрифта
        font_layout = QHBoxLayout()
        font_label = QLabel("Размер шрифта:")
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(12)
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_size)
        layout.addLayout(font_layout)
        
        # Автосохранение
        self.auto_save = QCheckBox("Автоматическое сохранение")
        layout.addWidget(self.auto_save)
        
        # Интервал автосохранения
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Интервал автосохранения (сек):")
        self.save_interval = QSpinBox()
        self.save_interval.setRange(1, 60)
        self.save_interval.setValue(5)
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.save_interval)
        layout.addLayout(interval_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
    def browse_db_path(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл базы данных", "", "Базы данных (*.db);;Все файлы (*)")
        if file_path:
            self.db_path_edit.setText(file_path)
        
    def load_settings(self):
        """Загрузка настроек"""
        settings = self.config.get_settings()
        
        # Загружаем путь к базе данных
        self.db_path_edit.setText(settings.get('db_path', 'notes.db'))
        
        # Загружаем тему
        theme_index = self.theme_combo.findText(settings.get('theme', 'Системная'))
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
            
        # Загружаем размер шрифта
        self.font_size.setValue(settings.get('font_size', 12))
        
        # Загружаем настройки автосохранения
        self.auto_save.setChecked(settings.get('auto_save', True))
        self.save_interval.setValue(settings.get('save_interval', 5))
        
    def save_settings(self):
        """Сохранение настроек"""
        settings = {
            'db_path': self.db_path_edit.text(),
            'theme': self.theme_combo.currentText(),
            'font_size': self.font_size.value(),
            'auto_save': self.auto_save.isChecked(),
            'save_interval': self.save_interval.value()
        }
        
        self.config.save_settings(settings)
        self.accept() 