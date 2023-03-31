from pathlib import Path
from typing import Any, Dict

from hydrolib.core.basemodel import (
    DiskOnlyFileModel,
    FileModel,
    ModelSaveSettings,
    SerializerConfig,
)
from hydrolib.core.dflowfm.extold.common_io import ORDERED_FORCING_FIELDS
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
            data (Dict): The data to be serialized. The data is expected to contain a `forcing` key with a list of `ExtForcing`.
            config (SerializerConfig): The config describing the serialization options.
            save_settings (ModelSaveSettings): The model save settings.
        """

        path.parent.mkdir(parents=True, exist_ok=True)

        serialized_blocks = []

        for forcing in data["forcing"]:
            serialized_block = Serializer._serialize_forcing(
                dict(forcing), config, save_settings
            )
            serialized_blocks.append(serialized_block)

        file_content = "\n\n".join(serialized_blocks)

        with path.open("w") as f:
            f.write(file_content)

    @classmethod
    def _serialize_forcing(
        cls, forcing: Dict, config: SerializerConfig, save_settings: ModelSaveSettings
    ) -> str:

        serialized_rows = []

        for key in ORDERED_FORCING_FIELDS:
            value = forcing.get(key.lower())

            if Serializer._skip_field_serialization(value):
                continue

            value = Serializer._convert_value(value, config, save_settings)

            serialized_row = f"{key}={value}"
            serialized_rows.append(serialized_row)

        serialized_block = "\n".join(serialized_rows)
        return serialized_block

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
