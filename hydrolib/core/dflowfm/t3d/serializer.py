from pathlib import Path

from hydrolib.core.base.models import ModelSaveSettings, SerializerConfig


class T3DSerializerConfig(SerializerConfig):
    """Configuration settings for the TimSerializer."""

    column_spacing: int = 1
    """(int): The number of spaces to include between columns in the serialized .t3d file."""


class T3DSerializer:

    @staticmethod
    def serialize(
        path: Path,
        data: dict,
        config: SerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> None:
        """
        Serialize the T3D model data (comments, layer_type, layers, and records)
        into the file at `path`, conforming to the typical .t3d format.

        Args:
            path (Path): Where to write the .t3d file.
            data (dict): A dict representation of the T3DModel. Contains:
                {
                  "comments": [str, ...],
                  "layer_type": "SIGMA" or "Z",
                  "layers": [float, float, ...],
                  "vectormax": Optional[int],
                  "records": [
                    {
                      "time": str,
                      "data": [floats...]
                    }, ...
                  ]
                }
            config (SerializerConfig): Contains settings like float_format.
            save_settings (ModelSaveSettings): Additional settings controlling how paths are saved, etc.

        Examples:
            ```python
            >>> from pathlib import Path
            >>> from hydrolib.core.base.models import ModelSaveSettings
            >>> from hydrolib.core.dflowfm.t3d.serializer import T3DSerializer, T3DSerializerConfig
            >>> data = {
            ... "comments": [],
            ... "layer_type": "SIGMA",
            ... "layers": [0.0, 0.2, 0.6, 0.8, 1.0],
            ... "records": [
            ...         {
            ...             "time": "0 seconds since 2006-01-01 00:00:00 +00:00",
            ...             "data": [1.0, 1.0, 1.0, 1.0, 1.0],
            ...         }
            ...     ],
            ... }
            >>> output_path = Path("tests/data/output/test_serialize.t3d")
            >>> config = T3DSerializerConfig(float_format=".1f")
            >>> T3DSerializer.serialize(output_path, data, config, ModelSaveSettings())
            >>> # Check the contents of the file
            >>> with output_path.open("r") as f:
            ...     print(f.read())
            LAYER_TYPE=SIGMA
            LAYERS=0.0 0.2 0.6 0.8 1.0
            TIME = 0 seconds since 2006-01-01 00:00:00 +00:00
            1.0 1.0 1.0 1.0 1.0
            <BLANKLINE>

            ```
        """
        format_float = lambda v: f"{v:{config.float_format}}"

        with path.open("w", encoding="utf-8") as f:

            # 1) Write the header comments (each line is prefixed by `#`)
            for comment in data.get("comments", []):
                # If the line is blank, just write a blank line; otherwise prefix with '#'
                if comment.strip():
                    f.write(f"#{comment.strip()}\n")
                else:
                    f.write("\n")

            # 2) Write layer type if present, e.g. LAYER_TYPE=SIGMA
            layer_type = data.get("layer_type", None)
            if layer_type:
                f.write(f"LAYER_TYPE={layer_type}\n")

            # 3) Write layers if present, e.g. LAYERS=0.0 0.25 0.75 1.0
            layers = data.get("layers", [])
            if layers:
                layer_str = " ".join(format_float(x) for x in layers)
                f.write(f"LAYERS={layer_str}\n")

            # 4) If VECTORMAX is defined, write it (this is optional in the T3D format).
            vectormax = data.get("vectormax", None)
            if vectormax is not None:
                f.write(f"VECTORMAX={vectormax}\n")

            # 5) Write each record. For each record:
            #      TIME = <time string>
            #      <float1> <float2> ...
            for record in data.get("records", []):
                time_val = record.get("time", "")
                f.write(f"TIME = {time_val}\n")
                data_values = record.get("data", [])
                # Format each float, then join with a space
                line = " ".join(format_float(v) for v in data_values)
                f.write(line + "\n")
