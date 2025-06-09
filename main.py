import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from ttkthemes import ThemedTk
from database import NotesDB
from config import Config
from settings_dialog import SettingsDialog

class NotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SkimNote - Менеджер заметок")
        self.root.geometry("1000x600")
        
        # Центрируем окно на экране
        self.center_window()
        
        # Загружаем настройки
        self.config = Config()
        
        self.db = NotesDB()
        self.current_note_id = None
        self.current_parent_id = 1
        self.content_modified = False
        self.editing_title = False

        self.create_menu()
        self.create_toolbar()
        self.setup_ui()
        self.load_notes()
        self.setup_shortcuts()
        self.apply_settings()

        # Привязываем обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self):
        """Центрирование окна на экране"""
        # Получаем размеры экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Получаем размеры окна
        window_width = 1000
        window_height = 600
        
        # Вычисляем координаты для центрирования
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)
        
        # Устанавливаем позицию окна
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

    def setup_shortcuts(self):
        """Настройка горячих клавиш"""
        self.root.bind('<Insert>', lambda e: self.new_note())
        self.root.bind('<Alt-Insert>', lambda e: self.new_subnote())
        self.root.bind('<Delete>', lambda e: self.delete_note())

    def create_menu(self):
        # Создаем главное меню
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # Меню "Файл"
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новая заметка (Insert)", command=self.new_note)
        file_menu.add_command(label="Новая вложенная заметка (Alt+Insert)", command=self.new_subnote)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_closing)

        # Меню "Настройки"
        settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Настройки", menu=settings_menu)
        settings_menu.add_command(label="Параметры...", command=self.show_settings)

        # Меню "Справка"
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)

    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=2)

        # Создаем кнопки с иконками и всплывающими подсказками
        ttk.Button(toolbar, text="➕", width=3,
                  command=self.new_note).pack(side=tk.LEFT, padx=2)
        self.create_tooltip(toolbar.winfo_children()[-1], 
                          "Новая заметка (Insert)")

        ttk.Button(toolbar, text="⊕", width=3,
                  command=self.new_subnote).pack(side=tk.LEFT, padx=2)
        self.create_tooltip(toolbar.winfo_children()[-1], 
                          "Новая вложенная заметка (Alt+Insert)")

        ttk.Button(toolbar, text="🗑", width=3,
                  command=self.delete_note).pack(side=tk.LEFT, padx=2)
        self.create_tooltip(toolbar.winfo_children()[-1], 
                          "Удалить заметку (Delete)")

    def create_tooltip(self, widget, text):
        """Создание всплывающей подсказки для виджета"""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20
            
            # Создаем всплывающее окно
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(self.tooltip, text=text, 
                            background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()

        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                del self.tooltip

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def load_notes(self, parent=''):
        # Очищаем дерево
        if not parent:
            for item in self.notes_tree.get_children():
                self.notes_tree.delete(item)
            
            # Получаем все заметки из БД
            notes = self.db.get_notes(None)
            # Создаем словарь для быстрого поиска родителей
            self.notes_dict = {note[0]: note for note in notes}
            
            # Сначала добавляем корневые заметки
            for note in notes:
                note_id, title, content, parent_id, created_at, updated_at = note
                if parent_id is None or parent_id == 1:
                    self.notes_tree.insert('', tk.END, str(note_id), text=title)
            
            # Затем добавляем все остальные заметки
            for note in notes:
                note_id, title, content, parent_id, created_at, updated_at = note
                if parent_id and parent_id != 1:
                    self.notes_tree.insert(str(parent_id), tk.END, str(note_id), text=title)

    def new_note(self):
        """Создать новую заметку"""
        try:
            note_id = self.db.add_note("Новая заметка", "", self.current_parent_id)
            self.load_notes()
            # Выбираем созданную заметку
            self.notes_tree.selection_set(str(note_id))
            self.notes_tree.see(str(note_id))
            self.notes_tree.focus(str(note_id))
            # Сразу запускаем переименование
            self.start_rename()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать заметку: {str(e)}")

    def new_subnote(self):
        """Создать новую вложенную заметку"""
        if not self.notes_tree.selection():
            return
            
        parent_id = int(self.notes_tree.selection()[0])
        try:
            note_id = self.db.add_note("Новая заметка", "", parent_id)
            self.load_notes()
            # Выбираем созданную заметку
            self.notes_tree.selection_set(str(note_id))
            self.notes_tree.see(str(note_id))
            self.notes_tree.focus(str(note_id))
            # Сразу запускаем переименование
            self.start_rename()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать заметку: {str(e)}")

    def save_current_note(self):
        if self.current_note_id and self.content_modified:
            content = self.note_content.get('1.0', tk.END).strip()
            try:
                note = self.db.get_note(self.current_note_id)
                if note:
                    self.db.update_note(self.current_note_id, note[1], content)
                    self.content_modified = False
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить заметку: {str(e)}")

    def delete_note(self):
        if not self.notes_tree.selection():
            return
            
        note_id = int(self.notes_tree.selection()[0])
        
        # Не позволяем удалить корневую заметку
        if note_id == 1:
            messagebox.showwarning("Предупреждение", "Нельзя удалить корневую заметку")
            return
            
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту заметку?"):
            try:
                self.db.delete_note(note_id)
                self.load_notes()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить заметку: {str(e)}")

    def on_note_select(self, event):
        if self.current_note_id:
            self.save_current_note()
            
        selected = self.notes_tree.selection()
        if selected:
            note_id = int(selected[0])
            note = self.db.get_note(note_id)
            if note:
                self.current_note_id = note_id
                self.current_parent_id = note[3] if note[3] else 1
                self.note_content.delete('1.0', tk.END)
                if note[2]:  # content
                    self.note_content.insert('1.0', note[2])
                self.content_modified = False
                self.note_content.edit_modified(False)

    def show_context_menu(self, event):
        # Получаем элемент под курсором
        item = self.notes_tree.identify_row(event.y)
        
        if item:
            # Выбираем элемент, на котором вызвано контекстное меню
            self.notes_tree.selection_set(item)
            # Обновляем current_note_id и current_parent_id
            self.current_note_id = int(item)
            note = self.db.get_note(self.current_note_id)
            if note:
                self.current_parent_id = note[3] if note[3] else 1
        else:
            # Если клик не на заметке, создаем в корневой папке
            self.current_note_id = None
            self.current_parent_id = 1
            
        # Показываем/скрываем пункты меню в зависимости от контекста
        if item:
            # Если выбрана заметка, показываем все пункты
            self.context_menu.entryconfig("📑 Добавить вложенную", state="normal")
            self.context_menu.entryconfig("✏️ Переименовать", state="normal")
            self.context_menu.entryconfig("🗑️ Удалить", state="normal")
            if int(item) == 1:  # Корневая заметка
                self.context_menu.entryconfig("🗑️ Удалить", state="disabled")
        else:
            # Если клик на пустом месте, оставляем только создание новой заметки
            self.context_menu.entryconfig("📝 Добавить заметку", state="disabled")
            self.context_menu.entryconfig("✏️ Переименовать", state="disabled")
            self.context_menu.entryconfig("🗑️ Удалить", state="disabled")
        
        # Показываем контекстное меню
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def on_content_modified(self, event=None):
        if self.note_content.edit_modified():
            self.content_modified = True
            self.note_content.edit_modified(False)

    def on_closing(self):
        self.save_current_note()
        self.root.destroy()

    def start_rename(self, event=None):
        """Начать редактирование названия заметки"""
        if not self.notes_tree.selection():
            return
            
        item_id = self.notes_tree.selection()[0]
        
        # Не позволяем редактировать корневую заметку
        if int(item_id) == 1:
            return
            
        if not self.editing_title:
            self.editing_title = True
            # Получаем координаты и размеры выбранного элемента
            bbox = self.notes_tree.bbox(item_id)
            if not bbox:
                return
                
            # Настраиваем поле ввода
            self.title_editor.delete(0, tk.END)
            self.title_editor.insert(0, self.notes_tree.item(item_id)['text'])
            
            # Размещаем поле ввода поверх элемента дерева
            self.title_editor.place(x=bbox[0], y=bbox[1],
                                  width=bbox[2], height=bbox[3])
            self.title_editor.focus_set()
            self.title_editor.selection_range(0, tk.END)

    def finish_rename(self, event=None):
        """Завершить редактирование названия заметки"""
        if not self.editing_title:
            return
            
        # Получаем новое название
        new_title = self.title_editor.get().strip()
        item_id = self.notes_tree.selection()[0]
        
        if new_title:  # Проверяем, что название не пустое
            try:
                note = self.db.get_note(int(item_id))
                if note:
                    self.db.update_note(int(item_id), new_title, note[2])
                    self.notes_tree.item(item_id, text=new_title)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось переименовать заметку: {str(e)}")
        
        self.title_editor.place_forget()
        self.editing_title = False
        self.notes_tree.focus_set()
        # Восстанавливаем выделение заметки
        self.notes_tree.selection_set(item_id)
        self.notes_tree.focus(item_id)

    def cancel_rename(self, event=None):
        """Отменить редактирование названия заметки"""
        if self.editing_title:
            item_id = self.notes_tree.selection()[0]
            self.title_editor.place_forget()
            self.editing_title = False
            self.notes_tree.focus_set()
            # Восстанавливаем выделение заметки
            self.notes_tree.selection_set(item_id)
            self.notes_tree.focus(item_id)

    def show_about(self):
        messagebox.showinfo("О программе", 
            "SkimNote - Менеджер заметок\n\n"
            "Горячие клавиши:\n"
            "Insert - Новая заметка\n"
            "Alt+Insert - Новая вложенная заметка\n"
            "F2 - Переименовать заметку\n"
            "Delete - Удалить заметку\n\n"
            "© 2024")

    def show_settings(self):
        """Показать диалог настроек"""
        dialog = SettingsDialog(self.root, self.config)
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            self.apply_settings()

    def apply_settings(self):
        """Применить настройки к интерфейсу"""
        # Настройки шрифта дерева
        # Для Treeview нужно использовать размер на 2-3 пункта больше,
        # чтобы визуально соответствовать размеру обычного текста
        tree_font_size = self.config.get('tree_font_size')
        tree_font = (self.config.get('tree_font_family'), 
                    tree_font_size + 3)
        style = ttk.Style()
        style.configure('Treeview', font=tree_font, rowheight=tree_font_size + 10)
        
        # Настройки шрифта заметок
        note_font = (self.config.get('note_font_family'), 
                    self.config.get('note_font_size'))
        self.note_content.configure(font=note_font)

    def setup_ui(self):
        # Создаем главный контейнер
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая панель с деревом заметок
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=1)

        # Дерево заметок
        self.notes_tree = ttk.Treeview(left_frame, selectmode='browse')
        self.notes_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notes_tree.heading('#0', text='Заметки', anchor=tk.W)
        
        # Привязываем события для дерева
        self.notes_tree.bind('<<TreeviewSelect>>', self.on_note_select)
        self.notes_tree.bind('<Double-1>', self.start_rename)
        self.notes_tree.bind('<Return>', self.start_rename)
        self.notes_tree.bind('<Escape>', self.cancel_rename)
        self.notes_tree.bind('<F2>', self.start_rename)
        
        # Создаем поле ввода для редактирования
        self.title_editor = ttk.Entry(self.notes_tree)
        self.title_editor.bind('<Return>', self.finish_rename)
        self.title_editor.bind('<Escape>', self.cancel_rename)
        self.title_editor.bind('<FocusOut>', self.finish_rename)
        
        # Создаем контекстное меню
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="📝 Добавить заметку", command=self.new_note)
        self.context_menu.add_command(label="📑 Добавить вложенную", command=self.new_subnote)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="✏️ Переименовать", command=self.start_rename)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Удалить", command=self.delete_note)
        
        # Привязываем появление контекстного меню к правой кнопке мыши
        self.notes_tree.bind('<Button-3>', self.show_context_menu)

        # Правая панель с редактором
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=3)

        # Поле для редактирования заметки
        self.note_content = tk.Text(right_frame, wrap=tk.WORD)
        self.note_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Отслеживаем изменения в тексте
        self.note_content.bind('<<Modified>>', self.on_content_modified)

if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    app = NotesApp(root)
    root.mainloop() 