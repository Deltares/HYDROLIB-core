from datetime import datetime
from pathlib import Path
from typing import List
from xml.dom import minidom
from hydrolib.core.io.rtc.rtcDataConfig.models import Model as RtcDataConfigModel
from lxml import etree as e


class RtcDataConfigSerializer:
    """A serializer for Real-Time Control files."""

    @staticmethod
    def serialize(path: Path, model: RtcDataConfigModel):
        """
        Serializes the RTC data to the file at the specified path.

        Attributes:
            path (Path): The path to the destination file.
            data (Dict): The RTC data configuration model to be serialized.
        """

        path.parent.mkdir(parents=True, exist_ok=True)

        xmlns = model.attr_xmlns
        xsi = model.attr_xmlns_xs
        schema_location = "rtcDataConfig.xsd"

        attrib = {e.QName(xsi, "schemaLocation"): f"{xmlns} {schema_location}"}
        namespaces = {None: xmlns, "xsi": xsi, "rtc": xmlns}

        root = e.Element(
            "rtcDataConfig",
            attrib=attrib,
            nsmap=namespaces,
        )

        serialization_data = model.rtcDataConfig.dict()
        RtcDataConfigSerializer._build_tree(root, serialization_data)

        to_string = minidom.parseString(e.tostring(root))
        xml = to_string.toprettyxml(indent=4 * " ", encoding="utf-8")

        with path.open("wb") as file:
            file.write(xml)

    @staticmethod
    def _build_tree(root, data: dict):
        for key, val in data.items():
            if val is None:
                continue

            elif key.startswith('attr_'):
                attribute_key = key.lstrip('attr_')
                root.set(attribute_key, str(val))

            elif key == "__root__":
                RtcDataConfigSerializer._build_tree(root, val)

            elif isinstance(val, dict):
                c = e.Element(key)
                root.append(c)
                RtcDataConfigSerializer._build_tree(c, val)

            elif isinstance(val, List):
                for item in val:
                    c = e.Element(key)
                    root.append(c)
                    RtcDataConfigSerializer._build_tree(c, item)

            else:
                c = e.Element(key)
                c.text = str(val)
                root.append(c)
