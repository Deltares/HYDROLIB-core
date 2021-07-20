from pathlib import Path

from lxml import etree


class DimrParser:
    """A parser for DIMR xml files."""

    @staticmethod
    def Parse(path: Path) -> dict:
        """Parses a DIMR file to a dictionary.

        Args:
            path (Path): Path to the DIMR configuration file.
        """
        if not path.is_file():
            raise Exception(f"File does not exist: {path}")

        with open(str(path)) as xml_file:
            xml = xml_file.read().encode()

        parser = etree.XMLParser(remove_comments=True)
        root = etree.fromstring(xml, parser)

        return DimrParser._node_to_dictionary(root)

    @staticmethod
    def _node_to_dictionary(node: etree):
        """
        Convert an lxml.etree node tree recursively into a nested dictionary.
        The node's attributes and child items will be added to it's dictionary.

        Args:
            node (etree): The etree node
        """

        result = dict(node.attrib)

        for child_node in node.iterchildren():

            if "}" in child_node.tag:
                key = child_node.tag.split("}")[1]
            else:
                key = child_node.tag

            if child_node.text and child_node.text.strip():
                value = child_node.text
            else:
                value = DimrParser._node_to_dictionary(child_node)

            if key in result:

                if type(result[key]) is list:
                    result[key].append(value)
                else:
                    first_value = result[key].copy()
                    result[key] = [first_value, value]
            else:
                result[key] = value

        return result
