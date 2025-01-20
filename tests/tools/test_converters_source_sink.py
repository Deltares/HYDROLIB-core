from pathlib import Path
from unittest.mock import patch

import pytest

from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.tools.ext_old_to_new.converters import SourceSinkConverter


class TestParseTimFileForSourceSink:
    time_file_full = Path("tests/data/input/source-sink/leftsor.tim")

    @pytest.mark.parametrize(
        "tim_file, ext_file_quantity_list, expected_data",
        [
            # The tim file has 4 columns (plus the time column), and the list of ext quantities has 4 quantities.
            pytest.param(
                time_file_full,
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
                time_file_full,
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
    def test_parse_tim_model(self, tim_file, ext_file_quantity_list, expected_data):
        converter = SourceSinkConverter()

        if expected_data is None:
            with pytest.raises(ValueError):
                converter.parse_tim_model(tim_file, ext_file_quantity_list)
        else:
            time_series_data = converter.parse_tim_model(
                tim_file, ext_file_quantity_list
            )
            data = time_series_data.as_dataframe().to_dict(orient="list")
            assert data == expected_data

    @pytest.mark.parametrize(
        "tim_file, ext_file_quantity_list, mdu_quantities, expected_data",
        [
            pytest.param(
                time_file_full,
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
                time_file_full,
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
                time_file_full,
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
                time_file_full,
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
                time_file_full,
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
        self, tim_file, ext_file_quantity_list, mdu_quantities, expected_data
    ):
        converter = SourceSinkConverter()

        time_series_data = converter.parse_tim_model(
            tim_file, ext_file_quantity_list, **mdu_quantities
        )
        data = time_series_data.as_dataframe().to_dict(orient="list")
        assert data == expected_data


class TestSourceSinkConverter:

    def test_default(self):
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
        converter = SourceSinkConverter()
        converter.root_dir = "tests/data/input/source-sink"
        new_quantity_block = converter.convert(forcing, ext_file_other_quantities)

        assert new_quantity_block.zsink == [-4.2]
        assert new_quantity_block.zsource == [-3]

        # check the converted bc_forcing
        bc_forcing = new_quantity_block.bc_forcing
        forcing_bases = bc_forcing.forcing
        assert [forcing_bases[i].quantityunitpair[1].quantity for i in range(4)] == [
            "discharge",
            "salinitydelta",
            "temperaturedelta",
            "initialtracer_anyname",
        ]
        assert [forcing_bases[i].quantityunitpair[1].unit for i in range(4)] == [
            "m3/s",
            "ppt",
            "C",
            "Unknown",
        ]
        # check the values of the data block
        # initialtracer_anyname
        assert forcing_bases[3].datablock[1] == [4.0, 4.0, 4.0, 4.0, 4.0]
        # temperature
        assert forcing_bases[2].datablock[1] == [3.0, 3.0, 3.0, 3.0, 3.0]
        # salinity
        assert forcing_bases[1].datablock[1] == [2.0, 2.0, 2.0, 2.0, 2.0]
        # discharge
        assert forcing_bases[0].datablock[1] == [1.0, 1.0, 1.0, 1.0, 1.0]

    def test_4_5_columns_polyline(self):
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
        converter = SourceSinkConverter()
        converter.root_dir = "tests/data/input/source-sink"
        tim_file = Path("leftsor.tim")
        with patch("pathlib.Path.with_suffix", return_value=tim_file):
            new_quantity_block = converter.convert(forcing, ext_file_other_quantities)

        assert new_quantity_block.zsink == [-4.2, -5.35]
        assert new_quantity_block.zsource == [-3, -2.90]

        # check the converted bc_forcing
        bc_forcing = new_quantity_block.bc_forcing
        forcing_bases = bc_forcing.forcing
        assert [forcing_bases[i].quantityunitpair[1].quantity for i in range(4)] == [
            "discharge",
            "salinitydelta",
            "temperaturedelta",
            "initialtracer_anyname",
        ]
        assert [forcing_bases[i].quantityunitpair[1].unit for i in range(4)] == [
            "m3/s",
            "ppt",
            "C",
            "Unknown",
        ]
        # check the values of the data block
        # initialtracer_anyname
        assert forcing_bases[3].datablock[1] == [4.0, 4.0, 4.0, 4.0, 4.0]
        # temperature
        assert forcing_bases[2].datablock[1] == [3.0, 3.0, 3.0, 3.0, 3.0]
        # salinity
        assert forcing_bases[1].datablock[1] == [2.0, 2.0, 2.0, 2.0, 2.0]
        # discharge
        assert forcing_bases[0].datablock[1] == [1.0, 1.0, 1.0, 1.0, 1.0]

    def test_no_temperature_no_salinity(self):
        """
        The test case is based on the assumptions of the default test plus the following changes:

        - The timfile has only two columns (plus the time column), and the list of ext quantities has only two quantities.
        ```


        - The tim file file has the following structure:
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

        converter = SourceSinkConverter()
        converter.root_dir = "tests/data/input/source-sink"

        tim_file = Path("no_temperature_no_salinity.tim")
        with patch("pathlib.Path.with_suffix", return_value=tim_file):
            new_quantity_block = converter.convert(forcing, ext_file_other_quantities)

        assert new_quantity_block.zsink == [-4.2]
        assert new_quantity_block.zsource == [-3]
        # check the converted bc_forcing
        bc_forcing = new_quantity_block.bc_forcing
        forcing_bases = bc_forcing.forcing
        assert [forcing_bases[i].quantityunitpair[1].quantity for i in range(2)] == [
            "discharge",
            "initialtracer_anyname",
        ]
        assert [forcing_bases[i].quantityunitpair[1].unit for i in range(2)] == [
            "m3/s",
            "Unknown",
        ]
        # check the values of the data block
        # initialtracer_anyname
        assert forcing_bases[1].datablock[1] == [4.0, 4.0, 4.0, 4.0, 4.0]
        # discharge
        assert forcing_bases[0].datablock[1] == [1.0, 1.0, 1.0, 1.0, 1.0]
