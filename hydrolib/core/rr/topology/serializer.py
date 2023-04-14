import os
from pathlib import Path
from typing import Any, Dict

from hydrolib.core.basemodel import ModelSaveSettings, SerializerConfig


class NodeFileSerializer:
    """Serializer for the RR node topology data."""

    @staticmethod
    def serialize(
        path: Path,
        data: dict,
        config: SerializerConfig,
        save_settings: ModelSaveSettings,
    ):
        """
        Serializes the RR node topology data to the file at the specified path.

        Args:
            path (Path): The path to the destination file.
            data (Dict): The data to be serialized.
            config (SerializerConfig): The serialization configuration.
            save_settings (ModelSaveSettings): The model save settings.
        """

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf8") as f:
            for node in data["node"]:
                line = f"NODE {NodeFileSerializer._to_line(node, config)} node\n"
                f.write(line)

    @staticmethod
    def _to_line(node: Dict[str, Any], config: SerializerConfig) -> str:

        identifier = node["id"]
        nm = node["nm"]
        ri = node["ri"]
        mt = node["mt"]
        nt = node["nt"]
        obid = node["ObID"]
        px = node["px"]
        py = node["py"]

        float_format = lambda v: f"{v:{config.float_format}}"
        return f"id '{identifier}' nm '{nm}' ri '{ri}' mt 1 '{mt}' nt {nt} ObID '{obid}' px {float_format(px)} py {float_format(py)}"


class LinkFileSerializer:
    """Serializer for the RR link topology data."""

    @staticmethod
    def serialize(
        path: Path,
        data: dict,
        config: SerializerConfig,
        save_settings: ModelSaveSettings,
    ):
        """
        Serializes the RR link topology data to the file at the specified path.

        Args:
            path (Path): The path to the destination file.
            data (Dict): The data to be serialized.
            config (SerializerConfig): The serialization configuration.
            save_settings (ModelSaveSettings): The model save settings.
        """

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf8") as f:
            for link in data["link"]:
                line = f"BRCH {LinkFileSerializer._to_line(link)} brch\n"
                f.write(line)

    @staticmethod
    def _to_line(link: Dict[str, Any]) -> str:
        identifier = link["id"]
        nm = link["nm"]
        ri = link["ri"]
        mt = link["mt"]
        bt = link["bt"]
        obid = link["ObID"]
        bn = link["bn"]
        en = link["en"]

        return f"id '{identifier}' nm '{nm}' ri '{ri}' mt 1 '{mt}' bt {bt} ObID '{obid}' bn '{bn}' en '{en}'"
