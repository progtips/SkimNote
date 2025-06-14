import json
import os

class Config:
    def __init__(self):
        self.config_file = "settings.json"
        self.default_settings = {
            'db_path': 'notes.db',
            'theme': 'Системная',
            'font_size': 12,
            'auto_save': True,
            'save_interval': 5
        }
        
    def get_settings(self):
        """Получение настроек из файла"""
        if not os.path.exists(self.config_file):
            return self.default_settings
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Обновляем настройки по умолчанию
                for key, value in self.default_settings.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        except Exception:
            return self.default_settings
            
    def save_settings(self, settings):
        """Сохранение настроек в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False
            
    def get(self, key, default=None):
        """Получение значения настройки по ключу"""
        settings = self.get_settings()
        return settings.get(key, default)
        
    def set(self, key, value):
        """Установка значения настройки"""
        settings = self.get_settings()
        settings[key] = value
        return self.save_settings(settings)

    def get_db_path(self):
        return self.get('db_path', 'notes.db') 