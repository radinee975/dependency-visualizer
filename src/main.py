import yaml
import sys
import os
import requests
import argparse
import gzip
import io

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
        print(f"Error: config file {path} not found.")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error: invalid YAML file.\n{e}")
        sys.exit(1)

    if not isinstance(config, dict):
        print("Error: config must be a dictionary.")
        sys.exit(1)

    for key, expected in EXPECTED_TYPES.items():
        if key not in config:
            print(f"Error: missing parameter {key}.")
            sys.exit(1)

        value = config[key]
        if not isinstance(value, expected):
            type_name = expected.__name__
            print(f"Error: {key} must be {type_name}.")
            sys.exit(1)

        # Пустую строку разрешаем только для filter_substring
        if expected is str and value.strip() == "" and key != "filter_substring":
            print(f"Error: {key} cannot be empty.")
            sys.exit(1)

    return config

def get_packages_data(config):
    url = config["repository_url"]

    if config["test_mode"]:
        if not os.path.exists(url):
            print(f"Error: test file {url} not found.")
            sys.exit(1)
        with open(url, "r", encoding="utf-8") as f:
            return f.read()

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        if url.endswith(".gz"):
            with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
                return gz.read().decode("utf-8", errors="replace")
        else:
            return response.text

    except Exception as e:
        print(f"Error downloading: {e}")
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
                pkg_name = line[9:].strip()
            elif line.startswith("Version: "):
                pkg_version = line[9:].strip()
            elif line.startswith("Depends: "):
                depends_line = line[9:].strip()

        if not pkg_name:
            continue

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
            "depends": deps,
        }

    return packages

def build_graph(packages, target, filter_sub, visited=None, graph=None):
    if visited is None:
        visited = set()
    if graph is None:
        graph = {}

    if target in visited:
        return graph

    visited.add(target)

    if target not in packages:
        return graph

    deps = packages[target]["depends"]
    filtered = [d for d in deps if not (filter_sub and filter_sub in d)]
    graph[target] = filtered

    for dep in filtered:
        build_graph(packages, dep, filter_sub, visited, graph)

    return graph

def find_reverse(packages, target, filter_sub):
    rev_graph = {}

    for pkg, data in packages.items():
        for dep in data["depends"]:
            if filter_sub and filter_sub in dep:
                continue
            rev_graph.setdefault(dep, []).append(pkg)

    result = set()
    visited = set()

    def dfs(node):
        if node in visited:
            return
        visited.add(node)
        for parent in rev_graph.get(node, []):
            result.add(parent)
            dfs(parent)

    dfs(target)
    return sorted(result)

def generate_plantuml(graph):
    lines = ["@startuml", "skinparam linetype ortho"]

    for pkg, deps in graph.items():
        if not deps:
            lines.append(f"[{pkg}]")
        for dep in deps:
            lines.append(f"[{pkg}] --> [{dep}]")

    lines.append("@enduml")
    return "\n".join(lines)

def print_tree(packages, pkg, filter_sub, prefix="", is_last=True, visited=None):
    if visited is None:
        visited = set()

    connector = "\\-- " if is_last else "|-- "

    if pkg in visited:
        print(f"{prefix}{connector}{pkg} (cycle)")
        return

    visited.add(pkg)

    if pkg not in packages:
        print(f"{prefix}{connector}{pkg} (not found)")
        return

    if prefix:
        print(f"{prefix}{connector}{pkg}")
    else:
        print(pkg)

    deps = [d for d in packages[pkg]["depends"] if not (filter_sub and filter_sub in d)]

    for i, dep in enumerate(deps):
        is_last_child = i == len(deps) - 1
        new_prefix = prefix + ("    " if is_last else "|   ")
        print_tree(packages, dep, filter_sub, new_prefix, is_last_child, visited)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=int)
    args = parser.parse_args()

    config = load_config()

    if args.stage == 1 or not args.stage:
        print("--- STAGE 1: Configuration ---")
        for key, value in config.items():
            print(f"  {key}: {value}")
        if args.stage == 1:
            return

    text = get_packages_data(config)
    packages = parse_packages(text)
    target = config["package_name"]

    if args.stage == 2 or not args.stage:
        print("\n--- STAGE 2: Data Collection ---")
        if target not in packages:
            print(f"Error: package {target} not found.")
            sys.exit(1)
        deps = packages[target]["depends"]
        print(f"Direct dependencies: {deps}")
        if args.stage == 2:
            return

    if args.stage == 3 or not args.stage:
        print("\n--- STAGE 3: Dependency Graph ---")
        graph = build_graph(packages, target, config["filter_substring"])
        for key, value in graph.items():
            print(f"  {key} -> {value}")
        if args.stage == 3:
            return

    if args.stage == 4 or not args.stage:
        print("\n--- STAGE 4: Reverse Dependencies ---")
        rev = find_reverse(packages, target, config["filter_substring"])
        if rev:
            print(f"Depends on {target}: {rev}")
        else:
            print(f"Depends on {target}: none")
        if args.stage == 4:
            return

    if args.stage == 5 or not args.stage:
        print("\n--- STAGE 5: Visualization ---")
        graph = build_graph(packages, target, config["filter_substring"])
        print("PlantUML code:")
        print(generate_plantuml(graph))

        if config["ascii_tree"]:
            print("\nASCII tree:")
            print_tree(packages, target, config["filter_substring"])

if __name__ == "__main__":
    main()