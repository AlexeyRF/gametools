import os
import random
import configparser
import json
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        self.playlists_file = 'playlists.json'
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            self.create_default_config()
        
        self.config.read(self.config_file)
        self.music_folder = self.config.get('Settings', 'music_folder', 
                          fallback=os.path.join(os.path.expanduser("~"), "Music"))
        self.scan_subdirs = self.config.getboolean('Settings', 'scan_subdirs', fallback=True)
        
        # Цвета
        self.bg_color = self.config.get('Colors', 'background', fallback='#0a1a2f')
        self.primary_color = self.config.get('Colors', 'primary', fallback='#1a2f4f')
        self.secondary_color = self.config.get('Colors', 'secondary', fallback='#2a4f7f')
        self.text_color = self.config.get('Colors', 'text', fallback='white')
        self.button_color = self.config.get('Colors', 'button', fallback='#3a6faf')

    def create_default_config(self):
        self.config['Settings'] = {
            'music_folder': os.path.join(os.path.expanduser("~"), "Music"),
            'scan_subdirs': 'True'
        }
        self.config['Colors'] = {
            'background': '#0a1a2f',
            'primary': '#1a2f4f',
            'secondary': '#2a4f7f',
            'text': 'white',
            'button': '#3a6faf'
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def save_settings(self):
        self.config.set('Settings', 'music_folder', self.music_folder)
        self.config.set('Settings', 'scan_subdirs', str(self.scan_subdirs))
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)

class MusicPlayer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.config = Config()
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        self.playlists = {"Все треки": []} 
        self.current_base_playlist = []    
        self.active_playlist = []        
        
        self.current_index = -1
        self.shuffle_mode = False
        self.repeat_mode = False

        self.setup_ui()
        self.load_playlists_from_file()
        self.scan_folder()

        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.player.mediaStatusChanged.connect(self.media_status_changed)

    def setup_ui(self):
        self.setWindowTitle("Оркестр")
        self.setFixedSize(450, 750)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(f"background-color: {self.config.bg_color}; color: {self.config.text_color};")

        layout = QtWidgets.QVBoxLayout(self)

        title_bar = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("Оркестр")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        close_btn = QtWidgets.QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(QtWidgets.QApplication.instance().quit)
        close_btn.setStyleSheet(f"background: {self.config.primary_color}; border: none; border-radius: 5px;")

        title_bar.addWidget(title_label)
        title_bar.addStretch()
        title_bar.addWidget(close_btn)
        layout.addLayout(title_bar)

        folder_layout = QtWidgets.QHBoxLayout()
        self.folder_input = QtWidgets.QLineEdit(self.config.music_folder)
        self.folder_input.setReadOnly(True)
        self.folder_input.setStyleSheet(f"background: {self.config.primary_color}; border: none; padding: 5px;")
        
        browse_btn = QtWidgets.QPushButton("📁")
        browse_btn.setFixedSize(30, 30)
        browse_btn.setStyleSheet(f"background: {self.config.button_color}; border-radius: 5px;")
        browse_btn.clicked.connect(self.choose_folder)
        
        self.subdirs_check = QtWidgets.QCheckBox("Подпапки")
        self.subdirs_check.setChecked(self.config.scan_subdirs)
        self.subdirs_check.stateChanged.connect(self.toggle_subdirs)

        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(browse_btn)
        folder_layout.addWidget(self.subdirs_check)
        layout.addLayout(folder_layout)

        playlist_layout = QtWidgets.QHBoxLayout()
        self.playlist_combo = QtWidgets.QComboBox()
        self.playlist_combo.setStyleSheet(f"background: {self.config.primary_color}; border: none; padding: 5px;")
        self.playlist_combo.currentTextChanged.connect(self.switch_playlist)
        
        save_pl_btn = QtWidgets.QPushButton("💾 Сохранить список")
        save_pl_btn.setStyleSheet(f"background: {self.config.button_color}; border-radius: 5px; padding: 5px;")
        save_pl_btn.clicked.connect(self.save_current_as_playlist)

        playlist_layout.addWidget(self.playlist_combo)
        playlist_layout.addWidget(save_pl_btn)
        layout.addLayout(playlist_layout)

        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Поиск (создает активный плейлист)...")
        self.search_input.textChanged.connect(self.filter_tracks)
        self.search_input.setStyleSheet(f"background: {self.config.secondary_color}; border: none; padding: 8px; border-radius: 5px;")
        layout.addWidget(self.search_input)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")
        self.track_list_widget = QtWidgets.QWidget()
        self.track_list_layout = QtWidgets.QVBoxLayout(self.track_list_widget)
        self.track_list_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.track_list_widget)
        layout.addWidget(self.scroll_area)

        controls = QtWidgets.QVBoxLayout()
        
        seek_layout = QtWidgets.QHBoxLayout()
        self.time_current = QtWidgets.QLabel("00:00")
        self.seek_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.seek_slider.setStyleSheet(f"QSlider::groove:horizontal {{ background: {self.config.primary_color}; height: 8px; border-radius: 4px; }}"
                                       f"QSlider::handle:horizontal {{ background: {self.config.button_color}; width: 14px; margin: -3px 0; border-radius: 7px; }}")
        self.seek_slider.sliderMoved.connect(self.set_position)
        self.time_total = QtWidgets.QLabel("00:00")
        
        seek_layout.addWidget(self.time_current)
        seek_layout.addWidget(self.seek_slider)
        seek_layout.addWidget(self.time_total)
        controls.addLayout(seek_layout)

        btns_layout = QtWidgets.QHBoxLayout()
        
        self.repeat_btn = QtWidgets.QPushButton("🔁")
        self.shuffle_btn = QtWidgets.QPushButton("🔀")
        self.prev_btn = QtWidgets.QPushButton("⏮")
        self.play_btn = QtWidgets.QPushButton("▶")
        self.next_btn = QtWidgets.QPushButton("⏭")

        for btn in [self.repeat_btn, self.shuffle_btn, self.prev_btn, self.play_btn, self.next_btn]:
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(f"background: {self.config.button_color}; border-radius: 20px; font-size: 16px;")
            btns_layout.addWidget(btn)

        self.play_btn.clicked.connect(self.toggle_play)
        self.next_btn.clicked.connect(self.next_track)
        self.prev_btn.clicked.connect(self.prev_track)
        self.shuffle_btn.clicked.connect(self.toggle_shuffle)
        self.repeat_btn.clicked.connect(self.toggle_repeat)

        btns_layout.addStretch()

        vol_label = QtWidgets.QLabel("🔊")
        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.audio_output.setVolume(0.5)

        btns_layout.addWidget(vol_label)
        btns_layout.addWidget(self.volume_slider)

        controls.addLayout(btns_layout)
        layout.addLayout(controls)

    def choose_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Выберите папку с музыкой/видео", self.config.music_folder)
        if folder:
            self.config.music_folder = folder
            self.folder_input.setText(folder)
            self.config.save_settings()
            self.scan_folder()

    def toggle_subdirs(self, state):
        self.config.scan_subdirs = bool(state)
        self.config.save_settings()
        self.scan_folder()

    def scan_folder(self):
        valid_exts = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".mp4", ".mkv", ".avi", ".mov", ".webm")
        scanned_tracks = []
        
        folder = self.config.music_folder
        if os.path.exists(folder):
            if self.config.scan_subdirs:
                for root, _, files in os.walk(folder):
                    for file in files:
                        if file.lower().endswith(valid_exts):
                            scanned_tracks.append(os.path.join(root, file))
            else:
                try:
                    for file in os.listdir(folder):
                        path = os.path.join(folder, file)
                        if os.path.isfile(path) and file.lower().endswith(valid_exts):
                            scanned_tracks.append(path)
                except Exception as e:
                    pass

        self.playlists["Все треки"] = scanned_tracks
        
        if self.playlist_combo.count() == 0:
            self.update_playlist_combo()
        else:
            self.playlist_combo.setCurrentText("Все треки")
            self.switch_playlist("Все треки")

    def load_playlists_from_file(self):
        if os.path.exists(self.config.playlists_file):
            try:
                with open(self.config.playlists_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.playlists[k] = v
            except:
                pass
        self.update_playlist_combo()

    def save_playlists_to_file(self):
        to_save = {k: v for k, v in self.playlists.items() if k != "Все треки"}
        with open(self.config.playlists_file, 'w', encoding='utf-8') as f:
            json.dump(to_save, f, ensure_ascii=False, indent=4)

    def update_playlist_combo(self):
        self.playlist_combo.blockSignals(True)
        self.playlist_combo.clear()
        self.playlist_combo.addItems(self.playlists.keys())
        self.playlist_combo.blockSignals(False)

    def save_current_as_playlist(self):
        if not self.active_playlist:
            return
        name, ok = QtWidgets.QInputDialog.getText(self, "Новый плейлист", "Введите название плейлиста:")
        if ok and name:
            self.playlists[name] = self.active_playlist.copy()
            self.save_playlists_to_file()
            self.update_playlist_combo()
            self.playlist_combo.setCurrentText(name)

    def switch_playlist(self, name):
        if name in self.playlists:
            self.current_base_playlist = self.playlists[name].copy()
            self.search_input.clear()
            self.filter_tracks() 

    def filter_tracks(self):
        query = self.search_input.text().lower()
        if not query:
            self.active_playlist = self.current_base_playlist.copy()
        else:
            self.active_playlist = [p for p in self.current_base_playlist if query in os.path.basename(p).lower()]
        
        if self.shuffle_mode:
            random.shuffle(self.active_playlist)
            
        self.refresh_track_list()

    def refresh_track_list(self):
        for i in reversed(range(self.track_list_layout.count())): 
            self.track_list_layout.itemAt(i).widget().setParent(None)

        for idx, path in enumerate(self.active_playlist):
            self.create_track_item(path, idx)
            
        self.highlight_current()

    def create_track_item(self, path, index):
        frame = QtWidgets.QFrame()
        frame.setStyleSheet(f"background: {self.config.primary_color}; border-radius: 3px;")
        item_layout = QtWidgets.QHBoxLayout(frame)
        item_layout.setContentsMargins(5, 5, 5, 5)
        
        name = os.path.basename(path)
        label = QtWidgets.QLabel(name if len(name) < 45 else f"{name[:42]}...")
        
        play_btn = QtWidgets.QPushButton("▶")
        play_btn.setFixedSize(25, 25)
        play_btn.clicked.connect(lambda: self.play_index(index))
        play_btn.setStyleSheet(f"background: {self.config.button_color}; border-radius: 12px;")

        item_layout.addWidget(play_btn)
        item_layout.addWidget(label)
        self.track_list_layout.addWidget(frame)

    def play_index(self, index):
        if 0 <= index < len(self.active_playlist):
            self.current_index = index
            self.play_track()

    def play_track(self):
        if not self.active_playlist or self.current_index < 0 or self.current_index >= len(self.active_playlist): 
            return
            
        path = self.active_playlist[self.current_index]
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        self.play_btn.setText("⏸")
        self.highlight_current()

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶")
        else:
            if self.player.source().isEmpty() and self.active_playlist:
                self.play_index(0)
            else:
                self.player.play()
                self.play_btn.setText("⏸")

    def next_track(self):
        if not self.active_playlist: return
        if not self.repeat_mode:
            self.current_index = (self.current_index + 1) % len(self.active_playlist)
        self.play_track()

    def prev_track(self):
        if not self.active_playlist: return
        self.current_index = (self.current_index - 1) % len(self.active_playlist)
        self.play_track()

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        self.filter_tracks() 
        color = self.config.secondary_color if self.shuffle_mode else self.config.button_color
        self.shuffle_btn.setStyleSheet(f"background: {color}; border-radius: 20px; font-size: 16px;")

    def toggle_repeat(self):
        self.repeat_mode = not self.repeat_mode
        color = self.config.secondary_color if self.repeat_mode else self.config.button_color
        self.repeat_btn.setStyleSheet(f"background: {color}; border-radius: 20px; font-size: 16px;")

    def set_volume(self, val):
        self.audio_output.setVolume(val / 100.0)

      def update_duration(self, duration):
        self.seek_slider.setRange(0, duration)
        tm, ts = divmod(duration // 1000, 60)
        self.time_total.setText(f"{tm:02}:{ts:02}")

    def update_position(self, position):
        self.seek_slider.blockSignals(True)
        self.seek_slider.setValue(position)
        self.seek_slider.blockSignals(False)
        m, s = divmod(position // 1000, 60)
        self.time_current.setText(f"{m:02}:{s:02}")

    def set_position(self, position):
        self.player.setPosition(position)

    def media_status_changed(self, status):
        
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.next_track()

    def highlight_current(self):
        for i in range(self.track_list_layout.count()):
            widget = self.track_list_layout.itemAt(i).widget()
            if widget:
                color = self.config.secondary_color if i == self.current_index else self.config.primary_color
                widget.setStyleSheet(f"background: {color}; border-radius: 3px;")

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'old_pos'):
            delta = QtCore.QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    player = MusicPlayer()
    player.show()
    app.exec()