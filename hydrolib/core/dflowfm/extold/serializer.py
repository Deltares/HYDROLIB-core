from pathlib import Path
from typing import Any, Dict

from hydrolib.core.basemodel import (
    DiskOnlyFileModel,
    FileModel,
    ModelSaveSettings,
    SerializerConfig,
)
from hydrolib.core.dflowfm.extold.io import FORCING_FILE_ORDERED_FIELDS
from hydrolib.core.utils import FilePathStyleConverter


class Serializer:
    """Serializer class for serializing the forcing data of the `ExtOldModel` to file."""

    _file_path_style_converter = FilePathStyleConverter()

    def serialize(
        path: Path,
        data: Dict,
        config: SerializerConfig,
        save_settings: ModelSaveSettings,
    ):
        """Serializes the provided data to file at the specified path.

        If a file already exists at the target location the file will be overwritten.

        Args:
            path (Path): The path to write the data to.
            data (Dict): The data to be serialized.
            config (SerializerConfig): The config describing the serialization options.
            save_settings (ModelSaveSettings): The model save settings.
        """

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w") as f:

            for forcing in data["forcing"]:
                forcing_dict = dict(forcing)

                for key in FORCING_FILE_ORDERED_FIELDS:
                    value = forcing_dict.get(key.lower())

                    if Serializer._skip_field_serialization(value):
                        continue

                    value = Serializer._convert_value(value, config, save_settings)

                    f.write((f"{key}={value}\n"))

                f.write(("\n"))

    @classmethod
    def _convert_value(
        cls, value: Any, config: SerializerConfig, save_settings: ModelSaveSettings
    ) -> str:
        if isinstance(value, float):
            return f"{value:{config.float_format}}"
        if isinstance(value, FileModel):
            return Serializer._file_path_style_converter.convert_from_os_style(
                value.filepath, save_settings.path_style
            )

        return str(value)

    @classmethod
    def _skip_field_serialization(cls, value: Any) -> str:
        return value is None or (
            isinstance(value, DiskOnlyFileModel) and value.filepath is None
        )
