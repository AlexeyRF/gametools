"""
Универсальный конвертер JSON в массив Python
Версия: 1.0.0
Автор: AI Assistant

Справка по использованию:
=======================

Базовое использование:
    from json_to_array import convert_json_to_array
    
    # Из строки
    result = convert_json_to_array('{"key": "value"}')
    
    # Из файла
    result = convert_json_from_file('data.json')

Параметры:
    - json_string: str - JSON строка для конвертации
    - file_path: str - путь к JSON файлу
    - force_array: bool - принудительно обернуть результат в массив (по умолчанию False)
    - recursive_convert: bool - рекурсивно конвертировать объекты в массивы (по умолчанию False)

Возвращаемое значение:
    - list - Python массив (список)

Исключения:
    - JSONConvertError - ошибка при конвертации JSON
    - FileOperationError - ошибка при работе с файлом

Примеры:
    # Пример 1: Конвертация JSON массива
    data = '["a", "b", "c"]'
    result = convert_json_to_array(data)  # ['a', 'b', 'c']
    
    # Пример 2: Конвертация JSON объекта (оборачивается в массив)
    data = '{"name": "John"}'
    result = convert_json_to_array(data, force_array=True)  # [{"name": "John"}]
    
    # Пример 3: Чтение из файла
    result = convert_json_from_file('/path/to/file.json')
    
    # Пример 4: Рекурсивная конвертация всех объектов в массивы
    data = '{"a": {"b": 1}}'
    result = convert_json_to_array(data, recursive_convert=True)  # [['a', ['b', 1]]]
"""

import json
from typing import Any, List, Union, Optional
from pathlib import Path


class JSONConvertError(Exception):
    """Исключение при ошибке конвертации JSON"""
    pass


class FileOperationError(Exception):
    """Исключение при ошибке работы с файлом"""
    pass


def _parse_json_constants(constant: str) -> Any:
    """
    Обработка специальных JSON констант
    
    Args:
        constant: JSON константа (NaN, Infinity, -Infinity)
        
    Returns:
        Соответствующее значение Python
    """
    if constant == 'NaN':
        return float('nan')
    elif constant == 'Infinity':
        return float('inf')
    elif constant == '-Infinity':
        return float('-inf')
    return constant


def _recursive_to_array(data: Any) -> Any:
    """
    Рекурсивное преобразование всех объектов в массивы
    
    Args:
        data: Данные для преобразования
        
    Returns:
        Преобразованные данные
    """
    if isinstance(data, dict):
        # Преобразуем словарь в массив пар [ключ, значение]
        return [[key, _recursive_to_array(value)] for key, value in data.items()]
    elif isinstance(data, list):
        return [_recursive_to_array(item) for item in data]
    else:
        return data


def convert_json_to_array(
    json_string: str, 
    force_array: bool = False, 
    recursive_convert: bool = False
) -> List[Any]:
    """
    Преобразует JSON строку в массив Python
    
    Args:
        json_string: JSON строка для конвертации
        force_array: Принудительно обернуть результат в массив, даже если это не массив
        recursive_convert: Рекурсивно конвертировать все объекты в массивы
        
    Returns:
        Python список (массив)
        
    Raises:
        JSONConvertError: При ошибке парсинга JSON
        
    Examples:
        >>> convert_json_to_array('[1, 2, 3]')
        [1, 2, 3]
        
        >>> convert_json_to_array('{"key": "value"}', force_array=True)
        [{'key': 'value'}]
        
        >>> convert_json_to_array('{"a": {"b": 1}}', recursive_convert=True)
        [['a', ['b', 1]]]
    """
    try:
        # Парсим JSON с полной поддержкой всех типов
        python_object = json.loads(
            json_string, 
            parse_constant=_parse_json_constants
        )
        
        # Рекурсивная конвертация объектов в массивы
        if recursive_convert:
            python_object = _recursive_to_array(python_object)
        
        # Принудительное оборачивание в массив если нужно
        if force_array or not isinstance(python_object, list):
            return [python_object]
        
        return python_object
        
    except json.JSONDecodeError as e:
        raise JSONConvertError(
            f"Ошибка парсинга JSON: {e.msg} (строка {e.lineno}, колонка {e.colno})"
        ) from e
    except Exception as e:
        raise JSONConvertError(f"Неожиданная ошибка при конвертации JSON: {str(e)}") from e


def convert_json_from_file(
    file_path: Union[str, Path], 
    force_array: bool = False, 
    recursive_convert: bool = False,
    encoding: str = 'utf-8'
) -> List[Any]:
    """
    Читает JSON из файла и преобразует в массив Python
    
    Args:
        file_path: Путь к JSON файлу
        force_array: Принудительно обернуть результат в массив
        recursive_convert: Рекурсивно конвертировать все объекты в массивы
        encoding: Кодировка файла (по умолчанию 'utf-8')
        
    Returns:
        Python список (массив)
        
    Raises:
        FileOperationError: При ошибке чтения файла
        JSONConvertError: При ошибке парсинга JSON
        
    Examples:
        >>> convert_json_from_file('data.json')
        [{'id': 1, 'name': 'Item'}]
        
        >>> convert_json_from_file('data.json', force_array=True)
        [{'id': 1, 'name': 'Item'}]
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileOperationError(f"Файл не найден: {file_path}")
        
        if not file_path.is_file():
            raise FileOperationError(f"Путь не является файлом: {file_path}")
        
        with open(file_path, 'r', encoding=encoding) as file:
            json_string = file.read()
            
        return convert_json_to_array(json_string, force_array, recursive_convert)
        
    except FileOperationError:
        raise
    except JSONConvertError:
        raise
    except PermissionError as e:
        raise FileOperationError(f"Нет прав на чтение файла {file_path}: {str(e)}") from e
    except Exception as e:
        raise FileOperationError(f"Ошибка при чтении файла {file_path}: {str(e)}") from e


def is_valid_json(json_string: str) -> bool:
    """
    Проверяет, является ли строка валидным JSON
    
    Args:
        json_string: Строка для проверки
        
    Returns:
        True если JSON валидный, иначе False
    """
    try:
        json.loads(json_string)
        return True
    except json.JSONDecodeError:
        return False


def get_json_type(json_string: str) -> str:
    """
    Определяет тип JSON структуры
    
    Args:
        json_string: JSON строка
        
    Returns:
        Тип структуры: 'array', 'object', 'value' или 'invalid'
    """
    try:
        data = json.loads(json_string)
        if isinstance(data, list):
            return 'array'
        elif isinstance(data, dict):
            return 'object'
        else:
            return 'value'
    except json.JSONDecodeError:
        return 'invalid'


# Интерфейс для простого использования
class JSONToArray:
    """
    Класс для удобной работы с конвертацией JSON в массив
    
    Attributes:
        data: Исходные данные (строка или файл)
        force_array: Принудительно обернуть в массив
        recursive: Рекурсивная конвертация
        
    Examples:
        >>> converter = JSONToArray('{"name": "John"}', force_array=True)
        >>> result = converter.convert()
        >>> print(result)  # [{'name': 'John'}]
        
        >>> converter = JSONToArray.from_file('data.json')
        >>> result = converter.convert()
    """
    
    def __init__(self, json_string: str, force_array: bool = False, recursive: bool = False):
        """
        Инициализация конвертера
        
        Args:
            json_string: JSON строка
            force_array: Принудительно обернуть в массив
            recursive: Рекурсивная конвертация
        """
        self.json_string = json_string
        self.force_array = force_array
        self.recursive = recursive
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path], force_array: bool = False, recursive: bool = False):
        """
        Создание конвертера из файла
        
        Args:
            file_path: Путь к файлу
            force_array: Принудительно обернуть в массив
            recursive: Рекурсивная конвертация
            
        Returns:
            Экземпляр JSONToArray
        """
        instance = cls("", force_array, recursive)
        instance.file_path = file_path
        return instance
    
    def convert(self) -> List[Any]:
        """
        Выполняет конвертацию
        
        Returns:
            Массив Python
        """
        if hasattr(self, 'file_path'):
            return convert_json_from_file(self.file_path, self.force_array, self.recursive)
        else:
            return convert_json_to_array(self.json_string, self.force_array, self.recursive)


def main():
    import sys
    
    if len(sys.argv) > 1:
        # Если передан аргумент командной строки - пробуем прочитать файл
        try:
            result = convert_json_from_file(sys.argv[1])
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except (FileOperationError, JSONConvertError) as e:
            print(f"Ошибка: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Команды:")
        print("  - Введите JSON строку для конвертации")
        print("  - 'file:путь_к_файлу' - загрузить из файла")
        print("  - 'exit' - выход")
        
        while True:
            try:
                user_input = input("\nВвод> ").strip()
                
                if user_input.lower() == 'exit':
                    break
                
                if user_input.lower().startswith('file:'):
                    file_path = user_input[5:].strip()
                    result = convert_json_from_file(file_path)
                else:
                    result = convert_json_to_array(user_input, force_array=True)
                
                print("\nРезультат:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                print(f"\nТип: {type(result)}")
                print(f"Длина: {len(result)}")
                
            except (JSONConvertError, FileOperationError) as e:
                print(f"Ошибка: {e}")
            except KeyboardInterrupt:
                print("\nВыход...")
                break
            except Exception as e:
                print(f"Неизвестная ошибка: {e}")


if __name__ == "__main__":
    main()