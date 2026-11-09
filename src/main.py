import yaml
import sys
import os
import requests

EXPECTED_TYPES = {
    "package_name": str,
    "repository_url": str,
    "test_mode": bool,
    "package_version": str,
    "ascii_tree": bool,
    "filter_substring": str,
}

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
    if not isinstance(config, dict):
        print("Ошибка: конфигурация должна быть словарём.")
        sys.exit(1)
    for key in EXPECTED_TYPES:
        if key not in config:
            print(f"Ошибка: отсутствует параметр '{key}'.")
            sys.exit(1)
    for key, expected_type in EXPECTED_TYPES.items():
        value = config[key]
        if not isinstance(value, expected_type):
            print(f"Ошибка: параметр '{key}' должен быть {expected_type.__name__}, получен {type(value).__name__}.")
            sys.exit(1)
        if expected_type is str and value.strip() == "":
            print(f"Ошибка: параметр '{key}' не должен быть пустым.")
            sys.exit(1)
    return config

def get_packages_data(config):
    """Загружает текст файла Packages из репозитория или локального файла."""
    url = config["repository_url"]
    if config["test_mode"]:
        # Режим тестирования: читаем локальный файл
        if not os.path.exists(url):
            print(f"Ошибка: тестовый файл '{url}' не найден.")
            sys.exit(1)
        with open(url, "r", encoding="utf-8") as f:
            return f.read()
    else:
        # Реальный режим: скачиваем по URL
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Ошибка при скачивании репозитория: {e}")
            sys.exit(1)

def parse_dependencies(packages_text, target_package, target_version):
    """Ищет пакет с нужной версией и возвращает список его прямых зависимостей."""
    # Файл Packages состоит из блоков, разделённых пустой строкой
    blocks = packages_text.strip().split("\n\n")
    
    for block in blocks:
        lines = block.strip().split("\n")
        pkg_name = None
        pkg_version = None
        depends_line = None
        
        for line in lines:
            if line.startswith("Package: "):
                pkg_name = line.replace("Package: ", "").strip()
            elif line.startswith("Version: "):
                pkg_version = line.replace("Version: ", "").strip()
            elif line.startswith("Depends: "):
                depends_line = line.replace("Depends: ", "").strip()
        
        # Если нашли нужный пакет и версию
        if pkg_name == target_package and pkg_version == target_version:
            if not depends_line:
                return []
            
            # Разбиваем строку зависимостей по запятым
            deps = []
            for dep in depends_line.split(","):
                dep = dep.strip()
                # Убираем версии в скобках, например "libc6 (>= 2.14)" -> "libc6"
                if "(" in dep:
                    dep = dep.split("(")[0].strip()
                # Убираем альтернативы, например "foo | bar" -> берём "foo"
                if "|" in dep:
                    dep = dep.split("|")[0].strip()
                if dep:
                    deps.append(dep)
            return deps
    
    print(f"Ошибка: пакет '{target_package}' версии '{target_version}' не найден.")
    sys.exit(1)

def main():
    config = load_config()
    print("Параметры конфигурации:")
    for key, value in config.items():
        print(f"{key}: {value}")
    
    print("\n--- Этап 2: Сбор данных ---")
    packages_text = get_packages_data(config)
    deps = parse_dependencies(packages_text, config["package_name"], config["package_version"])
    
    print(f"Прямые зависимости пакета {config['package_name']} (версия {config['package_version']}):")
    if not deps:
        print("  (нет зависимостей)")
    else:
        for dep in deps:
            print(f"  - {dep}")

if __name__ == "__main__":
    main()
