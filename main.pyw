import os
import random
import configparser
import tkinter as tk
from tkinter import ttk, font, messagebox
from pygame import mixer
from mutagen import File
import pystray
from PIL import Image, ImageTk
import threading
import time
from win10toast import ToastNotifier  # Для уведомлений

mixer.init()

class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            self.create_default_config()
        
        self.config.read(self.config_file)
        self.music_folder = self.config.get('Settings', 'music_folder', 
                          fallback=os.path.join(os.path.expanduser("~"), "Музыка"))
        self.notifications_enabled = self.config.getboolean('Settings', 'notifications', fallback=True)
        
        self.bg_color = self.config.get('Colors', 'background', fallback='#0a1a2f')
        self.primary_color = self.config.get('Colors', 'primary', fallback='#1a2f4f')
        self.secondary_color = self.config.get('Colors', 'secondary', fallback='#2a4f7f')
        self.text_color = self.config.get('Colors', 'text', fallback='white')
        self.button_color = self.config.get('Colors', 'button', fallback='#3a6faf')

    def create_default_config(self):
        self.config['Settings'] = {
            'music_folder': os.path.join(os.path.expanduser("~"), "Музыка"),
            'notifications': 'True'  # Уведомления включены по умолчанию
        }
        self.config['Colors'] = {
            'background': '#0a1a2f',
            'primary': '#1a2f4f',
            'secondary': '#2a4f7f',
            'text': 'white',
            'button': '#3a6faf'
        }
        with open(self.config_file, 'w') as f:
            self.config.write(f)

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Оркестр")
        self.root.geometry("400x800")
        self.config = Config()
        self.tray_icon = None
        self.tray_running = False
        self.paused_position = 0
        self.shuffle_mode = False
        self.repeat_mode = False
        self.original_playlist = []
        self.current_track_length = 0
        self.auto_scroll = True
        self.toaster = ToastNotifier()  # Инициализация уведомлений
        
        self.setup_ui()
        self.load_music()
        self.setup_tray()
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        self.root.after(100, self.update_time)
        self.root.after(100, self.auto_scroll_track)

    def setup_ui(self):
        self.root.overrideredirect(True)
        self.root.configure(bg=self.config.bg_color)
        
        # Верхняя панель
        self.title_bar = tk.Frame(self.root, bg=self.config.primary_color)
        self.title_bar.pack(fill=tk.X)
        
        # Кнопки управления окном
        self.minimize_btn = tk.Button(self.title_bar, text="—", command=self.minimize_to_tray,
                                    bg=self.config.primary_color, fg=self.config.text_color, bd=0)
        self.minimize_btn.pack(side=tk.LEFT, padx=5)
        
        self.title_label = tk.Label(self.title_bar, text="Оркестр", 
                                  bg=self.config.primary_color, fg=self.config.text_color)
        self.title_label.pack(side=tk.LEFT, padx=10)
        
        # Поиск
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.title_bar, textvariable=self.search_var, width=20,
                                    bg=self.config.secondary_color, fg=self.config.text_color)
        self.search_entry.pack(side=tk.RIGHT, padx=10)
        self.search_entry.bind("<KeyRelease>", self.filter_tracks)
        
        self.close_btn = tk.Button(self.title_bar, text="✕", command=self.quit_app,
                                 bg=self.config.primary_color, fg=self.config.text_color, bd=0)
        self.close_btn.pack(side=tk.RIGHT)
        
        # Основной контейнер
        self.main_frame = tk.Frame(self.root, bg=self.config.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Список треков
        self.canvas = tk.Canvas(self.main_frame, bg=self.config.bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.config.bg_color)
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Панель управления
        self.control_frame = tk.Frame(self.root, bg=self.config.primary_color)
        self.control_frame.pack(fill=tk.X, pady=5)
        
        self.setup_controls()
        self.setup_scroll()
        
        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.on_move)

    def setup_controls(self):
        btn_style = {
            'bg': self.config.button_color,
            'fg': self.config.text_color,
            'bd': 0,
            'activebackground': self.config.secondary_color
        }
        
        self.repeat_btn = tk.Button(self.control_frame, text="🔁", font=("Arial", 12),
                                   command=self.toggle_repeat, **btn_style)
        self.repeat_btn.pack(side=tk.LEFT, padx=5)
        
        self.shuffle_btn = tk.Button(self.control_frame, text="🔀", font=("Arial", 12),
                                   command=self.toggle_shuffle, **btn_style)
        self.shuffle_btn.pack(side=tk.LEFT, padx=5)
        
        self.prev_btn = tk.Button(self.control_frame, text="⏮", font=("Arial", 12), 
                                command=self.prev_track, **btn_style)
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.play_btn = tk.Button(self.control_frame, text="▶", font=("Arial", 14), 
                                command=self.toggle_play, **btn_style)
        self.play_btn.pack(side=tk.LEFT, padx=10)
        
        self.next_btn = tk.Button(self.control_frame, text="⏭", font=("Arial", 12), 
                                command=self.next_track, **btn_style)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        self.time_label = tk.Label(self.control_frame, text="00:00 / 00:00", 
                                 bg=self.config.primary_color, fg=self.config.text_color)
        self.time_label.pack(side=tk.LEFT, padx=10)
        
        self.volume_scale = ttk.Scale(self.control_frame, from_=0, to=1, 
                                    command=self.set_volume, style="TScale")
        self.volume_scale.set(0.5)
        self.volume_scale.pack(side=tk.RIGHT, padx=10)
        
        mixer.music.set_volume(0.5)

    def setup_scroll(self):
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)
        self.scrollable_frame.bind("<Enter>", lambda _: self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel))
        self.scrollable_frame.bind("<Leave>", lambda _: self.canvas.unbind_all("<MouseWheel>"))

    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def filter_tracks(self, event=None):
        query = self.search_var.get().lower()
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        for idx, path in enumerate(self.playlist):
            if query in os.path.basename(path).lower():
                self.create_track_item(path, idx)

    def create_track_item(self, path, index):
        frame = tk.Frame(self.scrollable_frame, bg=self.config.primary_color, pady=5)
        frame.pack(fill=tk.X, padx=5, pady=2)
        
        btn = tk.Button(frame, text="▶", width=3, command=lambda: self.play_index(index),
                      bg=self.config.button_color, fg=self.config.text_color, bd=0)
        btn.pack(side=tk.LEFT, padx=5)
        
        filename = os.path.basename(path)
        if len(filename) > 40:
            filename = f"{filename[:30]}...{filename[-10:]}"
        
        label = tk.Label(frame, text=filename, anchor='w', 
                       bg=self.config.primary_color, fg=self.config.text_color)
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        duration = self.get_duration(path)
        time_label = tk.Label(frame, text=duration, 
                            bg=self.config.primary_color, fg=self.config.text_color)
        time_label.pack(side=tk.RIGHT, padx=10)
        
        return frame

    def get_duration(self, path):
        try:
            audio = File(path)
            length = audio.info.length
            return f"{int(length // 60):02}:{int(length % 60):02}"
        except:
            return "--:--"

    def load_music(self):
        self.playlist = []
        self.original_playlist = []
        for root, _, files in os.walk(self.config.music_folder):
            for file in files:
                if file.split('.')[-1].lower() in ["mp3", "wav", "ogg", "flac", "m4a"]:
                    full_path = os.path.join(root, file)
                    self.playlist.append(full_path)
                    self.original_playlist.append(full_path)
        
        for idx, path in enumerate(self.playlist):
            self.create_track_item(path, idx)

    def play_index(self, index):
        self.current_index = index
        self.play_track()

    def play_track(self):
        mixer.music.load(self.playlist[self.current_index])
        mixer.music.play()
        self.play_btn.config(text="⏸")
        self.paused_position = 0
        self.current_track_length = self.get_track_length()
        self.highlight_current_track()
        self.show_notification(f"Сейчас играет: {os.path.basename(self.playlist[self.current_index])}")

    def toggle_play(self):
        if mixer.music.get_busy():
            self.paused_position = mixer.music.get_pos() / 1000
            mixer.music.pause()
            self.play_btn.config(text="▶")
        else:
            if self.paused_position > 0:
                mixer.music.unpause()
            else:
                mixer.music.load(self.playlist[self.current_index])
                mixer.music.play(start=self.paused_position)
            self.play_btn.config(text="⏸")

    def prev_track(self):
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.play_track()

    def next_track(self):
        if self.repeat_mode:
            self.play_track()
        else:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play_track()

    def stop_playlist(self):
        mixer.music.stop()
        self.play_btn.config(text="▶")
        self.paused_position = 0

    def set_volume(self, val):
        mixer.music.set_volume(float(val))

    def update_time(self):
        if mixer.music.get_busy():
            current_time = (mixer.music.get_pos() // 1000) % 60
            total_time = self.current_track_length
            self.time_label.config(text=f"{current_time // 60:02}:{current_time % 60:02} / {total_time}")
        self.root.after(1000, self.update_time)

    def get_track_length(self):
        try:
            audio = File(self.playlist[self.current_index])
            length = audio.info.length
            return f"{int(length // 60):02}:{int(length % 60):02}"
        except:
            return "--:--"

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode:
            random.shuffle(self.playlist)
        else:
            self.playlist = self.original_playlist.copy()
        self.filter_tracks()

    def toggle_repeat(self):
        self.repeat_mode = not self.repeat_mode
        self.repeat_btn.config(bg=self.config.secondary_color if self.repeat_mode else self.config.button_color)

    def auto_scroll_track(self):
        if self.auto_scroll and mixer.music.get_busy():
            current_pos = mixer.music.get_pos() / 1000
            total_length = self.get_track_length_seconds()
            if current_pos >= total_length - 1:
                self.next_track()
        self.root.after(1000, self.auto_scroll_track)

    def get_track_length_seconds(self):
        try:
            audio = File(self.playlist[self.current_index])
            return audio.info.length
        except:
            return 0

    def highlight_current_track(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.config(bg=self.config.primary_color)
        current_widget = self.scrollable_frame.winfo_children()[self.current_index]
        current_widget.config(bg=self.config.secondary_color)
        self.canvas.yview_moveto(self.current_index / len(self.playlist))

    def show_notification(self, message):
        """Показывает уведомление, если они включены в конфигурации"""
        if self.config.notifications_enabled:
            self.toaster.show_toast("Оркестр", message, duration=3, threaded=True)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def setup_tray(self):
        menu = (
            pystray.MenuItem("Открыть", self.show_window),
            pystray.MenuItem("Следующий трек", self.next_track),
            pystray.MenuItem("Предыдущий трек", self.prev_track),
            pystray.MenuItem("Выход", self.quit_app)
        )
        
        image = Image.new("RGB", (64, 64), self.config.bg_color)
        self.tray_icon = pystray.Icon("Оркестр", image, "Оркестр", menu)
        
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self):
        """Открывает окно поверх всех окон и активирует его"""
        self.root.deiconify()  # Восстанавливаем окно
        self.root.lift()  # Поднимаем окно поверх всех других окон
        self.root.attributes('-topmost', True)  # Делаем окно поверх всех окон
        self.root.after(100, lambda: self.root.attributes('-topmost', False))  # Снимаем флаг через 100 мс

    def minimize_to_tray(self):
        """Сворачивает окно в трей"""
        self.root.withdraw()  # Скрываем окно

    def quit_app(self):
        self.tray_icon.stop()
        mixer.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayer(root)
    root.mainloop()