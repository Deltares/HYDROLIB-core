from pathlib import Path
from typing import Dict, Iterable, Optional

from hydrolib.core.basemodel import ModelSaveSettings, SerializerConfig
from hydrolib.core.dflowfm.ini.io_models import Datablock, DatablockRow


class TimSerializerConfig(SerializerConfig):
    max_length_datablock = 10
    datablock_spacing = 0


class TimSerializer:
    @staticmethod
    def serialize(
        path: Path,
        data: Dict,
        config: TimSerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> None:
        """
        Serializes the timeseries data to the file at the specified path in .tim format.

        Attributes:
            path (Path): The path to the destination file.
            data (Dict): The data to be serialized.
            config (TimSerializerConfig): The serialization configuration.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        datarowlist = []
        commentrowlist = []

        for key in data:
            if key == "comments":
                commentrowlist.append(TimSerializer._get_commentblockrow(key, data))
            else:
                datarowlist.append(TimSerializer._get_datablockrow(key, data))

        timeseries = TimSerializer._serialize_datablock(datarowlist, config)

        with path.open("w") as file:
            TimSerializer._write_rows(file, commentrowlist)
            TimSerializer._write_rows(file, timeseries)

    @staticmethod
    def _write_rows(file, rowlist):
        for rows in rowlist:
            for row in rows:
                if isinstance(row, str):
                    file.write(row)

    @staticmethod
    def _get_datablockrow(key, dictionary):
        rowlist = [str]
        rowlist.append(str(key))
        for value in dictionary[key]:
            rowlist.append(str(value))
        return rowlist

    @staticmethod
    def _get_commentblockrow(key, dictionary):
        rowlist = [str]
        for comment in dictionary[key]:
            if isinstance(comment, str):
                data = f"# {comment}"
                rowlist.append(data)
        return rowlist

    @staticmethod
    def _serialize_datablock(datablock: Optional[Datablock], config) -> Iterable[str]:
        if datablock is None or config.max_length_datablock is None:
            return []

        linesofdatablock = []
        for row in datablock:
            linesofdatablock.append(TimSerializer._serialize_row(row, config))
        return linesofdatablock

    @staticmethod
    def _serialize_row(row: DatablockRow, config) -> str:
        elem_spacing = " " * config.datablock_spacing

        elems = []
        for item in row:
            if isinstance(item, str):
                elems += TimSerializer._serialize_row_element(item, config)
        return elem_spacing.join(elems).rstrip() + "\n"

    @staticmethod
    def _serialize_row_element(elem: str, config) -> str:
        max_length = config.max_length_datablock  # type: ignore
        whitespace = _get_offset_whitespace(elem, max_length)
        return elem + whitespace


def _get_offset_whitespace(key: Optional[str], max_length: int) -> str:
    key_length = len(key) if key is not None else 0
    return " " * max(max_length - key_length, 0)
