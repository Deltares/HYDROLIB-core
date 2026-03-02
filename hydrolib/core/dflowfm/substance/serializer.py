"""serializer.py defines the serializer for substance (.sub) files."""

from pathlib import Path
from typing import Any, Dict, List

from hydrolib.core.base.models import ModelSaveSettings, SerializerConfig


class SubstanceSerializerConfig(SerializerConfig):
    """Configuration settings for the SubstanceSerializer."""

    float_format: str = ".4E"


class SubstanceSerializer:
    """Serializer for D-WAQ substance (.sub) files."""

    @staticmethod
    def serialize(
        path: Path,
        data: Dict[str, Any],
        config: SubstanceSerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> None:
        """Serialize substance data to a .sub file.

        Args:
            path: Output file path.
            data: Dictionary from ``SubstanceModel.model_dump()``.
            config: Serializer configuration.
            save_settings: Model save settings.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        lines: List[str] = []

        for substance in data.get("substances", []):
            lines.extend(SubstanceSerializer._serialize_substance(substance))

        for parameter in data.get("parameters", []):
            lines.extend(
                SubstanceSerializer._serialize_parameter(parameter, config)
            )

        for output in data.get("outputs", []):
            lines.extend(SubstanceSerializer._serialize_output(output))

        active_processes = data.get("active_processes", {})
        processes = active_processes.get("processes", [])
        if processes:
            lines.extend(
                SubstanceSerializer._serialize_active_processes(processes)
            )

        with path.open("w", encoding="utf8") as f:
            f.write("\n".join(lines))
            if lines:
                f.write("\n")

    @staticmethod
    def _serialize_substance(substance: Dict[str, Any]) -> List[str]:
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
        lines = ["active-processes"]
        for proc in processes:
            name = proc.get("name", "")
            description = proc.get("description", "")
            lines.append(f"   name  '{name}' '{description}'")
        lines.append("end-active-processes")
        return lines
