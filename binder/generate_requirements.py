import argparse
from pathlib import Path
from typing import Any, Dict

import toml


# Based on: https://github.com/jla524/requirements/blob/main/src/convert.py
def retrieve_packages(toml_content: Dict[str, Any]) -> Dict[str, str]:
    packages = toml_content["tool"]["poetry"]["dependencies"]
    packages.pop("python", None)
    return packages


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


def generate(src_path: Path, target_path: Path) -> None:
    with src_path.open("r") as f:
        content = toml.load(f)

    packages = retrieve_packages(content)
    requirements = generate_requirements_content(packages)

    with target_path.open("w") as f:
        f.write(requirements)


def parse_args():
    """Parses and returns the arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("toml_path", help="Path to the toml source file.")
    parser.add_argument(
        "requirements_path", help="Path to the target requirements.txt file."
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    toml_path = Path(args.toml_path)
    requirements_path = Path(args.requirements_path)

    generate(toml_path, requirements_path)
