import re
import sys
import os
def process_file(file_path): 
    pattern = r"^\s*\d+\s"
    try:
        with open(file_path, 'r', encoding='utf-8') as f: lines = f.readlines()
        cleaned_lines = []
        for line in lines:
            new_line = re.sub(pattern, "", line)
            cleaned_lines.append(new_line)
        base, ext = os.path.splitext(file_path)
        output_path = f"{base}_cleaned{ext}"
        with open(output_path, 'w', encoding='utf-8') as f: f.writelines(cleaned_lines)
        print(f"Успешно обработан: {os.path.basename(file_path)}")
        print(f"Результат сохранен в: {os.path.basename(output_path)}")
    except Exception as e: print(f"Ошибка при обработке файла {file_path}: {e}")
if __name__ == "__main__":
    files = sys.argv[1:]
    if not files:
        print("Инструкция: Перетащите один или несколько текстовых файлов на иконку этого скрипта.")
        input("Нажмите Enter, чтобы выйти...")
    else:
        for file in files:
            if os.path.isfile(file):process_file(file)
            else:print(f"Объект {file} не является файлом.")
