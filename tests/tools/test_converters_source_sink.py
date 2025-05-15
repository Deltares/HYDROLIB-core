from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

from hydrolib.core.dflowfm.ext.models import SourceSink
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.tools.extforce_convert.converters import SourceSinkConverter
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser

tim_file = Path("tests/data/input/source-sink/leftsor.tim")


@pytest.fixture
def converter() -> SourceSinkConverter:
    converter = SourceSinkConverter()
    converter.root_dir = "tests/data/input/source-sink"
    return converter


@pytest.fixture
def time_file_full() -> Path:
    return tim_file


@pytest.fixture
def start_time():
    return "minutes since 2015-01-01 00:00:00"


@pytest.mark.parametrize(
    "tim_file, ext_file_quantity_list, expected_data",
    [
        # The tim file has 4 columns (plus the time column), and the list of ext quantities has 4 quantities.
        pytest.param(
            tim_file,
            ["discharge", "temperature", "salinity", "initialtracer_anyname"],
            {
                "discharge": [1.0] * 5,
                "salinitydelta": [2.0] * 5,
                "temperaturedelta": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="test_default_all_quantities_comes_from_ext",
        ),
        # The tim file has 4 columns (plus the time column), but the list of ext quantities has only 3 quantities.
        pytest.param(
            tim_file,
            ["discharge", "temperature", "salinity"],
            None,
            id="test_list_of_ext_quantities_tim_column_mismatch",
        ),
        # The tim file has 3 columns (plus the time column), but the list of ext quantities has only 3 quantities.
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_or_salinity.tim"),
            ["discharge", "salinity", "initialtracer_anyname"],
            {
                "discharge": [1.0] * 5,
                "salinitydelta": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="no_temperature",
        ),
        # The tim file has 3 columns (plus the time column), and the list of ext quantities has only 3 quantities.
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_or_salinity.tim"),
            ["discharge", "temperature", "initialtracer_anyname"],
            {
                "discharge": [1.0] * 5,
                "temperaturedelta": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="no_salinity",
        ),
        # The tim file has 2 columns (plus the time column), and the list of ext quantities has only 2 quantities.
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_no_salinity.tim"),
            ["discharge", "initialtracer_anyname"],
            {
                "discharge": [1.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="no_temperature_no_salinity",
        ),
    ],
)
def test_parse_tim_model(
    converter: SourceSinkConverter, tim_file, ext_file_quantity_list, expected_data
):

    if expected_data is None:
        with pytest.raises(ValueError):
            converter.parse_tim_model(tim_file, ext_file_quantity_list)
    else:
        time_series_data = converter.parse_tim_model(tim_file, ext_file_quantity_list)
        data = time_series_data.as_dataframe().to_dict(orient="list")
        assert data == expected_data


@pytest.mark.parametrize(
    "tim_file, ext_file_quantity_list, mdu_quantities, expected_data",
    [
        pytest.param(
            tim_file,
            ["discharge", "initialtracer_anyname"],
            {"salinity": True, "temperature": True},
            {
                "discharge": [1.0] * 5,
                "salinitydelta": [2.0] * 5,
                "temperaturedelta": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="all_quantities_from_mdu",
        ),
        pytest.param(
            tim_file,
            ["discharge", "temperature", "initialtracer_anyname"],
            {"salinity": True, "temperature": False},
            {
                "discharge": [1.0] * 5,
                "salinitydelta": [2.0] * 5,
                "temperaturedelta": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="temp_from_ext_salinity_from_mdu",
        ),
        pytest.param(
            tim_file,
            ["discharge", "salinity", "initialtracer_anyname"],
            {"salinity": False, "temperature": True},
            {
                "discharge": [1.0] * 5,
                "salinitydelta": [2.0] * 5,
                "temperaturedelta": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="temp_from_mdu_salinity_from_ext",
        ),
        pytest.param(
            tim_file,
            ["discharge", "salinity", "initialtracer_anyname"],
            {"salinity": True, "temperature": True},
            {
                "discharge": [1.0] * 5,
                "salinitydelta": [2.0] * 5,
                "temperaturedelta": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="temp_salinity_from_mdu",
        ),
        pytest.param(
            tim_file,
            ["discharge", "salinity", "temperature", "initialtracer_anyname"],
            {"salinity": False, "temperature": True},
            {
                "discharge": [1.0] * 5,
                "salinitydelta": [2.0] * 5,
                "temperaturedelta": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="temp_from_mdu_temp_salinity_from_ext",
        ),
    ],
)
def test_parse_tim_model_with_mdu(
    converter: SourceSinkConverter,
    tim_file,
    ext_file_quantity_list,
    mdu_quantities,
    expected_data,
):
    time_series_data = converter.parse_tim_model(
        tim_file, ext_file_quantity_list, **mdu_quantities
    )
    data = time_series_data.as_dataframe().to_dict(orient="list")
    assert data == expected_data


def compare_data(new_quantity_block: SourceSink):
    # check the converted forcings
    quantity_list = [
        "discharge",
        "salinitydelta",
        "temperaturedelta",
        "initialtracer_anyname",
    ]

    assert all(quantity in new_quantity_block.__dict__ for quantity in quantity_list)
    # all the quantities are stored in discharge attribute (one forcing model that has all the Forcings)
    # and this forcingModel is duplicated in the salinitydelta, temperaturedelta, and initialtracer_anyname
    # to be able to save them in the same .bc file.
    quantity = "discharge"
    forcing_model = getattr(new_quantity_block, quantity)
    units = [
        forcing_model.forcing[i].quantityunitpair[1].unit
        for i in range(len(quantity_list))
    ]
    assert units == ["m3/s", "1e-3", "degC", "-"]
    # check the values of the data block
    data = [forcing_model.forcing[i].as_dataframe() for i in range(len(quantity_list))]
    # initialtracer_anyname
    assert data[3].loc[:, 0].to_list() == [4.0, 4.0, 4.0, 4.0, 4.0]
    # temperature
    assert data[2].loc[:, 0].to_list() == [3.0, 3.0, 3.0, 3.0, 3.0]
    # salinity
    assert data[1].loc[:, 0].to_list() == [2.0, 2.0, 2.0, 2.0, 2.0]
    # discharge
    assert data[0].loc[:, 0].to_list() == [1.0, 1.0, 1.0, 1.0, 1.0]


class TestConverter:

    def test_default(self, converter: SourceSinkConverter, start_time: str):
        """
        The test case is based on the following assumptions:
        - temperature, salinity, and initialtracer_anyname are other quantities in the ext file.
        - The ext file has the following structure:
        ```
        QUANTITY=initialtemperature
        FILENAME=right.pol
        FILETYPE=10
        METHOD=4
        OPERAND=O
        VALUE=11.

        QUANTITY=initialsalinity
        FILENAME=right.pol
        FILETYPE=10
        METHOD=4
        OPERAND=O
        VALUE=11.

        QUANTITY=initialtracer_anyname
        FILENAME=leftsor.pliz
        FILETYPE=9
        METHOD=1
        OPERAND=O

        QUANTITY=discharge_salinity_temperature_sorsin
        FILENAME=leftsor.pliz
        FILETYPE=9
        METHOD=1
        OPERAND=O
        AREA=1.0
        ```

        - The time file has the following structure:
        ```
        0.0 1.0 2.0 3.0 4.0
        100 1.0 2.0 3.0 4.0
        200 1.0 2.0 3.0 4.0
        300 1.0 2.0 3.0 4.0
        400 1.0 2.0 3.0 4.0
        ```

        - The polyline has only 3 columns, so the zsink and zsource will have only one value which is in the third column.
        ```
        zsink = -4.2
        zsource = -3
        ```

        - The polyline file has the following structure:
        ```
        L1
             2 3
              63.350456 12.950216 -4.200000
              45.200344 6.350155 -3.000
        ```

        """
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.DischargeSalinityTemperatureSorSin,
            filename="tests/data/input/source-sink/leftsor.pliz",
            filetype=9,
            method="1",
            operand="O",
            area=1.0,
        )

        ext_file_other_quantities = [
            "salinity",
            "temperature",
            "initialtracer_anyname",
        ]

        new_quantity_block = converter.convert(
            forcing, ext_file_other_quantities, start_time
        )

        assert new_quantity_block.zsink == [-4.2]
        assert new_quantity_block.zsource == [-3]

        # check the converted bc_forcing
        compare_data(new_quantity_block)

    def test_4_5_columns_polyline(
        self, converter: SourceSinkConverter, start_time: str
    ):
        """
        The test case is based on the assumptions of the default test plus the following changes:

        - The polyline has only four or five columns, so the zsink and zsource will have two values which is in the
        third and forth columns' values, and if there is a fifth column it will be ignored.
        ```
        zsink = [-4.2, -5.35]
        zsource = [-3, -2.90]
        ```

        - The polyline file has the following structure:
        ```
        L1
             2 3
              63.35 12.95 -4.20 -5.35
              ...

              ...
              45.20 6.35 -3.00 -2.90
        ```
        when there is a fifth column:
        ```
        L1
             2 3
              63.35 12.95 -4.20 -5.35 0
              ...

              ...
              45.20 6.35 -3.00 -2.90 0
        ```

        """
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.DischargeSalinityTemperatureSorSin,
            filename="tests/data/input/source-sink/leftsor-5-columns.pliz",
            filetype=9,
            method="1",
            operand="O",
            area=1.0,
        )

        ext_file_other_quantities = [
            "salinity",
            "temperature",
            "initialtracer_anyname",
        ]

        tim_file = Path("leftsor.tim")
        with patch("pathlib.Path.with_suffix", return_value=tim_file):
            new_quantity_block = converter.convert(
                forcing, ext_file_other_quantities, start_time
            )

        assert new_quantity_block.zsink == [-4.2, -5.35]
        assert new_quantity_block.zsource == [-3, -2.90]

        # check the converted bc_forcing
        compare_data(new_quantity_block)

    def test_no_temperature_no_salinity(
        self, converter: SourceSinkConverter, start_time: str
    ):
        """
        The test case is based on the assumptions of the default test plus the following changes:

        - The timfile has only two columns (plus the time column), and the list of ext quantities has only two quantities.
        ```


        - The tim file has the following structure:
        ```
        0.0 1.0 4.0
        100 1.0 4.0
        200 1.0 4.0
        300 1.0 4.0
        400 1.0 4.0
        ```

        """
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.DischargeSalinityTemperatureSorSin,
            filename="tests/data/input/source-sink/leftsor.pliz",
            filetype=9,
            method="1",
            operand="O",
            area=1.0,
        )

        ext_file_other_quantities = [
            "initialtracer_anyname",
        ]

        tim_file = Path("no_temperature_no_salinity.tim")
        with patch("pathlib.Path.with_suffix", return_value=tim_file):
            new_quantity_block = converter.convert(
                forcing, ext_file_other_quantities, start_time
            )

        assert new_quantity_block.zsink == [-4.2]
        assert new_quantity_block.zsource == [-3]

        validation_list = ["discharge", "initialtracer_anyname"]

        # check the converted bc_forcing
        quantity = "discharge"
        forcing_model = getattr(new_quantity_block, quantity)
        quantities_names = [
            forcing_model.forcing[i].quantityunitpair[1].quantity
            for i in range(len(validation_list))
        ]
        units = [
            forcing_model.forcing[i].quantityunitpair[1].unit
            for i in range(len(validation_list))
        ]
        assert quantities_names == validation_list

        assert units == ["m3/s", "-"]
        data = [
            forcing_model.forcing[i].as_dataframe() for i in range(len(validation_list))
        ]
        # check the values of the data block
        # initialtracer_anyname
        assert data[1].loc[:, 0].to_list() == [4.0, 4.0, 4.0, 4.0, 4.0]
        # discharge
        assert data[0].loc[:, 0].to_list() == [1.0, 1.0, 1.0, 1.0, 1.0]


class TestMainConverter:
    path = "tests/data/input/source-sink/source-sink.ext"
    mdu_info = {
        "refdate": "minutes since 2015-01-01 00:00:00",
    }
    tim_file = Path("tim-3-columns.tim")
    mdu_parser = MagicMock(spec=MDUParser)
    mdu_parser.temperature_salinity_data = mdu_info

    def test_sources_sinks_only(self, old_forcing_file_boundary: Dict[str, str]):
        """
        The old external forcing file contains only 3 quantities `discharge_salinity_temperature_sorsin`,
        `initialsalinity`, and `initialtemperature`.

        - polyline 2*3 file `leftsor.pliz` is used to read the source and sink points.
        - tim file `tim-3-columns.tim` with 3 columns (plus the time column) the name should be the same as the
        polyline but the `tim-3-columns.tim` is mocked in the test.

        """
        converter = ExternalForcingConverter(self.path, mdu_parser=self.mdu_parser)

        with (
            patch("pathlib.Path.with_suffix", return_value=self.tim_file),
            patch(
                "hydrolib.tools.extforce_convert.main_converter.ExternalForcingConverter._update_fm_model"
            ),
        ):
            ext_model, inifield_model, structure_model = converter.update()

        self._compare(ext_model, inifield_model, structure_model)

    def test_sources_sinks_with_fm(self, old_forcing_file_boundary: Dict[str, str]):
        """
        The old external forcing file contains only 3 quantities `discharge_salinity_temperature_sorsin`,
        `initialsalinity`, and `initialtemperature`.

        - polyline 2*3 file `leftsor.pliz` is used to read the source and sink points.
        - tim file `tim-3-columns.tim` with 3 columns (plus the time column) the name should be the same as the
        polyline but the `tim-3-columns.tim` is mocked in the test.

        """
        self.mdu_parser.temperature_salinity_data["salinity"] = True
        self.mdu_parser.temperature_salinity_data["temperature"] = True

        converter = ExternalForcingConverter(self.path, mdu_parser=self.mdu_parser)

        with (
            patch("pathlib.Path.with_suffix", return_value=self.tim_file),
            patch(
                "hydrolib.tools.extforce_convert.main_converter.ExternalForcingConverter._update_fm_model"
            ),
        ):
            ext_model, inifield_model, structure_model = converter.update()

        self._compare(ext_model, inifield_model, structure_model)

    @staticmethod
    def _compare(ext_model, inifield_model, structure_model):
        # all the quantities in the old external file are initial conditions
        # check that all the quantities (3) were converted to initial conditions
        num_quantities = 1
        assert len(ext_model.sourcesink) == num_quantities
        # no parameters or any other structures, lateral or meteo data
        assert len(inifield_model.parameter) == 0
        assert len(ext_model.lateral) == 0
        assert len(ext_model.meteo) == 0
        assert len(structure_model.structure) == 0
        assert len(inifield_model.initial) == 2
        quantities = ext_model.sourcesink
        quantities[0].name = "discharge_salinity_temperature_sorsin"
