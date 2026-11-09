import yaml
import sys
import os

# Ожидаемые типы для каждого параметра (Вариант 2)
EXPECTED_TYPES = {
    "package_name": str,
    "repository_url": str,
    "test_mode": bool,
    "package_version": str,
    "ascii_tree": bool,
    "filter_substring": str,
}

def load_config(path="config.yaml"):
    # 1. Проверка существования файла
    if not os.path.exists(path):
        print(f"Ошибка: файл конфигурации '{path}' не найден.")
        sys.exit(1)

    # 2. Проверка валидности YAML
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Ошибка: некорректный YAML-файл.\n{e}")
        sys.exit(1)

    # 3. Проверка, что YAML — это словарь
    if not isinstance(config, dict):
        print("Ошибка: конфигурация должна быть словарём.")
        sys.exit(1)

    # 4. Проверка наличия всех параметров
    for key in EXPECTED_TYPES:
        if key not in config:
            print(f"Ошибка: отсутствует обязательный параметр '{key}'.")
            sys.exit(1)

    # 5. Проверка типов и пустых строк
    for key, expected_type in EXPECTED_TYPES.items():
        value = config[key]
        if not isinstance(value, expected_type):
            print(f"Ошибка: параметр '{key}' должен быть {expected_type.__name__}, получен {type(value).__name__}.")
            sys.exit(1)
        if expected_type is str and value.strip() == "":
            print(f"Ошибка: параметр '{key}' не должен быть пустой строкой.")
            sys.exit(1)

    return config

def main():
    config = load_config()
    print("Параметры конфигурации:")
    for key, value in config.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
