import yaml
import sys
import os

def load_config(path="config.yaml"):
    if not os.path.exists(path):
        print(f"Ошибка: файл конфигурации '{path}' не найден.")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Ошибка: некорректный YAML-файл.\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при чтении файла конфигурации: {e}")
        sys.exit(1)

    if not isinstance(config, dict):
        print("Ошибка: конфигурация должна быть словарём.")
        sys.exit(1)

    required = [
        "package_name",
        "repository_url",
        "test_mode",
        "package_version",
        "ascii_tree",
        "filter_substring"
    ]

    for key in required:
        if key not in config:
            print(f"Ошибка: отсутствует обязательный параметр '{key}'.")
            sys.exit(1)

    return config

def main():
    config = load_config()

    print("Параметры конфигурации:")
    for key, value in config.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
