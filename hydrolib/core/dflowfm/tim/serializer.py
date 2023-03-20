from itertools import count
from pathlib import Path
from typing import Iterable, List, Optional

from hydrolib.core.basemodel import SerializerConfig
from hydrolib.core.dflowfm.ini.io_models import Datablock, DatablockRow
from hydrolib.core.dflowfm.ini.serializer import (
    INISerializerConfig,
    MaxLengths,
    SectionSerializer,
)
from hydrolib.core.dflowfm.tim.parser import TimTimeSerie


class TimSerializerConfig(SerializerConfig):
    datablock_indent: int = 4
    datablock_spacing: int = 2

    @property
    def total_datablock_indent(self) -> int:
        """The combined datablock indentation, i.e. datablock_indent"""
        return self.datablock_indent


class TimTimeSeriesSerializer(SectionSerializer):

    Lines = Iterable[str]

    def serialize_timtimeseries(self, timeserie: TimTimeSerie, config) -> Lines:
        datablock = self._create_tim_datablock(timeserie, config)
        value = self._tim_serialize_datablock(datablock)
        return value

    def _create_tim_datablock(self, timeserie: TimTimeSerie, config) -> Datablock:
        format_float = lambda x: f"{x:{config.float_format}}"
        series = [str(format_float(p)) for p in timeserie.series]
        row = []
        row.append(str(timeserie.time))
        row.extend(series)

        datablock: Datablock = []
        datablock.append(row)
        return datablock

    def _tim_serialize_datablock(self, datablock: Optional[Datablock]) -> Lines:
        if datablock is None:
            return []

        indent = " " * self._config.total_datablock_indent
        return self._tim_serialize_row(datablock[0], indent)

    def _tim_serialize_row(self, row: DatablockRow, indent: str) -> str:
        elem_spacing = " " * self.config.datablock_spacing
        elems = (
            self._tim_serialize_row_element(elem, i) for elem, i in zip(row, count())
        )

        value = indent + elem_spacing.join(elems).rstrip()
        return value

    def _tim_serialize_row_element(self, elem: str, index: int) -> str:
        max_length = 10
        whitespace = _tim_get_offset_whitespace(elem, max_length)
        return elem + whitespace


def _tim_get_offset_whitespace(key: Optional[str], max_length: int) -> str:
    key_length = len(key) if key is not None else 0
    return " " * max(max_length - key_length, 0)


class TimSerializer:
    @staticmethod
    def serialize(
        path: Path, data: List[TimTimeSerie], config: TimSerializerConfig
    ) -> None:
        """
        Serializes the timeseries data to the file at the specified path in .tim format.

        Attributes:
            path (Path): The path to the destination file.
            data (List): The data to be serialized.
            config (SerializerConfig): The serialization configuration.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        timtimeseriesserializer = TimTimeSeriesSerializer(
            TimSerializerConfig(), MaxLengths(key=0, value=0)
        )

        with path.open("w") as f:
            for timeserie in data:
                if timeserie.comment:
                    f.write(timeserie.comment)
                else:
                    row = timtimeseriesserializer.serialize_timtimeseries(
                        timeserie, config
                    )
                    f.write(f"{row}\n")
