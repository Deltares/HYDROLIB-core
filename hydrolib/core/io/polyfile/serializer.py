from pathlib import Path
from typing import Dict
from hydrolib.core.io.polyfile.components import (
    Description,
    Metadata,
    Point,
    PolyObject,
)


class Serializer:
    """Serializer provides several static serialize methods for the models."""

    @staticmethod
    def serialize_description(description: Description) -> str:
        """Serialize the Description to a string which can be used within a polyfile.

        Returns:
            str: The serialised equivalent of this Description
        """
        if description.content == "":
            return "*"
        else:
            return "\n".join(f"*{v.rstrip()}" for v in description.content.splitlines())

    @staticmethod
    def serialize_metadata(metadata: Metadata) -> str:
        """Serialize this Metadata to a string which can be used within a polyfile.

        The number of rows and number of columns are separated by four spaces.

        Returns:
            str: The serialised equivalent of this Metadata
        """
        return f"{metadata.name}\n{metadata.n_rows}    {metadata.n_columns}"

    @staticmethod
    def serialize_point(point: Point) -> str:
        """Serialize this Point to a string which can be used within a polyfile.

        the point data is indented with 4 spaces, and the individual values are
        separated by 4 spaces as well.

        Returns:
            str: The serialised equivalent of this Point
        """
        z_val = f"{point.z}    " if point.z is not None else ""
        data_vals = "    ".join(str(v) for v in point.data)
        return f"    {point.x}    {point.y}    {z_val}{data_vals}".rstrip()

    @staticmethod
    def serialize_poly_object(obj: PolyObject) -> str:
        """Serialize this PolyObject to a string which can be used within a polyfile.

        Returns:
            str: The serialised equivalent of this Point
        """
        description = (
            f"{Serializer.serialize_description(obj.description)}\n"
            if obj.description is not None
            else ""
        )

        metadata = f"{Serializer.serialize_metadata(obj.metadata)}\n"
        points = "\n".join(map(Serializer.serialize_point, obj.points))
        return f"{description}{metadata}{points}"


def write_polyfile(path: Path, data: Dict) -> None:
    """Write the data to a new file at path

    Args:
        path (Path): The path to write the data to
        data (PolyFile): The data to write
    """
    serialized_data = "\n".join(map(Serializer.serialize_poly_object, data["objects"]))

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w") as f:
        f.write(serialized_data)
