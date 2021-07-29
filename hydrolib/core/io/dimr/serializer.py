from pathlib import Path
from typing import List
from xml.dom import minidom

from lxml import etree as e


class DIMRSerializer:
    def serialize(path: Path, data: dict):
        """
        Serializes the DIMR data to the file at the specified path.

        Attributes:
            path (Path): The path to the destination file.
            data (Dict): The data to be serialized.
        """

        path.parent.mkdir(parents=True, exist_ok=True)

        xmlns = "http://schemas.deltares.nl/dimr"
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        schemaLocation = "http://content.oss.deltares.nl/schemas/dimr-1.3.xsd"

        attrib = {e.QName(xsi, "schemaLocation"): f"{xmlns} {schemaLocation}"}
        namespaces = {None: xmlns, "xsi": xsi}

        root = e.Element(
            "dimrConfig",
            attrib=attrib,
            nsmap=namespaces,
        )
        DIMRSerializer._build_tree(root, data)

        to_string = minidom.parseString(e.tostring(root))
        xml = to_string.toprettyxml(indent="  ", encoding="utf-8", standalone=True)

        with path.open("wb") as f:
            f.write(xml)

    @staticmethod
    def _build_tree(root, data: dict):
        name = data.pop("name", None)
        if name:
            root.set("name", name)

        for key, val in data.items():
            if isinstance(val, dict):
                c = e.Element(key)
                DIMRSerializer._build_tree(c, val)
                root.append(c)
            elif isinstance(val, List):
                for item in val:
                    c = e.Element(key)
                    DIMRSerializer._build_tree(c, item)
                    root.append(c)
            else:
                c = e.Element(key)
                c.text = str(val)
                root.append(c)
