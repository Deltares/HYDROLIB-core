"""DIMR Serializer."""

from datetime import datetime
from pathlib import Path
from typing import List
from xml.dom import minidom

from lxml import etree as e

from hydrolib.core.base.models import ModelSaveSettings, SerializerConfig
from hydrolib.core.base.utils import FilePathStyleConverter


class DIMRSerializer:
    """A serializer for DIMR files."""

    @staticmethod
    def serialize(
        path: Path,
        data: dict,
        config: SerializerConfig,
        save_settings: ModelSaveSettings,
    ):
        """Serializes the DIMR data to the file at the specified path.

        Attributes:
            path (Path): The path to the destination file.
            data (Dict): The data to be serialized.
            config (SerializerConfig): The serialization configuration.
            save_settings (ModelSaveSettings): The model save settings.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        xmlns = "http://schemas.deltares.nl/dimr"
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        schema_location = "http://content.oss.deltares.nl/schemas/dimr-1.3.xsd"

        attrib = {e.QName(xsi, "schemaLocation"): f"{xmlns} {schema_location}"}
        namespaces = {None: xmlns, "xsi": xsi}

        root = e.Element(
            "dimrConfig",
            attrib=attrib,
            nsmap=namespaces,
        )

        path_style_converter = FilePathStyleConverter()
        DIMRSerializer._build_tree(
            root, data, config, save_settings, path_style_converter
        )

        to_string = minidom.parseString(e.tostring(root))
        xml = to_string.toprettyxml(indent="  ", encoding="utf-8")

        with path.open("wb") as f:
            f.write(xml)

    @staticmethod
    def _build_tree(
        root,
        data: dict,
        config: SerializerConfig,
        save_settings: ModelSaveSettings,
        path_style_converter: FilePathStyleConverter,
    ):
        name = data.pop("name", None)
        if name:
            root.set("name", name)

        for key, val in data.items():
            if isinstance(val, dict):
                c = e.Element(key)
                DIMRSerializer._build_tree(
                    c, val, config, save_settings, path_style_converter
                )
                root.append(c)
            elif isinstance(val, List):
                for item in val:
                    c = e.Element(key)
                    DIMRSerializer._build_tree(
                        c, item, config, save_settings, path_style_converter
                    )
                    root.append(c)
            else:
                c = e.Element(key)
                if isinstance(val, datetime):
                    c.text = val.isoformat(sep="T", timespec="auto")
                elif isinstance(val, float):
                    c.text = f"{val:{config.float_format}}"
                elif isinstance(val, Path):
                    c.text = path_style_converter.convert_from_os_style(
                        val, save_settings.path_style
                    )
                else:
                    c.text = str(val)
                root.append(c)
