from pathlib import Path
from typing import Any, Dict, List

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

    @staticmethod
    def serialize(
        path: Path,
        data: Dict[str, List[Any]],
        config: SerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> None:

        """
        Serialize the given data and write it to a file at the given path.

        This function may create a new file at the given path, or overwrite an existing file.

        Args:
            path (Path): The path to write the serialized data to.
            data (Dict[str, List[Any]]): The data to be serialized. The data should contain two keys:
                - 'comment' (List[str]): a list of the comments
                - 'forcing' (List[Dict[str, Any]]): a list of the external forcing data
            config (SerializerConfig): Configuration settings for the serializer.
            save_settings (ModelSaveSettings): Settings for how the model should be saved.
        """

        path.parent.mkdir(parents=True, exist_ok=True)

        serialized_comments: List[str] = []
        serialized_blocks: List[str] = []

        for comment in data["comment"]:
            serialized_comment = Serializer._serialize_comment(comment)
            serialized_comments.append(serialized_comment)

        for forcing in data["forcing"]:
            serialized_block = Serializer._serialize_forcing(
                forcing, config, save_settings
            )
            serialized_blocks.append(serialized_block)

        file_content: str = (
            "\n".join(serialized_comments) + "\n" + "\n\n".join(serialized_blocks)
        )

        with path.open("w", encoding="utf8") as f:
            f.write(file_content)

    @staticmethod
    def _serialize_comment(comment: str):
        return f"*{comment}"

    @staticmethod
    def _serialize_forcing(
        forcing: Dict[str, Any],
        config: SerializerConfig,
        save_settings: ModelSaveSettings,
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
