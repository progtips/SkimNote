import os
import configparser
import sys

class Config:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            # Если приложение запущено как exe
            self.config_file = os.path.join(os.path.dirname(sys.executable), 'settings.ini')
        else:
            # Если приложение запущено из исходников
            self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.ini')
            
        self.default_settings = {
            'language': 'Русский',
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
            config = configparser.ConfigParser()
            config.read(self.config_file, encoding='utf-8')
            
            # Получаем настройки из секции main
            if 'main' not in config:
                return self.default_settings
                
            settings = {}
            for key, value in self.default_settings.items():
                if key in config['main']:
                    # Преобразуем строковые значения в соответствующие типы
                    if isinstance(value, bool):
                        settings[key] = config['main'].getboolean(key)
                    elif isinstance(value, int):
                        settings[key] = config['main'].getint(key)
                    else:
                        settings[key] = config['main'][key]
                else:
                    settings[key] = value
                    
            return settings
        except Exception:
            return self.default_settings
            
    def save_settings(self, settings):
        """Сохранение настроек в файл"""
        try:
            config = configparser.ConfigParser()
            
            # Создаем секцию main
            config['main'] = {}
            
            # Сохраняем все настройки
            for key, value in settings.items():
                config['main'][key] = str(value)
            
            # Создаем директорию для файла настроек, если она не существует
            settings_dir = os.path.dirname(self.config_file)
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
                
            # Сохраняем файл
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
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