from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from hydrolib.core.basemodel import ModelSaveSettings, SerializerConfig

TimeSeriesRow = List[str]
TimeSeriesBlock = List[TimeSeriesRow]


class TimSerializerConfig(SerializerConfig):
    """Configuration settings for the TimSerializer."""

    column_spacing: int = 1
    """(int): The number of spaces to include between columns in the serialized .tim file."""


class TimSerializer:
    @staticmethod
    def serialize(
        path: Path,
        data: Dict[str, List[Any]],
        config: TimSerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> None:
        """
        Serialize timeseries data to a file in .tim format.

        Args:
            path (Path): The path to the destination .tim file.
            data (Dict[str, List[Any]]): A dictionary with keys "comments" and "timeseries".
            - "comments" represents comments found at the start of the file.
            - "timeseries" is a list of dictionaries with the key as "time" and values as "data".
                - "time" is a time as a string.
                - "data" is data as a list of strings.

            config (TimSerializerConfig): The serialization configuration settings.
            save_settings (ModelSaveSettings): The save settings to be used.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        commentlines = TimSerializer._serialize_comment_lines(data)
        timeserieslines = TimSerializer._serialize_timeseries_lines(data, config)

        file_content = TimSerializer._serialize_file_content(
            timeserieslines, commentlines
        )
        with path.open("w", encoding="utf8") as file:
            file.write(file_content)

    @staticmethod
    def _serialize_comment_lines(data: Dict[str, List[Any]]) -> List[str]:
        commentlines = []
        for comment in data["comments"]:
            commentlines.append(f"#{comment}")
        return commentlines

    @staticmethod
    def _serialize_timeseries_lines(
        data: Dict[str, List[Any]], config: TimSerializerConfig
    ) -> List[str]:
        format_float = lambda v: f"{v:{config.float_format}}"
        timeseriesblock = TimSerializer._serialize_to_timeseries_block(
            data, format_float
        )
        timeserieslines = TimSerializer._serialize_timeseries_to_lines(
            timeseriesblock, config
        )
        return timeserieslines

    @staticmethod
    def _serialize_to_timeseries_block(
        data: Dict[str, List[Any]], format_float: Callable[[float], str]
    ) -> TimeSeriesBlock:
        timeseries_block: TimeSeriesBlock = []
        for timeseries in data["timeseries"]:
            time = timeseries["time"]
            row_elements = timeseries["data"]
            timeseries_row = [format_float(time)] + [
                format_float(value) for value in row_elements
            ]
            timeseries_block.append(timeseries_row)
        return timeseries_block

    @staticmethod
    def _serialize_timeseries_to_lines(
        timeseries_block: TimeSeriesBlock, config: TimSerializerConfig
    ) -> List[str]:
        # Make sure the columns are aligned and have the proper spacing
        column_space = " " * config.column_spacing
        column_lengths = TimSerializer._get_column_lengths(timeseries_block)

        timeserieslines = []
        for timeseries_row in timeseries_block:
            row_elements: List[str] = []
            for index, value in enumerate(timeseries_row):
                whitespace_offset = TimSerializer._get_offset_whitespace(
                    value, column_lengths[index]
                )
                row_elements.append(value + whitespace_offset)

            line = column_space.join(row_elements)
            timeserieslines.append(line)
        return timeserieslines

    @staticmethod
    def _get_offset_whitespace(value: Optional[str], max_length: int) -> str:
        value_length = len(value) if value is not None else 0
        return " " * max(max_length - value_length, 0)

    @staticmethod
    def _serialize_file_content(timeserieslines: List[str], commentlines: List[str]):
        lines = []
        lines.extend(commentlines)
        lines.extend(timeserieslines)
        file_content = "\n".join(lines)
        return file_content

    @staticmethod
    def _get_column_lengths(timeseries_block: TimeSeriesBlock) -> List[int]:
        if len(timeseries_block) == 0:
            return []

        n_columns = len(timeseries_block[0])
        column_lengths = [0] * n_columns

        for timeseries_row in timeseries_block:
            for index, row_element in enumerate(timeseries_row):
                if len(row_element) > column_lengths[index]:
                    column_lengths[index] = len(row_element)

        return column_lengths
