import json
import os

class Config:
    DEFAULT_CONFIG = {
        'tree_font_family': 'Arial',
        'tree_font_size': 10,
        'note_font_family': 'Arial',
        'note_font_size': 11
    }
    
    def __init__(self, config_file='settings.json'):
        self.config_file = config_file
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Загрузка настроек из файла"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return {**self.DEFAULT_CONFIG, **json.load(f)}
            except:
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def save_settings(self):
        """Сохранение настроек в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except:
            return False
    
    def get(self, key, default=None):
        """Получение значения настройки"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Установка значения настройки"""
        self.settings[key] = value
        self.save_settings() 