"""Parser for D-WAQ substance (.sub) files.

This module provides :class:`SubstanceParser`, which reads a block-based .sub
file and returns a dictionary representation suitable for constructing a
:class:`~hydrolib.core.dflowfm.substance.models.SubstanceModel`.

The .sub format has four block types:

*   `substance 'Name' active … end-substance`
*   `parameter 'Name' … end-parameter`
*   `output 'Name' … end-output`
*   `active-processes … end-active-processes`

String values are enclosed in single quotes; numeric values use Fortran
scientific notation (e.g. `0.1500E+02`).
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from hydrolib.core.base.parser import open_file_with_fallback_encoding

_TOKEN_RE = re.compile(r"#[^\n]*|'[^']*'|\S+")
"""re.Pattern: Compiled regex that matches a `#` comment, a single-quoted value or a bare word.

A `#` only starts a comment at the beginning of a token, so a `#` inside a quoted value
(or in the middle of a bare word) is kept.
"""


class SubstanceParser:
    """Parser for D-WAQ substance (.sub) files.

    The parser splits the file into whitespace-separated tokens (a single-quoted
    value is one token, even if it contains spaces), identifies block-start
    keywords, and delegates to block-specific helpers that consume tokens until
    the corresponding `end-*` keyword is found. Line breaks carry no meaning, so
    a block may be written over several lines or entirely on one line.

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
        splits it into tokens, then iterates through them to identify and parse
        each block type.

        Args:
            filepath (Path): Path to the .sub file.

        Returns:
            Dict[str, Any]: Dictionary with four keys:

                - `"substances"` — list of substance dicts, each with keys
                  `name`, `type`, `description`, `concentration_unit`,
                  `waste_load_unit`.
                - `"parameters"` — list of parameter dicts, each with keys
                  `name`, `description`, `unit`, and `value` (as raw string).
                  `value` is present only when the block contains a `value`
                  line; a block that omits it produces a dict without the key,
                  which makes model construction fail rather than default to 0.
                - `"outputs"` — list of output dicts, each with keys
                  `name`, `description`.
                - `"active_processes"` — dict with a single key `"processes"`
                  containing a list of dicts with `name` and `description`.

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
        tokens = [t for t in _TOKEN_RE.findall(content) if not t.startswith("#")]

        substances: List[Dict[str, str]] = []
        parameters: List[Dict[str, str]] = []
        outputs: List[Dict[str, str]] = []
        active_processes: Dict[str, List[Dict[str, str]]] = {"processes": []}

        i = 0
        while i < len(tokens):
            keyword = tokens[i].lower()

            if keyword == "substance":
                block, i = SubstanceParser._parse_substance_block(tokens, i)
                substances.append(block)
            elif keyword == "parameter":
                block, i = SubstanceParser._parse_parameter_block(tokens, i)
                parameters.append(block)
            elif keyword == "output":
                block, i = SubstanceParser._parse_output_block(tokens, i)
                outputs.append(block)
            elif keyword == "active-processes":
                block, i = SubstanceParser._parse_active_processes_block(tokens, i)
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
    def _unquote(token: str) -> str:
        """Strip the surrounding single quotes from a token, if present.

        Args:
            token (str): A token produced by the tokenizer.

        Returns:
            str: The token without surrounding quotes.

        Examples:
            - Quoted and bare tokens:
                ```python
                >>> from hydrolib.core.dflowfm.substance.parser import SubstanceParser
                >>> SubstanceParser._unquote("'hello world'")
                'hello world'
                >>> SubstanceParser._unquote("0.1500E+02")
                '0.1500E+02'

                ```
        """
        quoted = len(token) >= 2 and token[0] == "'" and token[-1] == "'"
        return token[1:-1] if quoted else token

    @staticmethod
    def _parse_header_name(tokens: List[str], start: int) -> str:
        """Return the unquoted name following a block keyword, or `""` if absent.

        Args:
            tokens (List[str]): All tokens in the file.
            start (int): Index of the block keyword (`substance`, `parameter`, ...).

        Returns:
            str: The block name.
        """
        name = ""
        if start + 1 < len(tokens):
            name = SubstanceParser._unquote(tokens[start + 1])
        return name

    @staticmethod
    def _parse_fields(
        tokens: List[str], start: int, end_keyword: str, fields: Dict[str, str]
    ) -> Tuple[Dict[str, str], int]:
        """Read `key value` pairs from `start` until `end_keyword` (or EOF).

        Keys are matched case-insensitively. Each recognised key takes the next
        token as its (unquoted) value; unrecognised tokens are skipped.

        Args:
            tokens (List[str]): All tokens in the file.
            start (int): Index of the first token after the block header.
            end_keyword (str): Lowercase terminator, e.g. `end-substance`.
            fields (Dict[str, str]): Maps recognised file keys to result keys.

        Returns:
            Tuple[Dict[str, str], int]: The values found, keyed by result key, and
                the index of the token after the terminator (or `len(tokens)` if
                the block is unterminated).
        """
        values: Dict[str, str] = {}
        i = start
        done = False
        while i < len(tokens) and not done:
            key = tokens[i].lower()
            if key == end_keyword:
                done = True
            elif key in fields:
                has_value = i + 1 < len(tokens) and (
                    tokens[i + 1].lower() != end_keyword
                )
                values[fields[key]] = (
                    SubstanceParser._unquote(tokens[i + 1]) if has_value else ""
                )
                i += 2 if has_value else 1
            else:
                i += 1

        return values, i + 1 if done else i

    @staticmethod
    def _parse_substance_block(
        tokens: List[str], start: int
    ) -> Tuple[Dict[str, str], int]:
        """Parse a `substance … end-substance` block.

        The block has the form (on one or several lines)::

            substance 'Name' active
               description 'text' concentration-unit 'unit' waste-load-unit '-'
            end-substance

        Args:
            tokens (List[str]): All tokens in the file.
            start (int): Index of the `substance` keyword.

        Returns:
            Tuple[Dict[str, str], int]: A tuple of:

                - Parsed substance dict with keys `name`, `type`,
                  `description`, `concentration_unit`, `waste_load_unit`.
                - Index of the next token after the block.
        """
        name = SubstanceParser._parse_header_name(tokens, start)
        after = tokens[start + 2].lower() if start + 2 < len(tokens) else ""

        values, end = SubstanceParser._parse_fields(
            tokens,
            start + 2,
            "end-substance",
            {
                "description": "description",
                "concentration-unit": "concentration_unit",
                "waste-load-unit": "waste_load_unit",
            },
        )
        result: Dict[str, str] = {
            "name": name,
            "type": "inactive" if after == "inactive" else "active",
            "description": "",
            "concentration_unit": "",
            "waste_load_unit": "-",
        }
        result.update(values)

        return result, end

    @staticmethod
    def _parse_parameter_block(
        tokens: List[str], start: int
    ) -> Tuple[Dict[str, str], int]:
        """Parse a `parameter … end-parameter` block.

        The block has the form `parameter 'Name' description '…' unit '…'
        value … end-parameter`, on one or several lines.

        Args:
            tokens (List[str]): All tokens in the file.
            start (int): Index of the `parameter` keyword.

        Returns:
            Tuple[Dict[str, str], int]: A tuple of:

                - Parsed parameter dict with keys `name`, `description`,
                  `unit`, and `value` (kept as raw string). `value` is only
                  included when the block contains a `value` entry, so that a
                  malformed block fails model construction rather than
                  defaulting to 0.
                - Index of the next token after the block.
        """
        name = SubstanceParser._parse_header_name(tokens, start)
        values, end = SubstanceParser._parse_fields(
            tokens,
            start + 2,
            "end-parameter",
            {"description": "description", "unit": "unit", "value": "value"},
        )
        result: Dict[str, str] = {"name": name, "description": "", "unit": ""}
        result.update(values)

        return result, end

    @staticmethod
    def _parse_output_block(
        tokens: List[str], start: int
    ) -> Tuple[Dict[str, str], int]:
        """Parse an `output … end-output` block.

        Args:
            tokens (List[str]): All tokens in the file.
            start (int): Index of the `output` keyword.

        Returns:
            Tuple[Dict[str, str], int]: A tuple of:

                - Parsed output dict with keys `name`, `description`.
                - Index of the next token after the block.
        """
        name = SubstanceParser._parse_header_name(tokens, start)
        values, end = SubstanceParser._parse_fields(
            tokens, start + 2, "end-output", {"description": "description"}
        )
        result: Dict[str, str] = {"name": name, "description": ""}
        result.update(values)

        return result, end

    @staticmethod
    def _parse_active_processes_block(
        tokens: List[str], start: int
    ) -> Tuple[Dict[str, List[Dict[str, str]]], int]:
        """Parse an `active-processes … end-active-processes` block.

        Each `name` entry is followed by two quoted tokens: the process
        identifier and its description. Entries without two quoted tokens are
        skipped.

        Args:
            tokens (List[str]): All tokens in the file.
            start (int): Index of the `active-processes` keyword.

        Returns:
            Tuple[Dict[str, List[Dict[str, str]]], int]: A tuple of:

                - Dict with key `"processes"` containing a list of dicts,
                  each with `name` and `description`.
                - Index of the next token after the block.
        """
        processes: List[Dict[str, str]] = []

        i = start + 1
        done = False
        while i < len(tokens) and not done:
            keyword = tokens[i].lower()
            if keyword == "end-active-processes":
                done = True
            elif (
                keyword == "name"
                and i + 2 < len(tokens)
                and tokens[i + 1].startswith("'")
                and tokens[i + 2].startswith("'")
            ):
                processes.append(
                    {
                        "name": SubstanceParser._unquote(tokens[i + 1]),
                        "description": SubstanceParser._unquote(tokens[i + 2]),
                    }
                )
                i += 3
            else:
                i += 1

        return {"processes": processes}, i + 1 if done else i
