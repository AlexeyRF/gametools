import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import os
from pathlib import Path
import threading
class PixelArtConverter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pixel")
        self.root.geometry("600x500")
        self.input_path = None
        self.output_folder = None
        self.pixel_size = tk.IntVar(value=8)
        self.color_reduction = tk.IntVar(value=32)
        self.is_gif = False
        self.create_widgets()
    def create_widgets(self):
        control_frame = tk.Frame(self.root, padx=10, pady=10)
        control_frame.pack(fill=tk.X)
        tk.Button(control_frame, text="Выбрать файл",
                 command=self.select_file, width=15).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(control_frame, text="Выбрать папку",
                 command=self.select_folder, width=15).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(control_frame, text="Выбрать выходную папку",
                 command=self.select_output_folder, width=20).grid(row=0, column=2, padx=5, pady=5)
        param_frame = tk.LabelFrame(self.root, text="Параметры конвертации", padx=10, pady=10)
        param_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(param_frame, text="Размер пикселя:").grid(row=0, column=0, sticky=tk.W, pady=5)
        tk.Scale(param_frame, from_=4, to=32, variable=self.pixel_size,
                orient=tk.HORIZONTAL, length=200).grid(row=0, column=1, padx=10)
        tk.Label(param_frame, text="Уменьшение цветов:").grid(row=1, column=0, sticky=tk.W, pady=5)
        tk.Scale(param_frame, from_=2, to=256, variable=self.color_reduction,
                orient=tk.HORIZONTAL, length=200).grid(row=1, column=1, padx=10)
        self.convert_btn = tk.Button(self.root, text="Конвертировать",
                                    command=self.start_conversion,
                                    bg="green", fg="white", font=("Arial", 12),
                                    state=tk.DISABLED)
        self.convert_btn.pack(pady=20)
        self.info_label = tk.Label(self.root, text="Выберите файл или папку для конвертации",
                                  wraplength=550)
        self.info_label.pack(pady=10)
        self.progress = tk.Label(self.root, text="")
        self.progress.pack(pady=5)
    def select_file(self):
        filetypes = [
            ('Изображения', '*.png *.jpg *.jpeg *.bmp *.gif'),
            ('Все файлы', '*.*')
        ]
        filename = filedialog.askopenfilename(title="Выберите изображение", filetypes=filetypes)
        if filename:
            self.input_path = filename
            self.is_gif = filename.lower().endswith('.gif')
            self.update_info_label()
            self.convert_btn.config(state=tk.NORMAL)
    def select_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку с изображениями")
        if folder:
            self.input_path = folder
            self.is_gif = False
            self.update_info_label()
            self.convert_btn.config(state=tk.NORMAL)
    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if folder:
            self.output_folder = folder
    def update_info_label(self):
        if os.path.isdir(self.input_path):
            files = [f for f in os.listdir(self.input_path)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            info = f"Выбрана папка: {self.input_path}\nНайдено изображений: {len(files)}"
        else:
            info = f"Выбран файл: {os.path.basename(self.input_path)}"
            if self.is_gif:
                info += " (GIF - будет обработан каждый кадр)"
        self.info_label.config(text=info)
    def start_conversion(self):
        if not self.input_path:
            messagebox.showerror("Ошибка", "Сначала выберите файл или папку!")
            return
        if not self.output_folder:
            self.output_folder = os.path.join(os.path.dirname(self.input_path), "pixelart_output")
            os.makedirs(self.output_folder, exist_ok=True)
        self.convert_btn.config(state=tk.DISABLED, text="Конвертация...")
        self.progress.config(text="Начинаю конвертацию...")
        thread = threading.Thread(target=self.convert_images)
        thread.daemon = True
        thread.start()
    def convert_images(self):
        try:
            if os.path.isdir(self.input_path):
                self.process_folder()
            else:
                if self.is_gif:
                    self.process_gif()
                else:
                    self.process_single_image(self.input_path)
            self.root.after(0, self.conversion_complete)
        except Exception as e:
            self.root.after(0, lambda: self.conversion_error(str(e)))
    def process_folder(self):
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif']:
            image_files.extend(Path(self.input_path).glob(ext))
            image_files.extend(Path(self.input_path).glob(ext.upper()))
        total = len(image_files)
        for i, img_path in enumerate(image_files):
            self.root.after(0, lambda i=i:
                          self.progress.config(text=f"Обработка: {i+1}/{total}"))
            if str(img_path).lower().endswith('.gif'):
                self.process_gif(str(img_path))
            else:
                self.process_single_image(str(img_path))
    def process_single_image(self, image_path):
        try:
            img = Image.open(image_path)
            pixel_art = self.convert_to_pixelart(img)
            output_path = self.get_output_path(image_path, is_gif=False)
            pixel_art.save(output_path)
        except Exception as e:
            print(f"Ошибка обработки {image_path}: {e}")
    def process_gif(self, gif_path=None):
        if not gif_path:
            gif_path = self.input_path
        try:
            gif = Image.open(gif_path)
            frames = []
            total_frames = 0
            while True:
                total_frames += 1
                try:
                    gif.seek(total_frames)
                except EOFError:
                    break
            gif.seek(0)
            for frame_num in range(total_frames):
                gif.seek(frame_num)
                self.root.after(0, lambda fn=frame_num:
                              self.progress.config(text=f"Обработка GIF: кадр {fn+1}/{total_frames}"))
                frame = gif.copy()
                if frame.mode != 'RGBA':
                    frame = frame.convert('RGBA')
                pixel_frame = self.convert_to_pixelart(frame)
                frames.append(pixel_frame)
            output_path = self.get_output_path(gif_path, is_gif=True)
            frames[0].save(output_path, save_all=True,
                          append_images=frames[1:],
                          optimize=False,
                          duration=gif.info.get('duration', 100),
                          loop=gif.info.get('loop', 0))
        except Exception as e:
            print(f"Ошибка обработки GIF {gif_path}: {e}")
    def convert_to_pixelart(self, img):
        colors = self.color_reduction.get()
        if colors < 256:
            img = img.convert('P', palette=Image.ADAPTIVE, colors=colors)
            img = img.convert('RGBA')
        width, height = img.size
        pixel_size = self.pixel_size.get()
        new_width = (width // pixel_size) * pixel_size
        new_height = (height // pixel_size) * pixel_size
        if new_width == 0 or new_height == 0:
            new_width = max(pixel_size, width)
            new_height = max(pixel_size, height)
        img_small = img.resize((new_width // pixel_size, new_height // pixel_size),
                              Image.NEAREST)
        pixel_art = img_small.resize((new_width, new_height), Image.NEAREST)
        result = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        result.paste(pixel_art, (0, 0))
        return result
    def get_output_path(self, input_path, is_gif=False):
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_pixelart{ext}"
        counter = 1
        base_output_filename = output_filename
        while os.path.exists(os.path.join(self.output_folder, output_filename)):
            name, ext = os.path.splitext(base_output_filename)
            output_filename = f"{name}_{counter}{ext}"
            counter += 1
        return os.path.join(self.output_folder, output_filename)
    def conversion_complete(self):
        self.convert_btn.config(state=tk.NORMAL, text="Конвертировать")
        self.progress.config(text="Конвертация завершена!")
        messagebox.showinfo("Готово",
                          f"Конвертация завершена!\nРезультаты сохранены в:\n{self.output_folder}")
    def conversion_error(self, error_msg):
        self.convert_btn.config(state=tk.NORMAL, text="Конвертировать")
        self.progress.config(text="Ошибка!")
        messagebox.showerror("Ошибка", f"Произошла ошибка:\n{error_msg}")
    def run(self):
        self.root.mainloop()
if __name__ == "__main__":
    try:
        from PIL import Image
        app = PixelArtConverter()
        app.run()
    except ImportError as e:
        print("Необходимо установить библиотеки:")
        print("pip install Pillow numpy")
        input("Нажмите Enter для выхода...")
