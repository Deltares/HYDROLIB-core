"""Parser for D-WAQ substance (.sub) files.

This module provides :class:`SubstanceParser`, which reads a block-based .sub
file and returns a dictionary representation suitable for constructing a
:class:`~hydrolib.core.dflowfm.substance.models.SubstanceModel`.

The .sub format has four block types:

*   ``substance 'Name' active … end-substance``
*   ``parameter 'Name' … end-parameter``
*   ``output 'Name' … end-output``
*   ``active-processes … end-active-processes``

String values are enclosed in single quotes; numeric values use Fortran
scientific notation (e.g. ``0.1500E+02``).
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from hydrolib.core.base.parser import open_file_with_fallback_encoding

_QUOTED_VALUE_RE = re.compile(r"'([^']*)'")
"""re.Pattern: Compiled regex that matches single-quoted values."""


class SubstanceParser:
    """Parser for D-WAQ substance (.sub) files.

    The parser reads the file line by line, identifies block-start keywords,
    and delegates to block-specific helpers that consume lines until the
    corresponding ``end-*`` keyword is found.

    All methods are static; no instance state is required.

    Examples:
        - Parse a .sub file and inspect the returned dictionary keys:
            ```python
            >>> from pathlib import Path
            >>> from hydrolib.core.dflowfm.substance.parser import SubstanceParser
            >>> data = SubstanceParser.parse(Path("tests/data/input/substances/substance-file.sub"))
            >>> sorted(data.keys())
            ['active_processes', 'outputs', 'parameters', 'substances']

            ```
        - Inspect parsed substance details:
            ```python
            >>> from pathlib import Path
            >>> from hydrolib.core.dflowfm.substance.parser import SubstanceParser
            >>> data = SubstanceParser.parse(Path("tests/data/input/substances/substance-file.sub"))
            >>> data["substances"][0]["name"]
            'Any-substance-name-1'
            >>> data["substances"][0]["type"]
            'active'

            ```

    See Also:
        SubstanceSerializer: Writes the dictionary back to .sub format.
        SubstanceModel: Pydantic model constructed from the parser output.
    """

    @staticmethod
    def parse(filepath: Path) -> Dict[str, Any]:
        """Parse a .sub file into a dictionary of substance data.

        Reads the entire file using UTF-8 with Latin-1 fallback encoding,
        then iterates through lines to identify and parse each block type.

        Args:
            filepath (Path): Path to the .sub file.

        Returns:
            Dict[str, Any]: Dictionary with four keys:

                - ``"substances"`` — list of substance dicts, each with keys
                  ``name``, ``type``, ``description``, ``concentration_unit``,
                  ``waste_load_unit``.
                - ``"parameters"`` — list of parameter dicts, each with keys
                  ``name``, ``description``, ``unit``, ``value`` (as raw string).
                - ``"outputs"`` — list of output dicts, each with keys
                  ``name``, ``description``.
                - ``"active_processes"`` — dict with a single key ``"processes"``
                  containing a list of dicts with ``name`` and ``description``.

        Examples:
            - Parse and count blocks:
                ```python
                >>> from pathlib import Path
                >>> from hydrolib.core.dflowfm.substance.parser import SubstanceParser
                >>> data = SubstanceParser.parse(Path("tests/data/input/substances/substance-file.sub"))
                >>> len(data["substances"])
                2
                >>> len(data["parameters"])
                2

                ```
            - Parse an empty file:
                ```python
                >>> from pathlib import Path
                >>> from hydrolib.core.dflowfm.substance.parser import SubstanceParser
                >>> data = SubstanceParser.parse(Path("tests/data/input/substances/empty-file.sub"))
                >>> data["substances"]
                []
                >>> data["active_processes"]["processes"]
                []

                ```
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
        """Extract all single-quoted values from a line of text.

        Args:
            text (str): Input text potentially containing ``'quoted'`` values.

        Returns:
            List[str]: Ordered list of extracted values (without quotes).
                Empty list if no quoted values are found.

        Examples:
            - Extract a description value:
                ```python
                >>> from hydrolib.core.dflowfm.substance.parser import SubstanceParser
                >>> SubstanceParser._extract_quoted_values("description 'hello world'")
                ['hello world']

                ```
            - Extract multiple values from a name line:
                ```python
                >>> from hydrolib.core.dflowfm.substance.parser import SubstanceParser
                >>> SubstanceParser._extract_quoted_values("name  'RearOXY' 'Reaeration of oxygen'")
                ['RearOXY', 'Reaeration of oxygen']

                ```
            - No quotes returns an empty list:
                ```python
                >>> from hydrolib.core.dflowfm.substance.parser import SubstanceParser
                >>> SubstanceParser._extract_quoted_values("value 0.1500E+02")
                []

                ```
        """
        return _QUOTED_VALUE_RE.findall(text)

    @staticmethod
    def _parse_substance_block(
        lines: List[str], start: int
    ) -> Tuple[Dict[str, str], int]:
        """Parse a ``substance … end-substance`` block.

        The opening line has the form::

            substance 'Name' active

        Subsequent indented lines carry field values (``description``,
        ``concentration-unit``, ``waste-load-unit``) until ``end-substance``
        is encountered.

        Args:
            lines (List[str]): All lines in the file.
            start (int): Index of the ``substance`` opening line.

        Returns:
            Tuple[Dict[str, str], int]: A tuple of:

                - Parsed substance dict with keys ``name``, ``type``,
                  ``description``, ``concentration_unit``, ``waste_load_unit``.
                - Index of the next line after the block.
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
        """Parse a ``parameter … end-parameter`` block.

        The opening line has the form ``parameter 'Name'``. Indented lines
        carry ``description``, ``unit``, and ``value`` fields.

        Args:
            lines (List[str]): All lines in the file.
            start (int): Index of the ``parameter`` opening line.

        Returns:
            Tuple[Dict[str, str], int]: A tuple of:

                - Parsed parameter dict with keys ``name``, ``description``,
                  ``unit``, ``value`` (value kept as raw string).
                - Index of the next line after the block.
        """
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
        """Parse an ``output … end-output`` block.

        The opening line has the form ``output 'Name'``. The block
        contains a ``description`` field.

        Args:
            lines (List[str]): All lines in the file.
            start (int): Index of the ``output`` opening line.

        Returns:
            Tuple[Dict[str, str], int]: A tuple of:

                - Parsed output dict with keys ``name``, ``description``.
                - Index of the next line after the block.
        """
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
        """Parse an ``active-processes … end-active-processes`` block.

        Each ``name`` line inside the block has two quoted values: the process
        identifier and its description. Lines with fewer than two quoted values
        are skipped.

        Args:
            lines (List[str]): All lines in the file.
            start (int): Index of the ``active-processes`` opening line.

        Returns:
            Tuple[Dict[str, List[Dict[str, str]]], int]: A tuple of:

                - Dict with key ``"processes"`` containing a list of dicts,
                  each with ``name`` and ``description``.
                - Index of the next line after the block.
        """
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
        """Parse an indented field line into a ``(key, value)`` pair.

        Handles two value forms:

        *   **Quoted**: ``description  'some text'`` returns
            ``("description", "some text")``.
        *   **Unquoted**: ``value  0.1500E+02`` returns
            ``("value", "0.1500E+02")``.

        Keys are always lowercased. Hyphens in keys are preserved
        (e.g. ``concentration-unit``).

        Args:
            line (str): A single indented line from inside a block.

        Returns:
            Tuple[str, str]: ``(key, value)`` pair. If the line has no value
                part, value is an empty string.

        Examples:
            - Parse a quoted description field:
                ```python
                >>> from hydrolib.core.dflowfm.substance.parser import SubstanceParser
                >>> SubstanceParser._parse_field_line("   description 'some text'")
                ('description', 'some text')

                ```
            - Parse an unquoted numeric value:
                ```python
                >>> from hydrolib.core.dflowfm.substance.parser import SubstanceParser
                >>> SubstanceParser._parse_field_line("   value  0.1500E+02")
                ('value', '0.1500E+02')

                ```
            - Parse a key-only line:
                ```python
                >>> from hydrolib.core.dflowfm.substance.parser import SubstanceParser
                >>> SubstanceParser._parse_field_line("   keyword")
                ('keyword', '')

                ```
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
