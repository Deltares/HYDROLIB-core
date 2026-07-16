"""Serializer for D-WAQ substance (.sub) files.

This module provides :class:`SubstanceSerializer`, which converts the
dictionary representation produced by
:meth:`~hydrolib.core.dflowfm.substance.models.SubstanceModel.model_dump`
back into the block-based .sub text format.

Configuration is handled via :class:`SubstanceSerializerConfig`, which
controls float formatting (default: Fortran-style ``".4E"`` scientific
notation).

See Also:
    SubstanceParser: Reads .sub files into dictionary form.
    SubstanceModel: Pydantic model that orchestrates parsing and serialization.
"""

from pathlib import Path
from typing import Any, Dict, List

from hydrolib.core.base.models import ModelSaveSettings, SerializerConfig


class SubstanceSerializerConfig(SerializerConfig):
    """Configuration for the :class:`SubstanceSerializer`.

    Controls how numeric parameter values are formatted when writing .sub files.

    Attributes:
        float_format (str):
            Python format specifier for float values. Defaults to ``".4E"``
            which produces Fortran-compatible scientific notation with four
            decimal places (e.g. ``1.5000E+01``). Set to an empty string
            to use plain ``str()`` conversion instead.

    Examples:
        - Default configuration uses scientific notation:
            ```python
            >>> from hydrolib.core.dflowfm.substance.serializer import SubstanceSerializerConfig
            >>> cfg = SubstanceSerializerConfig()
            >>> cfg.float_format
            '.4E'
            >>> f"{15.0:{cfg.float_format}}"
            '1.5000E+01'

            ```
        - Custom format with 2 decimal places:
            ```python
            >>> from hydrolib.core.dflowfm.substance.serializer import SubstanceSerializerConfig
            >>> cfg = SubstanceSerializerConfig(float_format=".2f")
            >>> f"{15.0:{cfg.float_format}}"
            '15.00'

            ```

    See Also:
        SubstanceSerializer: Uses this config during serialization.
    """

    float_format: str = ".4E"
    """str: Python format specifier for float values. Defaults to ``'.4E'``."""


class SubstanceSerializer:
    """Serializer for D-WAQ substance (.sub) files.

    Converts the dictionary produced by ``SubstanceModel.model_dump()`` into
    the block-based .sub text format and writes it to disk. Parent directories
    are created automatically.

    All methods are static; no instance state is required.

    The serialization order follows the .sub file convention:

    1. Substance blocks
    2. Parameter blocks
    3. Output blocks
    4. Active-processes block (omitted when the process list is empty)

    Examples:
        - Serialize minimal data to a file:
            ```python
            >>> import tempfile
            >>> from pathlib import Path
            >>> from hydrolib.core.dflowfm.substance.serializer import (
            ...     SubstanceSerializer, SubstanceSerializerConfig,
            ... )
            >>> from hydrolib.core.base.models import ModelSaveSettings
            >>> data = {
            ...     "substances": [{"name": "OXY", "type": "active",
            ...         "description": "Dissolved Oxygen",
            ...         "concentration_unit": "(g/m3)", "waste_load_unit": "-"}],
            ...     "parameters": [], "outputs": [],
            ...     "active_processes": {"processes": []},
            ... }
            >>> with tempfile.TemporaryDirectory() as td:
            ...     p = Path(td) / "test.sub"
            ...     SubstanceSerializer.serialize(p, data, SubstanceSerializerConfig(), ModelSaveSettings())
            ...     p.exists()
            True

            ```

    See Also:
        SubstanceSerializerConfig: Configuration for float formatting.
        SubstanceParser: Reads .sub files into dictionary form.
        SubstanceModel: Pydantic model that orchestrates parsing and serialization.
    """

    @staticmethod
    def serialize(
        path: Path,
        data: Dict[str, Any],
        config: SubstanceSerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> None:
        """Serialize substance data to a .sub file.

        Writes substance, parameter, output, and active-processes blocks
        in order. Empty active-processes lists are omitted entirely.
        Parent directories are created if they do not exist.

        Args:
            path (Path): Output file path.
            data (Dict[str, Any]): Dictionary from ``SubstanceModel.model_dump()``.
                Expected keys: ``"substances"``, ``"parameters"``,
                ``"outputs"``, ``"active_processes"``.
            config (SubstanceSerializerConfig): Serializer configuration
                controlling float formatting.
            save_settings (ModelSaveSettings): General model save settings.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        lines: List[str] = []

        for substance in data.get("substances", []):
            lines.extend(SubstanceSerializer._serialize_substance(substance))

        for parameter in data.get("parameters", []):
            lines.extend(SubstanceSerializer._serialize_parameter(parameter, config))

        for output in data.get("outputs", []):
            lines.extend(SubstanceSerializer._serialize_output(output))

        active_processes = data.get("active_processes", {})
        processes = active_processes.get("processes", [])
        if processes:
            lines.extend(SubstanceSerializer._serialize_active_processes(processes))

        with path.open("w", encoding="utf8") as f:
            f.write("\n".join(lines))
            if lines:
                f.write("\n")

    @staticmethod
    def _serialize_substance(substance: Dict[str, Any]) -> List[str]:
        """Serialize a single substance dict to .sub file lines.

        Produces the block::

            substance 'Name' active
               description        'desc'
               concentration-unit 'unit'
               waste-load-unit    '-'
            end-substance

        Args:
            substance (Dict[str, Any]): Substance dict with keys ``name``,
                ``type``, ``description``, ``concentration_unit``,
                ``waste_load_unit``.

        Returns:
            List[str]: Lines for the substance block (without trailing newlines).
        """
        name = substance.get("name", "")
        stype = substance.get("type", "active")
        description = substance.get("description", "")
        conc_unit = substance.get("concentration_unit", "")
        wl_unit = substance.get("waste_load_unit", "-")

        return [
            f"substance '{name}' {stype}",
            f"   description        '{description}'",
            f"   concentration-unit '{conc_unit}'",
            f"   waste-load-unit    '{wl_unit}'",
            "end-substance",
        ]

    @staticmethod
    def _serialize_parameter(
        parameter: Dict[str, Any], config: SubstanceSerializerConfig
    ) -> List[str]:
        """Serialize a single parameter dict to .sub file lines.

        Produces the block::

            parameter 'Name'
               description   'desc'
               unit          'unit'
               value          1.5000E+01
            end-parameter

        The value is formatted according to ``config.float_format``.

        Args:
            parameter (Dict[str, Any]): Parameter dict with keys ``name``,
                ``description``, ``unit``, ``value``.
            config (SubstanceSerializerConfig): Serializer configuration.

        Returns:
            List[str]: Lines for the parameter block.
        """
        name = parameter.get("name", "")
        description = parameter.get("description", "")
        unit = parameter.get("unit", "")
        value = parameter.get("value", 0)

        if config.float_format:
            value_str = f"{value:{config.float_format}}"
        else:
            value_str = str(value)

        return [
            f"parameter '{name}'",
            f"   description   '{description}'",
            f"   unit          '{unit}'",
            f"   value          {value_str}",
            "end-parameter",
        ]

    @staticmethod
    def _serialize_output(output: Dict[str, Any]) -> List[str]:
        """Serialize a single output dict to .sub file lines.

        Produces the block::

            output 'Name'
               description   'desc'
            end-output

        Args:
            output (Dict[str, Any]): Output dict with keys ``name``,
                ``description``.

        Returns:
            List[str]: Lines for the output block.
        """
        name = output.get("name", "")
        description = output.get("description", "")

        return [
            f"output '{name}'",
            f"   description   '{description}'",
            "end-output",
        ]

    @staticmethod
    def _serialize_active_processes(
        processes: List[Dict[str, Any]],
    ) -> List[str]:
        """Serialize the active-processes block to .sub file lines.

        Produces the block::

            active-processes
               name  'ProcName' 'Process description'
            end-active-processes

        Args:
            processes (List[Dict[str, Any]]): List of process dicts,
                each with keys ``name`` and ``description``.

        Returns:
            List[str]: Lines for the active-processes block.
        """
        lines = ["active-processes"]
        for proc in processes:
            name = proc.get("name", "")
            description = proc.get("description", "")
            lines.append(f"   name  '{name}' '{description}'")
        lines.append("end-active-processes")
        return lines
