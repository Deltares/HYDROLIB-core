from pathlib import Path
from warnings import warn

from lxml import etree


class DIMRParser:
    """A parser for DIMR xml files."""

    @staticmethod
    def parse(path: Path) -> dict:
        """Parses a DIMR file to a dictionary.

        Args:
            path (Path): Path to the DIMR configuration file.
        """
        if not path.is_file():
            warn(f"File: `{path}` not found, skipped parsing.")
            return {}

        parser = etree.XMLParser(
            remove_comments=True, resolve_entities=False, no_network=True
        )
        root = etree.parse(str(path), parser=parser).getroot()

        return DIMRParser._node_to_dictionary(root, True)

    @staticmethod
    def _node_to_dictionary(node: etree, ignore_attributes: bool = False):
        """
        Convert an lxml.etree node tree recursively into a nested dictionary.
        The node's attributes and child items will be added to it's dictionary.

        Args:
            node (etree): The etree node
            ignore_attributes (bool): Optional parameter; whether or not to
                                      skip the node's attributes. Default is False.
        """

        result = {} if ignore_attributes else dict(node.attrib)

        for child_node in node.iterchildren():

            key = child_node.tag.split("}")[1]

            if child_node.text and child_node.text.strip():
                value = child_node.text
            else:
                value = DIMRParser._node_to_dictionary(child_node)

            if key in result:

                if type(result[key]) is list:
                    result[key].append(value)
                else:
                    first_value = result[key].copy()
                    result[key] = [first_value, value]
            else:
                result[key] = value

        return result
