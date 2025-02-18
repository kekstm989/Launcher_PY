import os
import json
import requests
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, Frame, IntVar
from threading import Thread
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# Константы
MODS_URL = "https://nexon-project.ru/mods/"
MODS_DIR = os.path.join(os.getenv('APPDATA'), ".minecraft", "mods")
CONFIG_PATH = "config.json"
WINDOW_WIDTH = 750
WINDOW_HEIGHT = 550

# Локализация интерфейса
LANGUAGES = {
    "ru": {
        "title": "🔧 Обновление модов Minecraft Nexon Project",
        "choose_theme": "Тема:",
        "apply_theme": "Применить",
        "choose_lang": "Язык:",
        "autoupdate": "Автообновление",
        "check_update": "🔄 Проверить и обновить",
        "done": "Готово",
        "update_available": "🔄 Обновление доступно",
        "up_to_date": "✅ Актуально",
        "update_completed": "Проверка обновлений завершена.",
        "updating": "⏳ Идет обновление... Пожалуйста, подождите.",
        "downloading": "📥 Загрузка {mod_name}...",
        "checking": "🔍 Проверка обновлений..."
    },
    "en": {
        "title": "🔧 Minecraft Nexon Project Mod Updater",
        "choose_theme": "Theme:",
        "apply_theme": "Apply",
        "choose_lang": "Language:",
        "autoupdate": "Auto-update",
        "check_update": "🔄 Check & Update",
        "done": "Done",
        "update_available": "🔄 Update Available",
        "up_to_date": "✅ Up-to-Date",
        "update_completed": "Update check completed.",
        "updating": "⏳ Updating... Please wait.",
        "downloading": "📥 Downloading {mod_name}...",
        "checking": "🔍 Checking for updates..."
    },
}

# Функции работы с конфигурацией
def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"theme": "darkly", "language": "ru", "auto_update": True}

def save_config(key, value):
    config[key] = value
    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)

# Загружаем настройки
config = load_config()
selected_theme = config.get("theme", "darkly")
selected_language = config.get("language", "ru")
auto_update = config.get("auto_update", True)
lang = LANGUAGES[selected_language]

# **Создание GUI**
root = ttk.Window(themename=selected_theme)
root.title(lang["title"])
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
root.resizable(False, False)

def center_window():
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - WINDOW_WIDTH) // 2
    y = (screen_height - WINDOW_HEIGHT) // 2
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

center_window()

# **Горизонтальные настройки**
settings_frame = Frame(root)
settings_frame.pack(pady=10)

# Тема
theme_label = ttk.Label(settings_frame, text=lang["choose_theme"])
theme_label.grid(row=0, column=0, padx=5)
theme_combobox = ttk.Combobox(settings_frame, values=["darkly", "superhero", "cyborg", "morph", "flatly", "journal"], state="readonly")
theme_combobox.grid(row=0, column=1, padx=5)
theme_combobox.set(selected_theme)
apply_theme_button = ttk.Button(settings_frame, text=lang["apply_theme"], command=lambda: save_config("theme", theme_combobox.get()))
apply_theme_button.grid(row=0, column=2, padx=5)

# Язык
lang_label = ttk.Label(settings_frame, text=lang["choose_lang"])
lang_label.grid(row=0, column=3, padx=5)
lang_combobox = ttk.Combobox(settings_frame, values=["ru", "en"], state="readonly")
lang_combobox.grid(row=0, column=4, padx=5)
lang_combobox.set(selected_language)
apply_lang_button = ttk.Button(settings_frame, text=lang["apply_theme"], command=lambda: save_config("language", lang_combobox.get()))
apply_lang_button.grid(row=0, column=5, padx=5)

# Автообновление
autoupdate_var = IntVar(value=int(auto_update))
autoupdate_checkbox = ttk.Checkbutton(settings_frame, text=lang["autoupdate"], bootstyle="success", variable=autoupdate_var, command=lambda: save_config("auto_update", bool(autoupdate_var.get())))
autoupdate_checkbox.grid(row=0, column=6, padx=5)

# **Список модов**
columns = ("Имя мода", "Статус")
mod_list = ttk.Treeview(root, columns=columns, show="headings", bootstyle="info")
for col in columns:
    mod_list.heading(col, text=col)
    mod_list.column(col, anchor="center", width=250)
mod_list.pack(pady=5, fill=BOTH, expand=True)

update_button = ttk.Button(root, text=lang["check_update"], command=lambda: Thread(target=update_mods).start(), bootstyle="primary-outline")
update_button.pack(pady=10)

# **Функция работы с модами**
def fetch_mod_list():
    try:
        response = requests.get(MODS_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return [link.get('href') for link in soup.find_all('a') if link.get('href').endswith('.jar')]
    except requests.exceptions.RequestException:
        return []

def get_server_file_date(mod_name):
    try:
        response = requests.head(f"{MODS_URL}{mod_name}", allow_redirects=True)
        response.raise_for_status()
        last_modified = response.headers.get('Last-Modified', None)
        if last_modified:
            try:
                server_time = parsedate_to_datetime(last_modified)
                if server_time.tzinfo is None:
                    server_time = server_time.replace(tzinfo=timezone.utc)
                return server_time.replace(microsecond=0)
            except Exception:
                return None
    except requests.exceptions.RequestException:
        return None

def get_local_file_date(mod_name):
    local_path = os.path.join(MODS_DIR, mod_name)
    if os.path.exists(local_path):
        return datetime.fromtimestamp(os.path.getmtime(local_path), timezone.utc).replace(microsecond=0)
    return None

def download_mod(mod_name):
    try:
        url = f"{MODS_URL}{mod_name}"
        file_path = os.path.join(MODS_DIR, mod_name)
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Ошибка", f"Ошибка загрузки: {e}")

def update_mods():
    mod_list.delete(*mod_list.get_children())  # Очистка списка перед обновлением
    mods_on_server = set(fetch_mod_list())  # Получаем список файлов на сервере
    mods_local = {mod for mod in os.listdir(MODS_DIR) if mod.endswith(".jar")}  # Получаем список локальных модов

    to_update = []
    to_delete = mods_local - mods_on_server  # Оставляем только те моды, которых нет на сервере

    # Удаляем только отсутствующие на сервере моды
    for mod_name in to_delete:
        local_path = os.path.join(MODS_DIR, mod_name)
        try:
            os.remove(local_path)  # Удаляем файл
            print(f"🗑 Удален устаревший мод: {mod_name}")
        except Exception as e:
            print(f"❌ Ошибка при удалении {mod_name}: {e}")

    for mod_name in mods_on_server:
        server_date = get_server_file_date(mod_name)
        local_date = get_local_file_date(mod_name)

        if local_date is None:
            # Если файла нет локально – мод нужно скачать
            status = lang["update_available"]
            to_update.append(mod_name)
        elif server_date and local_date and server_date > local_date:
            # Если версия сервера новее – обновляем
            status = lang["update_available"]
            to_update.append(mod_name)
        else:
            # Если мод уже актуален
            status = lang["up_to_date"]

        # Добавляем в список GUI
        mod_list.insert("", "end", values=(mod_name, status))

    if to_update:
        for mod_name in to_update:
            download_mod(mod_name)

    messagebox.showinfo(lang["done"], lang["update_completed"])

if auto_update:
    Thread(target=update_mods).start()

root.mainloop()
