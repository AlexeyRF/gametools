import sys
import os
from PIL import Image, ImageEnhance
import numpy as np

def process_image(input_path):
    # Открываем изображение
    img = Image.open(input_path).convert('L')  # сразу в ч/б

    # Повышаем контрастность
    enhancer = ImageEnhance.Contrast(img)
    img_high_contrast = enhancer.enhance(1.8)  # коэффициент можно менять

    # Сохраняем результат
    base, ext = os.path.splitext(input_path)
    output_path = f"{base}_processed{ext}"
    img_high_contrast.save(output_path)
    print(f"Сохранено: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Перетащите изображение на иконку программы.")
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.isfile(input_path):
        print("Файл не найден.")
        sys.exit(1)

    process_image(input_path)