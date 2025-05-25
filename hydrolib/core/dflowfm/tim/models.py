from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from pandas import DataFrame
from pydantic.v1 import Field
from pydantic.v1.class_validators import validator

from hydrolib.core.base.models import BaseModel, ModelSaveSettings, ParsableFileModel
from hydrolib.core.base.utils import FortranUtils
from hydrolib.core.dflowfm.tim.parser import TimParser
from hydrolib.core.dflowfm.tim.serializer import TimSerializer, TimSerializerConfig


class TimRecord(BaseModel):
    """Single tim record, representing a time and a list of data."""

    time: float
    """float: Time of the time record."""

    data: List[float] = Field(default_factory=list)
    """List[float]: Record of the time record."""


class TimModel(ParsableFileModel):
    """Class representing a tim (*.tim) file.

    Attributes:
        serializer_config (TimSerializerConfig):
            Configuration for serialization of the .tim file.
        comments (List[str]):
            Header comments from the .tim file.
        timeseries (List[TimRecord]):
            A list of TimRecord objects, each containing a time value and associated data.
        quantities_names (Optional[List[str]]):
            List of names for the quantities in the timeseries.


    Methods:
        _ext() -> str:
            Returns the file extension for .tim files.
        _filename() -> str:
            Returns the default filename for .tim files.
        _get_serializer() -> Callable:
            Returns the serializer callable for .tim files.
        _get_parser() -> Callable:
            Returns the parser callable for .tim files.
        _validate_timeseries_values(cls, v: List[TimRecord]) -> List[TimRecord]:
            Validates the timeseries data.
        as_dataframe(columns: List[Any] = None) -> DataFrame:
            Returns the timeseries as a pandas DataFrame.
        _validate_quantities_names(cls, v, values) -> List[str]:
            Validates that quantities_names match the values or each record.

    Args:
        filepath (Path):
            Path to the .tim file.
        data (Dict):
            Parsed data containing comments and timeseries.
        serializer_config (TimSerializerConfig):
            Configuration for serializing the .tim file.

    Returns:
        List[TimRecord]:
            Validated list of TimRecord objects.

    Raises:
        ValueError:
            If the timeseries has inconsistent column counts or duplicate time values.

    Examples:
        Create a TimModel object from a .tim file:

            ```python
            >>> from hydrolib.core.dflowfm.tim.models import TimModel, TimRecord
            >>> tim_model = TimModel(filepath="tests/data/input/tim/triple_data_for_timeseries.tim")
            >>> print(tim_model.timeseries)
            [TimRecord(time=10.0, data=[1.232, 2.343, 3.454]), TimRecord(time=20.0, data=[4.565, 5.676, 6.787]), TimRecord(time=30.0, data=[1.5, 2.6, 3.7])]

            ```

        Provide names for the quantities in the timeseries:
            ```python
            >>> quantities_names = ["discharge", "waterlevel", "salinity", "temperature", "initialtracer"]
            >>> tim_model = TimModel(filepath="tests/data/input/source-sink/tim-5-columns.tim", quantities_names=quantities_names)
            >>> print(tim_model.quantities_names)
            ['discharge', 'waterlevel', 'salinity', 'temperature', 'initialtracer']
            >>> print(tim_model.as_dataframe())
                   discharge  waterlevel  salinity  temperature  initialtracer
            0.0          1.0         2.0       3.0          4.0            5.0
            100.0        1.0         2.0       3.0          4.0            5.0
            200.0        1.0         2.0       3.0          4.0            5.0
            300.0        1.0         2.0       3.0          4.0            5.0
            400.0        1.0         2.0       3.0          4.0            5.0

            ```

        Create a `TimModel` object from a dictionary:
            ```python
            >>> data = {
            ...     "comments": ["# Example comment"],
            ...     "timeseries": [TimRecord(time=0.0, data=[1.0, 2.0])]
            ... }
            >>> tim_model = TimModel(**data)
            >>> print(tim_model.timeseries)
            [TimRecord(time=0.0, data=[1.0, 2.0])]

            ```

        Create `TimModel` from `TimRecord` objects:
            ```python
            >>> new_tim = TimModel()
            >>> new_tim.comments = ["# Example comment"]
            >>> new_tim.timeseries = [TimRecord(time=0.0, data=[1.0, 2.0])]

            ```

        Serialize the `TimModel` to a .tim file:
            ```python
            >>> new_tim.save(filepath=Path("output.tim")) # doctest: +SKIP

            ```

    See Also:
        TimParser: Used for parsing .tim files.
        TimSerializer: Used for serializing .tim files.
        TimRecord: Represents individual time and data entries in the timeseries.

    Notes:
        This class ensures the integrity of the timeseries by validating data consistency and detecting duplicate time entries.

    References:
        - `TIM file format <https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#C4>`_
    """

    serializer_config = TimSerializerConfig()
    """TimSerializerConfig: The serialization configuration for the tim file."""

    comments: List[str] = Field(default_factory=list)
    """List[str]: A list with the header comment of the tim file."""

    timeseries: List[TimRecord] = Field(default_factory=list)
    """List[TimRecord]: A list containing the timeseries."""

    quantities_names: Optional[List[str]] = Field(default=None)

    def __init__(
        self,
        filepath: Optional[Union[str, Path]] = None,
        quantities_names: Optional[List[str]] = None,
        **parsable_file_kwargs,
    ):
        """
        Custom initializer to handle extra parameters specific to TimModel.

        Args:
            quantities_names (Optional[List[str]]): Names for the quantities in the timeseries.
            *args, **kwargs: Other arguments for the superclass.
        """
        super().__init__(filepath=filepath, **parsable_file_kwargs)
        self.quantities_names = quantities_names

    @classmethod
    def _ext(cls) -> str:
        return ".tim"

    @classmethod
    def _filename(cls) -> str:
        return "timeseries"

    @classmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, TimSerializerConfig, ModelSaveSettings], None]:
        return TimSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return TimParser.parse

    @validator("timeseries", pre=True, check_fields=True, allow_reuse=True)
    def replace_fortran_scientific_notation_for_floats(cls, value, field):
        for record in value:
            if isinstance(record, dict):
                record["time"] = FortranUtils.replace_fortran_scientific_notation(
                    record["time"]
                )
                record["data"] = FortranUtils.replace_fortran_scientific_notation(
                    record["data"]
                )
            elif isinstance(record, TimRecord):
                record.time = FortranUtils.replace_fortran_scientific_notation(
                    record.time
                )
                record.data = FortranUtils.replace_fortran_scientific_notation(
                    record.data
                )

        return value

    @validator("timeseries")
    @classmethod
    def _validate_timeseries_values(cls, v: List[TimRecord]) -> List[TimRecord]:
        """Validate if the number of columns per timeseries matches and if the timeseries have no duplicate times.

        Args:
            v (List[TimRecord]): Timeseries to validate.

        Raises:
            ValueError: When the number of columns for timeseries is zero.
            ValueError: When the number of columns differs per timeseries.
            ValueError: When the timeseries has a duplicate time.

        Returns:
            List[TimRecord]: Validated timeseries.
        """
        if len(v) == 0:
            return v

        cls._raise_error_if_amount_of_columns_differ(v)
        cls._raise_error_if_duplicate_time(v)

        return v

    @staticmethod
    def _raise_error_if_amount_of_columns_differ(timeseries: List[TimRecord]) -> None:
        n_columns = len(timeseries[0].data)

        if n_columns == 0:
            raise ValueError("Time series cannot be empty.")

        for timrecord in timeseries:
            if len(timrecord.data) != n_columns:
                raise ValueError(
                    f"Time {timrecord.time}: Expected {n_columns} columns, but was {len(timrecord.data)}"
                )

    @staticmethod
    def _raise_error_if_duplicate_time(timeseries: List[TimRecord]) -> None:
        seen_times = set()
        for timrecord in timeseries:
            if timrecord.time in seen_times:
                raise ValueError(
                    f"Timeseries cannot contain duplicate times. Time: {timrecord.time} is duplicate."
                )
            seen_times.add(timrecord.time)

    @validator("quantities_names")
    def _validate_quantities_names(cls, v, values):
        """Validate if the number of quantities_names matches the number of columns in the timeseries.

        The validator compared the amount of quantities_names with the number of columns in the first record of
        the timeseries.
        """
        if v is not None:
            first_records_data = values["timeseries"][0].data
            if len(v) != len(first_records_data):
                raise ValueError(
                    f"The number of quantities_names ({len(v)}) must match the number of columns in the Tim file ({len(first_records_data)})."
                )
        return v

    def add_column(self, new_values: List[float], column_name: str = None) -> None:
        """
        Add new values to each TimRecord in the timeseries, representing a new location.

        Args:
            new_values (List[float]): A list of new values to add, one for each TimRecord.
            column_name (str, optional): The name of the new column. Defaults to None.
                if None, the column is named as "quantity-{len(quantities_names) + 1}".

        Raises:
            ValueError: If the number of new values does not match the number of TimRecords.

        Examples:
            ```python
            >>> tim_model = TimModel(
            ...     timeseries=[
            ...         TimRecord(time=0.0, data=[1.0, 2.0]),
            ...         TimRecord(time=1.0, data=[3.0, 4.0]),
            ...     ]
            ... )
            >>> tim_model.add_column([5.0, 6.0])
            >>> print(tim_model.timeseries)
            [TimRecord(time=0.0, data=[1.0, 2.0, 5.0]), TimRecord(time=1.0, data=[3.0, 4.0, 6.0])]

            ```
        """
        if len(new_values) != len(self.timeseries):
            raise ValueError(
                f"Expected {len(self.timeseries)} values, but got {len(new_values)}."
            )

        for record, value in zip(self.timeseries, new_values):
            record.data.append(value)

        if self.quantities_names:
            if column_name is None:
                column_name = f"quantity-{len(self.quantities_names) + 1}"
            self.quantities_names.append(column_name)

    def as_dataframe(self, columns: List[Any] = None) -> DataFrame:
        """Return the timeseries as a pandas DataFrame.

        Args:
            columns (List[Any, str], optional, Defaults to None):
                The column names for the DataFrame.

        Returns:
            DataFrame: The timeseries as a pandas DataFrame.

        Notes:
            - If the columns are not provided, the quantities_names will be used as column names.
            - If the quantities_names are not provided, the columns will be named as 0, 1, 2, etc.

        Examples:
            Create a `TimModel` object from a .tim file:
                >>> from hydrolib.core.dflowfm.tim.models import TimModel
                >>> tim_model = TimModel(filepath="tests/data/input/tim/triple_data_for_timeseries.tim")
                >>> df = tim_model.as_dataframe()
                >>> print(df)
                          0      1      2
                10.0  1.232  2.343  3.454
                20.0  4.565  5.676  6.787
                30.0  1.500  2.600  3.700

            If the `TimModel` object was created with quantities names:
                >>> quantities_names = ["Column1", "Column2", "Column3"]
                >>> tim_model = TimModel(filepath="tests/data/input/tim/triple_data_for_timeseries.tim", quantities_names=quantities_names)
                >>> df = tim_model.as_dataframe()
                >>> print(df)
                      Column1  Column2  Column3
                10.0    1.232    2.343    3.454
                20.0    4.565    5.676    6.787
                30.0    1.500    2.600    3.700

            To add column names to the DataFrame after you have created the `TimModel` object:
                >>> df = tim_model.as_dataframe(columns=["Column1", "Column2", "Column3"])
                >>> print(df)
                      Column1  Column2  Column3
                10.0    1.232    2.343    3.454
                20.0    4.565    5.676    6.787
                30.0    1.500    2.600    3.700
        """
        time_series = [record.data for record in self.timeseries]
        index = [record.time for record in self.timeseries]
        if not columns:
            columns = self.quantities_names
        return DataFrame(time_series, index=index, columns=columns)

    def as_dict(self) -> Dict[str, List[float]]:
        """Extract time series data from a TIM model.

        Extract the time series data (each column) from the TimModel object

        Returns:
            Dict[str, List[float]]: A dictionary containing the time series data form each column.
            the keys of the dictionary will be index starting from 1 to the number of columns in the tim file
            (excluding the first column(time)).

        Examples:
            ```python
            >>> tim_file = Path("tests/data/input/source-sink/leftsor.tim")
            >>> time_file = TimParser.parse(tim_file)
            >>> tim_model = TimModel(**time_file)
            >>> time_series = tim_model.as_dict()
            >>> print(time_series) # doctest: +SKIP
            {
                1: [1.0, 1.0, 3.0, 5.0, 8.0],
                2: [2.0, 2.0, 5.0, 8.0, 10.0],
                3: [3.0, 5.0, 12.0, 9.0, 23.0],
                4: [4.0, 4.0, 4.0, 4.0, 4.0]
            }
            ```
        """
        data = self.as_dataframe().to_dict(orient="list")
        return data

    def get_units(self):
        """Return the units for each quantity in the timeseries.

        Returns:
            List[str]: A list of units for each quantity in the timeseries.

        Examples:
            Create a `TimModel` object from a .tim file:
                ```python
                >>> from hydrolib.core.dflowfm.tim.models import TimModel
                >>> tim_model = TimModel(filepath="tests/data/input/source-sink/tim-5-columns.tim")
                >>> tim_model.quantities_names = ["discharge", "waterlevel", "temperature", "salinity", "initialtracer"]
                >>> print(tim_model.get_units())
                ['m3/s', 'm', 'degC', '1e-3', '-']

                ```
        """
        if self.quantities_names is None:
            return None
        return TimModel._get_quantity_unit(self.quantities_names)
