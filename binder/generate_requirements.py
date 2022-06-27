import argparse
from pathlib import Path
from typing import Any, Dict

import toml


# Based on: https://github.com/jla524/requirements/blob/main/src/convert.py
def retrieve_packages(toml_content: Dict[str, Any]) -> Dict[str, str]:
    packages = dict(toml_content["tool"]["poetry"]["dependencies"])
    packages.pop("python", None)
    return packages


def retrieve_python_version(toml_content: Dict[str, Any]) -> str:
    version = toml_content["tool"]["poetry"]["dependencies"]["python"].strip("~^")
    return f"python-{version}"


def to_package(name: str, version: str) -> str:
    # version can be a DynamicInlineTableDict
    if not isinstance(version, str):
        version = version["version"]

    return f"{name}=={version.strip('^~')}"


header = """# Auto-generated with generate_requirements.py
# This file is required for binder and is automatically synced with pyproject.toml
# It should *not* be adjusted by hand
"""


def generate_requirements_content(packages: Dict[str, str]) -> str:
    body = "\n".join((to_package(name, version) for name, version in packages.items()))
    return header + body


def generate(toml_path: Path, requirements_path: Path, runtime_path: Path) -> None:
    with toml_path.open("r") as f:
        content = toml.load(f)

    packages = retrieve_packages(content)
    requirements = generate_requirements_content(packages)

    with requirements_path.open("w") as f:
        f.write(requirements)

    python_version = retrieve_python_version(content)

    with runtime_path.open("w") as f:
        f.write(python_version)


def parse_args():
    """Parses and returns the arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("toml_path", help="Path to the toml source file.")
    parser.add_argument("requirements_path", help="Path to the requirements.txt file.")
    parser.add_argument("runtime_path", help="Path to the runtime.txt file.")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    toml_path = Path(args.toml_path)
    requirements_path = Path(args.requirements_path)
    runtime_path = Path(args.runtime_path)

    generate(toml_path, requirements_path, runtime_path)
