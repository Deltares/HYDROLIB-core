from pathlib import Path
from typing import Iterable, List, Optional

from hydrolib.core.basemodel import SerializerConfig
from hydrolib.core.dflowfm.ini.io_models import Datablock, DatablockRow
from hydrolib.core.dflowfm.ini.serializer import MaxLengths, SectionSerializer
from hydrolib.core.dflowfm.tim.parser import TimTimeData


class TimSerializerConfig(SerializerConfig):
    datablock_indent: int = 4
    datablock_spacing: int = 2


class TimTimeDatasSerializer(SectionSerializer):

    Lines = Iterable[str]
    MAX_LENGTH = 10

    def serialize(self, timeserie: TimTimeData, config: TimSerializerConfig) -> Lines:
        """Serialize the provided timeserie with the given config

        Args:
            timeserie (TimTimeData): The timeserie to serialize
            config (TimSerializerConfig): The config describing the serialization options

        Returns:
            Lines: The iterable lines of the serialized timeserie
        """
        datablock = self._create_tim_datablock(timeserie, config)
        return self._tim_serialize_datablock(datablock)

    def _create_tim_datablock(self, timeserie: TimTimeData, config) -> Datablock:
        datablock = []
        row = self._create_tim_data_row(timeserie, config.float_format)
        datablock.append(row)
        return datablock

    def _create_tim_data_row(self, timeserie: TimTimeData, float_format: str):
        format_float = lambda x: f"{x:{float_format}}"
        series = [str(format_float(p)) for p in timeserie.series]
        row = []
        row.append(str(timeserie.time))
        row.extend(series)
        return row

    def _tim_serialize_datablock(self, datablock: Optional[Datablock]) -> Lines:
        if datablock is None:
            return []

        indent = " " * self._config.datablock_indent
        return self._tim_serialize_row(datablock[0], indent)

    def _tim_serialize_row(self, row: DatablockRow, indent: str) -> str:
        elem_spacing = " " * self.config.datablock_spacing
        elems = (self._tim_serialize_row_element(elem) for elem in row)
        return indent + elem_spacing.join(elems).rstrip()

    def _tim_serialize_row_element(self, elem: str) -> str:
        whitespace = _tim_get_offset_whitespace(elem, self.MAX_LENGTH)
        return elem + whitespace


def _tim_get_offset_whitespace(key: Optional[str], max_length: int) -> str:
    key_length = len(key) if key is not None else 0
    return " " * max(max_length - key_length, 0)


class TimSerializer:
    @staticmethod
    def serialize(
        path: Path, data: List[TimTimeData], config: TimSerializerConfig
    ) -> None:
        """
        Serializes the timeseries data to the file at the specified path in .tim format.

        Attributes:
            path (Path): The path to the destination file.
            data (List): The data to be serialized.
            config (TimSerializerConfig): The serialization configuration.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        serializer = TimTimeDatasSerializer(config, MaxLengths(key=0, value=0))

        with path.open("w") as file:
            for timeserie in data:
                TimSerializer._write_row(file, serializer, timeserie, config)

    @staticmethod
    def _write_row(
        file,
        serializer: TimTimeDatasSerializer,
        timeserie: TimTimeData,
        config: TimSerializerConfig,
    ):
        if timeserie.comment:
            file.write(timeserie.comment)
        else:
            row = serializer.serialize(timeserie, config)
            file.write(f"{row}\n")
