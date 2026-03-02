"""parser.py defines the parser for substance (.sub) files."""

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from hydrolib.core.base.parser import open_file_with_fallback_encoding

_QUOTED_VALUE_RE = re.compile(r"'([^']*)'")


class SubstanceParser:
    """Parser for D-WAQ substance (.sub) files.

    The substance file format is block-based with 4 block types:
    ``substance``, ``parameter``, ``output``, and ``active-processes``.
    Each block opens with a keyword and closes with ``end-<keyword>``.
    String values are enclosed in single quotes.
    """

    @staticmethod
    def parse(filepath: Path) -> Dict[str, Any]:
        """Parse a .sub file into a dictionary.

        Args:
            filepath: Path to the .sub file.

        Returns:
            Dict with keys: ``substances``, ``parameters``, ``outputs``,
            ``active_processes``.
        """
        content = open_file_with_fallback_encoding(filepath)
        lines = content.splitlines()

        substances: List[Dict[str, str]] = []
        parameters: List[Dict[str, str]] = []
        outputs: List[Dict[str, str]] = []
        active_processes: Dict[str, List[Dict[str, str]]] = {"processes": []}

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            lower = line.lower()

            if lower.startswith("substance "):
                block, i = SubstanceParser._parse_substance_block(lines, i)
                substances.append(block)
            elif lower.startswith("parameter "):
                block, i = SubstanceParser._parse_parameter_block(lines, i)
                parameters.append(block)
            elif lower.startswith("output "):
                block, i = SubstanceParser._parse_output_block(lines, i)
                outputs.append(block)
            elif lower.startswith("active-processes"):
                block, i = SubstanceParser._parse_active_processes_block(lines, i)
                active_processes = block
            else:
                i += 1

        return {
            "substances": substances,
            "parameters": parameters,
            "outputs": outputs,
            "active_processes": active_processes,
        }

    @staticmethod
    def _extract_quoted_values(text: str) -> List[str]:
        """Extract all single-quoted values from *text*."""
        return _QUOTED_VALUE_RE.findall(text)

    @staticmethod
    def _parse_substance_block(
        lines: List[str], start: int
    ) -> Tuple[Dict[str, str], int]:
        """Parse a ``substance … end-substance`` block.

        The opening line has the form::

            substance 'Name' active

        Subsequent indented lines carry field values until ``end-substance``.
        """
        header = lines[start].strip()
        quoted = SubstanceParser._extract_quoted_values(header)
        name = quoted[0] if quoted else ""

        # Determine active / inactive from the text after the quoted name
        after_name = header.split("'")[-1].strip().lower()
        substance_type = "inactive" if "inactive" in after_name else "active"

        result: Dict[str, str] = {
            "name": name,
            "type": substance_type,
            "description": "",
            "concentration_unit": "",
            "waste_load_unit": "-",
        }

        i = start + 1
        while i < len(lines):
            line = lines[i].strip()
            lower = line.lower()

            if lower == "end-substance":
                return result, i + 1

            key, value = SubstanceParser._parse_field_line(line)
            if key == "description":
                result["description"] = value
            elif key == "concentration-unit":
                result["concentration_unit"] = value
            elif key == "waste-load-unit":
                result["waste_load_unit"] = value

            i += 1

        return result, i

    @staticmethod
    def _parse_parameter_block(
        lines: List[str], start: int
    ) -> Tuple[Dict[str, str], int]:
        """Parse a ``parameter … end-parameter`` block."""
        header = lines[start].strip()
        quoted = SubstanceParser._extract_quoted_values(header)
        name = quoted[0] if quoted else ""

        result: Dict[str, str] = {
            "name": name,
            "description": "",
            "unit": "",
            "value": "0",
        }

        i = start + 1
        while i < len(lines):
            line = lines[i].strip()
            lower = line.lower()

            if lower == "end-parameter":
                return result, i + 1

            key, value = SubstanceParser._parse_field_line(line)
            if key == "description":
                result["description"] = value
            elif key == "unit":
                result["unit"] = value
            elif key == "value":
                result["value"] = value

            i += 1

        return result, i

    @staticmethod
    def _parse_output_block(
        lines: List[str], start: int
    ) -> Tuple[Dict[str, str], int]:
        """Parse an ``output … end-output`` block."""
        header = lines[start].strip()
        quoted = SubstanceParser._extract_quoted_values(header)
        name = quoted[0] if quoted else ""

        result: Dict[str, str] = {
            "name": name,
            "description": "",
        }

        i = start + 1
        while i < len(lines):
            line = lines[i].strip()
            lower = line.lower()

            if lower == "end-output":
                return result, i + 1

            key, value = SubstanceParser._parse_field_line(line)
            if key == "description":
                result["description"] = value

            i += 1

        return result, i

    @staticmethod
    def _parse_active_processes_block(
        lines: List[str], start: int
    ) -> Tuple[Dict[str, List[Dict[str, str]]], int]:
        """Parse an ``active-processes … end-active-processes`` block."""
        processes: List[Dict[str, str]] = []

        i = start + 1
        while i < len(lines):
            line = lines[i].strip()
            lower = line.lower()

            if lower == "end-active-processes":
                return {"processes": processes}, i + 1

            if lower.startswith("name"):
                quoted = SubstanceParser._extract_quoted_values(line)
                if len(quoted) >= 2:
                    processes.append(
                        {"name": quoted[0], "description": quoted[1]}
                    )

            i += 1

        return {"processes": processes}, i

    @staticmethod
    def _parse_field_line(line: str) -> Tuple[str, str]:
        """Parse an indented field line into ``(key, value)``.

        Handles two forms:
        - Quoted value: ``description  'some text'``  → ``("description", "some text")``
        - Unquoted value: ``value  0.1500E+02``       → ``("value", "0.1500E+02")``
        """
        parts = line.split(None, 1)
        if len(parts) < 2:
            return (parts[0].lower() if parts else "", "")

        key = parts[0].lower()
        rest = parts[1].strip()

        # Try quoted value first
        quoted = SubstanceParser._extract_quoted_values(rest)
        if quoted:
            return key, quoted[0]

        # Unquoted value (e.g. numeric)
        return key, rest.strip()
