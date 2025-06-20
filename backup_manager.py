import os
import shutil
from datetime import datetime, timedelta
import atexit

class BackupManager:
    def __init__(self, base_dir):
        """
        Инициализация менеджера бэкапов
        
        Args:
            base_dir (str): Базовая директория для создания папки backup
        """
        self.base_dir = base_dir
        self.backup_dir = os.path.join(base_dir, "backup")
        
        # Создаем папку backup, если её нет
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self, db_path=None):
        """
        Создание бэкапа базы данных
        
        Args:
            db_path (str, optional): Путь к файлу базы данных. 
                                   Если не указан, ищет .db файлы в base_dir
        
        Returns:
            str: Путь к созданному бэкапу или None в случае ошибки
        """
        try:
            # Если путь к БД не указан, ищем .db файлы в base_dir
            if db_path is None:
                db_files = [file for file in os.listdir(self.base_dir) if file.endswith('.db')]
                if not db_files:
                    return None
                db_file = db_files[0]  # Берем первый найденный .db файл
                db_path = os.path.join(self.base_dir, db_file)
            else:
                db_file = os.path.basename(db_path)
            
            # Проверяем, существует ли файл базы данных
            if not os.path.exists(db_path):
                return None
            
            # Создаем имя файла бэкапа с временной меткой
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{db_file}_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Копируем файл базы данных
            shutil.copy2(db_path, backup_path)
            
            # Очищаем старые бэкапы
            self.cleanup_old_backups(db_file)
            
            return backup_path
            
        except Exception as e:
            print(f"Ошибка при создании бэкапа: {e}")
            return None
    
    def cleanup_old_backups(self, db_name, max_days=10):
        """
        Удаление старых бэкапов
        
        Args:
            db_name (str): Имя файла базы данных (без пути)
            max_days (int): Максимальное количество дней хранения бэкапов
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=max_days)
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith(db_name) and filename.endswith(".db"):
                    file_path = os.path.join(self.backup_dir, filename)
                    try:
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time < cutoff_date:
                            os.remove(file_path)
                            print(f"Удален старый бэкап: {filename}")
                    except Exception as e:
                        print(f"Ошибка при удалении старого бэкапа {filename}: {e}")
        except Exception as e:
            print(f"Ошибка при очистке старых бэкапов: {e}")
    
    def get_backup_list(self, db_name=None):
        """
        Получение списка доступных бэкапов
        
        Args:
            db_name (str, optional): Имя файла базы данных для фильтрации
        
        Returns:
            list: Список путей к файлам бэкапов
        """
        try:
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.endswith(".db"):
                    if db_name is None or filename.startswith(db_name):
                        file_path = os.path.join(self.backup_dir, filename)
                        backup_files.append(file_path)
            
            # Сортируем по дате создания (от новых к старым)
            backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            return backup_files
        except Exception as e:
            print(f"Ошибка при получении списка бэкапов: {e}")
            return []
    
    def restore_backup(self, backup_path, target_path):
        """
        Восстановление базы данных из бэкапа
        
        Args:
            backup_path (str): Путь к файлу бэкапа
            target_path (str): Путь для восстановления базы данных
        
        Returns:
            bool: True если восстановление успешно, False в случае ошибки
        """
        try:
            if not os.path.exists(backup_path):
                return False
            
            # Копируем бэкап на место основной базы данных
            shutil.copy2(backup_path, target_path)
            return True
            
        except Exception as e:
            print(f"Ошибка при восстановлении бэкапа: {e}")
            return False

# Глобальная переменная для хранения экземпляра менеджера
_backup_manager = None

def init_backup_manager(base_dir):
    """
    Инициализация глобального менеджера бэкапов
    
    Args:
        base_dir (str): Базовая директория
    """
    global _backup_manager
    _backup_manager = BackupManager(base_dir)

def create_backup_on_exit():
    """
    Функция для создания бэкапа при завершении программы
    Регистрируется через atexit.register
    """
    global _backup_manager
    if _backup_manager:
        _backup_manager.create_backup()

def register_exit_handler():
    """
    Регистрация обработчика завершения программы
    """
    atexit.register(create_backup_on_exit) 