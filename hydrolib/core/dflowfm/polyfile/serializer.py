from itertools import chain
from pathlib import Path
from typing import Generator, Iterable, Optional, Sequence

from hydrolib.core.basemodel import SerializerConfig
from hydrolib.core.dflowfm.polyfile.models import (
    Description,
    Metadata,
    Point,
    PolyObject,
)


class Serializer:
    """Serializer provides several static serialize methods for the models."""

    @staticmethod
    def serialize_description(description: Optional[Description]) -> Iterable[str]:
        """Serialize the Description to a string which can be used within a polyfile.

        Returns:
            str: The serialised equivalent of this Description
        """
        if description is None:
            return []
        if description.content == "":
            return [
                "*",
            ]
        return (f"*{v.rstrip()}" for v in (description.content + "\n").splitlines())

    @staticmethod
    def serialize_metadata(metadata: Metadata) -> Iterable[str]:
        """Serialize this Metadata to a string which can be used within a polyfile.

        The number of rows and number of columns are separated by four spaces.

        Returns:
            str: The serialised equivalent of this Metadata
        """
        return [metadata.name, f"{metadata.n_rows}    {metadata.n_columns}"]

    @staticmethod
    def serialize_point(point: Point, config: SerializerConfig) -> str:
        """Serialize this Point to a string which can be used within a polyfile.

        the point data is indented with 4 spaces, and the individual values are
        separated by 4 spaces as well.

        Args:
            point (Point): The point to serialize.
            config (SerializerConfig): The serialization configuration.

        Returns:
            str: The serialised equivalent of this Point
        """
        space = 4 * " "
        float_format = lambda v: f"{v:{config.float_format}}"
        return space + space.join(
            float_format(v) for v in Serializer._get_point_values(point)
        )

    @staticmethod
    def _get_point_values(point: Point) -> Generator[float, None, None]:
        yield point.x
        yield point.y
        if point.z:
            yield point.z
        for value in point.data:
            yield value

    @staticmethod
    def serialize_poly_object(
        obj: PolyObject, config: SerializerConfig
    ) -> Iterable[str]:
        """Serialize this PolyObject to a string which can be used within a polyfile.

        Args:
            obj (PolyObject): The poly object to serializer.
            config (SerializerConfig): The serialization configuration.

        Returns:
            str: The serialised equivalent of this PolyObject
        """

        description = Serializer.serialize_description(obj.description)
        metadata = Serializer.serialize_metadata(obj.metadata)
        points = [Serializer.serialize_point(obj, config) for obj in obj.points]
        return chain(description, metadata, points)


def write_polyfile(
    path: Path, data: Sequence[PolyObject], config: SerializerConfig
) -> None:
    """Write the data to a new file at path

    Args:
        path (Path): The path to write the data to
        data (Sequence[PolyObject]): The poly objects to write
        config (SerializerConfig): The serialization configuration.
    """
    serialized_poly_objects = [
        Serializer.serialize_poly_object(poly_object, config) for poly_object in data
    ]
    serialized_data = chain.from_iterable(serialized_poly_objects)

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf8") as f:

        for line in serialized_data:
            f.write(line)
            f.write("\n")
