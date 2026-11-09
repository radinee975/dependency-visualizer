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
        print(f"Ошибка: файл конфигурации {path} не найден.")
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
            print(f"Ошибка: отсутствует параметр {key}.")
            sys.exit(1)
    for key, expected_type in EXPECTED_TYPES.items():
        value = config[key]
        if not isinstance(value, expected_type):
            print(f"Ошибка: параметр {key} должен быть {expected_type.__name__}, получен {type(value).__name__}.")
            sys.exit(1)
        if expected_type is str and value.strip() == "":
            print(f"Ошибка: параметр {key} не должен быть пустым.")
            sys.exit(1)
    return config

def get_packages_data(config):
    url = config["repository_url"]
    if config["test_mode"]:
        if not os.path.exists(url):
            print(f"Ошибка: тестовый файл {url} не найден.")
            sys.exit(1)
        with open(url, "r", encoding="utf-8") as f:
            return f.read()
    else:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Ошибка при скачивании репозитория: {e}")
            sys.exit(1)

def parse_packages(packages_text):
    packages = {}
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
        
        if pkg_name:
            deps = []
            if depends_line:
                for dep in depends_line.split(","):
                    dep = dep.strip()
                    if "(" in dep:
                        dep = dep.split("(")[0].strip()
                    if "|" in dep:
                        dep = dep.split("|")[0].strip()
                    if dep:
                        deps.append(dep)
            packages[pkg_name] = {
                "version": pkg_version,
                "depends": deps
            }
    return packages

def build_dependency_graph(packages, package_name, filter_substring, visited=None, graph=None):
    if visited is None:
        visited = set()
    if graph is None:
        graph = {}
    
    if package_name in visited:
        return graph
    
    visited.add(package_name)
    
    if package_name not in packages:
        return graph
    
    deps = packages[package_name]["depends"]
    
    filtered_deps = []
    for dep in deps:
        if filter_substring and filter_substring in dep:
            continue
        filtered_deps.append(dep)
    
    graph[package_name] = filtered_deps
    
    for dep in filtered_deps:
        build_dependency_graph(packages, dep, filter_substring, visited, graph)
    
    return graph

def find_reverse_dependencies(packages, target_package, filter_substring):
    """Находит все пакеты, которые зависят от target_package (прямо или косвенно)."""
    reverse_graph = {}
    
    # Строим обратный граф: для каждого пакета находим, кто на него ссылается
    for pkg_name, pkg_data in packages.items():
        deps = pkg_data["depends"]
        for dep in deps:
            if filter_substring and filter_substring in dep:
                continue
            if dep not in reverse_graph:
                reverse_graph[dep] = []
            reverse_graph[dep].append(pkg_name)
    
    # Теперь рекурсивно ищем все пакеты, которые зависят от target_package
    result = set()
    visited = set()
    
    def dfs(node):
        if node in visited:
            return
        visited.add(node)
        for parent in reverse_graph.get(node, []):
            result.add(parent)
            dfs(parent)
    
    dfs(target_package)
    return sorted(result)

def main():
    config = load_config()
    print("Параметры конфигурации:")
    for key, value in config.items():
        print(f"{key}: {value}")
    
    print("\n--- Этап 2: Сбор данных ---")
    packages_text = get_packages_data(config)
    packages = parse_packages(packages_text)
    
    target = config["package_name"]
    if target not in packages:
        print(f"Ошибка: пакет {target} не найден в репозитории.")
        sys.exit(1)
    
    print(f"Прямые зависимости пакета {target}:")
    for dep in packages[target]["depends"]:
        print(f"  - {dep}")
    
    print("\n--- Этап 3: Построение графа зависимостей (DFS) ---")
    graph = build_dependency_graph(
        packages,
        target,
        config["filter_substring"]
    )
    
    print("Граф зависимостей:")
    for pkg, deps in graph.items():
        deps_str = ", ".join(deps) if deps else "(нет)"
        print(f"  {pkg} -> {deps_str}")
    
    print("\n--- Этап 4: Обратные зависимости ---")
    reverse_deps = find_reverse_dependencies(packages, target, config["filter_substring"])
    if not reverse_deps:
        print(f"Пакеты, зависящие от {target}: (нет)")
    else:
        print(f"Пакеты, зависящие от {target}:")
        for pkg in reverse_deps:
            print(f"  - {pkg}")

if __name__ == "__main__":
    main()
