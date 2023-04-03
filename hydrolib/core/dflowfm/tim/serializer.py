from pathlib import Path
from typing import Any, Dict, List

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
        data: Dict[str, Any],
        config: TimSerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> None:
        """
        Serializes timeseries data to a file in .tim format.

        Args:
            path (Path): The path to the destination .tim file.
            data (Dict[str, Any]): The timeseries data to be serialized. The data should be provided as a dictionary with the following keys:
                - 'comments' (List[str]): A list of comments to be included at the beginning of the file. Each comment should be a string.
                - 'timeseries' (Dict[float, List[float]]): A dictionary representing the timeseries data, where the key is the time and the value the values at that time.
            config (TimSerializerConfig): The serialization configuration settings.
            save_settings (ModelSaveSettings): The save settings to be used.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = []

        # Serialize comments
        for comment in data["comments"]:
            lines.append(f"#{comment}")

        # Convert time series float data to time series string data        
        format_float = lambda v: f"{v:{config.float_format}}"

        timeseries_block: TimeSeriesBlock = []
        for time, row_elements in data["timeseries"].items():           
            timeseries_row = [format_float(time)] + [format_float(value) for value in row_elements] 
            timeseries_block.append(timeseries_row)
        
        # Make sure the columns are aligned and have the proper spacing
        column_space = " " * config.column_spacing
        column_lengths = TimSerializer._get_column_lengths(timeseries_block)
        
        for timeseries_row in timeseries_block:

            row_elements: List[str] = []
            for index, value in enumerate(timeseries_row):
                whitespace_offset = " " * column_lengths[index]
                row_elements.append(value + whitespace_offset)

            line = column_space.join(row_elements)
            lines.append(line)

        # Write all the line to file
        file_content = "\n".join(lines)
        with path.open("w") as file:
            file.write(file_content)

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