import tkinter as tk
from tkinter import ttk
from tkinter import font

class SettingsDialog:
    def __init__(self, parent, config):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Настройки")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.config = config
        self.result = None
        
        # Получаем список доступных шрифтов
        self.available_fonts = sorted(font.families())
        
        self.create_widgets()
        self.center_dialog()
        
    def create_widgets(self):
        # Создаем вкладки
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Вкладка шрифтов
        fonts_frame = ttk.Frame(notebook)
        notebook.add(fonts_frame, text="Шрифты")
        
        # Настройки шрифта дерева заметок
        tree_frame = ttk.LabelFrame(fonts_frame, text="Дерево заметок")
        tree_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(tree_frame, text="Шрифт:").grid(row=0, column=0, padx=5, pady=5)
        self.tree_font = ttk.Combobox(tree_frame, values=self.available_fonts, state="readonly")
        self.tree_font.set(self.config.get('tree_font_family'))
        self.tree_font.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(tree_frame, text="Размер:").grid(row=1, column=0, padx=5, pady=5)
        self.tree_size = ttk.Spinbox(tree_frame, from_=8, to=24, width=5)
        self.tree_size.set(self.config.get('tree_font_size'))
        self.tree_size.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Настройки шрифта текста заметок
        note_frame = ttk.LabelFrame(fonts_frame, text="Текст заметок")
        note_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(note_frame, text="Шрифт:").grid(row=0, column=0, padx=5, pady=5)
        self.note_font = ttk.Combobox(note_frame, values=self.available_fonts, state="readonly")
        self.note_font.set(self.config.get('note_font_family'))
        self.note_font.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(note_frame, text="Размер:").grid(row=1, column=0, padx=5, pady=5)
        self.note_size = ttk.Spinbox(note_frame, from_=8, to=24, width=5)
        self.note_size.set(self.config.get('note_font_size'))
        self.note_size.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Кнопки
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(buttons_frame, text="OK", command=self.save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.RIGHT)
        
    def center_dialog(self):
        """Центрирование диалога относительно главного окна"""
        self.dialog.update_idletasks()
        
        # Получаем размеры и позицию главного окна
        parent = self.dialog.master
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # Получаем размеры диалога
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Вычисляем позицию для центрирования
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # Устанавливаем позицию диалога
        self.dialog.geometry(f"+{x}+{y}")
        
    def save_settings(self):
        """Сохранение настроек"""
        # Сохраняем настройки шрифтов
        self.config.set('tree_font_family', self.tree_font.get())
        self.config.set('tree_font_size', int(self.tree_size.get()))
        self.config.set('note_font_family', self.note_font.get())
        self.config.set('note_font_size', int(self.note_size.get()))
        
        self.result = True
        self.dialog.destroy() 