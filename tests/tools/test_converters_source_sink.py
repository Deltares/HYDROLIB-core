from pathlib import Path
from typing import Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

from hydrolib.core.dflowfm.ext.models import ExtModel, SourceSink, ForcingModel
from hydrolib.core.dflowfm.extold.models import (
    ExtOldForcing,
    ExtOldModel,
    ExtOldQuantity,
)
from hydrolib.tools.extforce_convert.converters import SourceSinkConverter
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser

tim_file = Path("tests/data/input/source-sink/leftsor.tim")


@pytest.fixture
def converter(source_sink_dir: Path, mdu_parser_mock: MagicMock) -> SourceSinkConverter:
    converter = SourceSinkConverter(mdu_parser=mdu_parser_mock)
    converter.root_dir = source_sink_dir
    return converter


@pytest.fixture
def time_file_full() -> Path:
    return tim_file


@pytest.fixture
def mdu_parser_mock() -> MagicMock:
    mock = MagicMock(spec=MDUParser)
    mock.temperature_salinity_data = {"refdate": "minutes since 2015-01-01 00:00:00"}
    mock.get_keyword.return_value = None
    mock.is_relative_to_parent = False
    mock.mdu_path = Path("tests/data/input/source-sink/mdu.mdu")
    return mock


@pytest.mark.parametrize(
    "tim_file, ext_file_quantity_list, active_substance_names, expected_data",
    [
        # The tim file has 4 columns (plus the time column), and the list of ext quantities has 4 quantities.
        pytest.param(
            tim_file,
            [
                "discharge",
                "temperature",
                "salinity",
                "initialtracer_anyname",
            ],
            None,
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="test_default_all_quantities_comes_from_ext",
        ),
        # The tim file has 4 columns (plus the time column), but the list of ext quantities has only 3 quantities.
        pytest.param(
            tim_file,
            ["discharge", "temperature", "salinity"],
            None,
            None,
            id="test_list_of_ext_quantities_tim_column_mismatch",
        ),
        # The tim file has 3 columns (plus the time column), but the list of ext quantities has only 3 quantities.
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_or_salinity.tim"),
            ["discharge", "salinity", "initialtracer_anyname"],
            None,
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="no_temperature",
        ),
        # The tim file has 3 columns (plus the time column), and the list of ext quantities has only 3 quantities.
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_or_salinity.tim"),
            ["discharge", "temperature", "initialtracer_anyname"],
            None,
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="no_salinity",
        ),
        # The tim file has 2 columns (plus the time column), and the list of ext quantities has only 2 quantities.
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_no_salinity.tim"),
            ["discharge", "initialtracer_anyname"],
            None,
            {
                "sourcesink_discharge": [1.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="no_temperature_no_salinity",
        ),
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_no_salinity.tim"),
            ["sourcesink_discharge", "initialtracer_anyname", "initialtracer_anyname"],
            None,
            {
                "sourcesink_discharge": [1.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="2_unique_quantities_in_ext_file_list",
        ),
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_no_salinity.tim"),
            [
                "sourcesink_discharge",
                "temperature",
                "initialtracer_anyname",
                "initialtracer_anyname",
            ],
            None,
            None,
            id="3_unique_quantities_in_ext_file_list_missing_column_in_tim",
        ),
        # An empty substance list behaves like None: no extra columns are expected.
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_no_salinity.tim"),
            ["discharge", "initialtracer_anyname"],
            [],
            {
                "sourcesink_discharge": [1.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="empty_active_substances",
        ),
        # One active substance appends one column after discharge/salinity/temperature.
        # leftsor.tim has 4 columns: discharge, salinity, temperature, substance_a.
        pytest.param(
            tim_file,
            ["discharge", "salinity", "temperature"],
            ["substance_a"],
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "substance_a": [4.0] * 5,
            },
            id="one_active_substance",
        ),
        # Two active substances append two columns, in the order given.
        # leftsor.tim has 4 columns: discharge, salinity, substance_a, substance_b.
        pytest.param(
            tim_file,
            ["discharge", "salinity"],
            ["substance_a", "substance_b"],
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "substance_a": [3.0] * 5,
                "substance_b": [4.0] * 5,
            },
            id="two_active_substances",
        ),
        # Substances that push the quantity count past the tim columns raise a ValueError.
        # leftsor.tim already fills its 4 columns without the extra substance.
        pytest.param(
            tim_file,
            ["discharge", "salinity", "temperature", "initialtracer_anyname"],
            ["substance_a"],
            None,
            id="active_substance_exceeds_tim_columns",
        ),
    ],
)
def test_parse_tim_model(
    converter: SourceSinkConverter,
    tim_file,
    ext_file_quantity_list,
    active_substance_names,
    expected_data,
):
    if expected_data is None:
        with pytest.raises(ValueError):
            converter.parse_tim_model(
                tim_file, ext_file_quantity_list, active_substance_names
            )
    else:
        time_series_data = converter.parse_tim_model(
            tim_file, ext_file_quantity_list, active_substance_names
        )
        data = time_series_data.as_dataframe().to_dict(orient="list")
        assert data == expected_data


def test_filter_source_sink_quantities():
    """Ignore-prefixed quantities are dropped; all others keep their order."""
    quantities = [
        "sourcesink_discharge",
        "initialtracer_anyname",
        "salinity",
        "initialsedfrac_mud",
        "temperature",
    ]
    assert SourceSinkConverter.filter_source_sink_quantities(quantities) == [
        "sourcesink_discharge",
        "salinity",
        "temperature",
    ]


@pytest.mark.parametrize(
    "tim_file, ext_file_quantity_list, mdu_quantities, expected_data",
    [
        pytest.param(
            tim_file,
            ["sourcesink_discharge", "initialtracer_anyname"],
            {"salinity": True, "temperature": True},
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="all_quantities_from_mdu",
        ),
        pytest.param(
            tim_file,
            ["sourcesink_discharge", "temperature", "initialtracer_anyname"],
            {"salinity": True, "temperature": False},
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="temp_from_ext_salinity_from_mdu",
        ),
        pytest.param(
            tim_file,
            ["sourcesink_discharge", "salinity", "initialtracer_anyname"],
            {"salinity": False, "temperature": True},
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="temp_from_mdu_salinity_from_ext",
        ),
        pytest.param(
            tim_file,
            ["sourcesink_discharge", "salinity", "initialtracer_anyname"],
            {"salinity": True, "temperature": True},
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="temp_salinity_from_mdu",
        ),
        pytest.param(
            tim_file,
            [
                "sourcesink_discharge",
                "salinity",
                "temperature",
                "initialtracer_anyname",
            ],
            {"salinity": False, "temperature": True},
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="temp_from_mdu_temp_salinity_from_ext",
        ),
        pytest.param(
            tim_file,
            [
                "sourcesink_discharge",
                "salinity",
                "temperature",
                "initialtracer_anyname",
                "initialtracer_anyname",
            ],
            {"salinity": False, "temperature": True},
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "initialtracer_anyname": [4.0] * 5,
            },
            id="duplicate_quantities_in_ext_list",
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
        "salinity",
        "temperature",
        "initialtracer_anyname",
    ]

    assert all(hasattr(new_quantity_block, quantity) for quantity in quantity_list)
    # all the quantities are stored in discharge attribute (one forcing model that has all the Forcings)
    # and this forcingModel is duplicated in the sourcesink_salinity, sourcesink_temperature, and initialtracer_anyname
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

    def test_default(self, converter: SourceSinkConverter, source_sink_dir: Path):
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
        location_file = (source_sink_dir / "leftsor.pliz").resolve()
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.DischargeSalinityTemperatureSorSin,
            filename=location_file,
            filetype=9,
            method="1",
            operand="override",
            area=1.0,
        )

        ext_file_other_quantities = [
            "salinity",
            "temperature",
            "initialtracer_anyname",
        ]

        new_quantity_block = converter.convert(forcing, ext_file_other_quantities)

        assert new_quantity_block.zsink == [-4.2]
        assert new_quantity_block.zsource == [-3]
        assert converter.legacy_files == [location_file.with_suffix(".tim")]

        # check the converted bc_forcing
        compare_data(new_quantity_block)

    @pytest.mark.parametrize(
        "area", [None, 2.1, 0.0], ids=["Unset", "Area = 2.1", "Area = 0.0"]
    )
    def test_sourcesink_area_is_set(
        self,
        converter: SourceSinkConverter,
        source_sink_dir: Path,
        area: Optional[float],
    ):
        """Test if the area is set in the forcing, it is used in the converted model."""
        location_file = (source_sink_dir / "leftsor.pliz").resolve()
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.DischargeSalinityTemperatureSorSin,
            filename=location_file,
            filetype=9,
            method="1",
            operand="override",
            area=area,
        )

        ext_file_other_quantities = [
            "salinity",
            "temperature",
            "initialtracer_anyname",
        ]

        new_quantity_block = converter.convert(forcing, ext_file_other_quantities)

        assert new_quantity_block.zsink == [-4.2]
        assert new_quantity_block.zsource == [-3]
        assert converter.legacy_files == [location_file.with_suffix(".tim")]
        if area is None:
            assert new_quantity_block.area is None
        else:
            assert new_quantity_block.area == area

        # check the converted bc_forcing
        compare_data(new_quantity_block)

    def test_4_5_columns_polyline(
        self, converter: SourceSinkConverter, source_sink_dir: Path
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
        location_file = source_sink_dir / "leftsor-5-columns.pliz"
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.DischargeSalinityTemperatureSorSin,
            filename=location_file,
            filetype=9,
            method="1",
            operand="override",
            area=1.0,
        )

        ext_file_other_quantities = [
            "salinity",
            "temperature",
            "initialtracer_anyname",
        ]
        _real_with_suffix = Path.with_suffix  # Save the real method before patching

        def make_side_effect():
            call_count = {"count": 0}  # mutable counter in closure

            def side_effect(self, suffix):
                if call_count["count"] == 0:
                    call_count["count"] += 1
                    return tim_file
                return _real_with_suffix(self, suffix)

            return side_effect

        tim_file = source_sink_dir / "leftsor.tim"
        with patch("pathlib.Path.with_suffix", new=make_side_effect()):
            new_quantity_block = converter.convert(forcing, ext_file_other_quantities)

        assert new_quantity_block.zsink == [-4.2, -5.35]
        assert new_quantity_block.zsource == [-3, -2.90]

        # check the converted bc_forcing
        compare_data(new_quantity_block)

    def test_no_temperature_no_salinity(
        self, converter: SourceSinkConverter, source_sink_dir: Path
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
            filename=str(source_sink_dir / "leftsor.pliz"),
            filetype=9,
            method="1",
            operand="override",
            area=1.0,
        )

        ext_file_other_quantities = [
            "initialtracer_anyname",
        ]

        tim_file = source_sink_dir / "no_temperature_no_salinity.tim"
        with patch("pathlib.Path.with_suffix", return_value=tim_file):
            new_quantity_block = converter.convert(forcing, ext_file_other_quantities)

        assert new_quantity_block.zsink == [-4.2]
        assert new_quantity_block.zsource == [-3]

        validation_list = ["sourcesink_discharge", "initialtracer_anyname"]

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


class TestNoDeltaSuffixInConverter:
    """Regression tests ensuring 'Delta' is not appended to quantity names.

    Loads both forcings from sources_no_delta_suffix.ext (the old-format ext file from the
    2cols_old_format scenario that originally triggered the bug):
      - forcing[0]: left_no_delta_suffix.pli / left_no_delta_suffix.tim  — 2 columns: discharge + salinity
      - forcing[1]: right_no_delta_suffix.pli / right_no_delta_suffix.tim — 2 columns: discharge + temperature

    After the fix, both the .ext file field keys and the .bc file quantity
    column names must use `salinity`/`temperature` without the 'Delta' suffix.
    """

    @pytest.mark.parametrize(
        "forcing_idx, ext_quantities, expected_bc_quantity",
        [
            (0, ["salinity"], "sourcesink_salinity"),
            (1, ["temperature"], "sourcesink_temperature"),
        ],
        ids=["salinity", "temperature"],
    )
    def test_bc_quantities_have_no_delta_suffix(
        self,
        converter: SourceSinkConverter,
        source_sink_dir: Path,
        forcing_idx: int,
        ext_quantities: list,
        expected_bc_quantity: str,
    ):
        """The .bc file quantity names must not contain 'delta'.

        Test scenario:
            Both forcings in sources_no_delta_suffix.ext must produce quantity column names
            without the 'Delta' suffix (`sourcesink_salinity` / `sourcesink_temperature`).
        """
        old_ext = ExtOldModel(source_sink_dir / "sources_no_delta_suffix.ext")
        forcing = old_ext.forcing[forcing_idx]

        new_quantity_block = converter.convert(forcing, ext_quantities)

        bc_quantities = [
            f.quantityunitpair[1].quantity for f in new_quantity_block.discharge.forcing
        ]
        assert expected_bc_quantity in bc_quantities
        assert not any(
            "delta" in q.lower() for q in bc_quantities
        ), f"No quantity name should contain 'delta', got: {bc_quantities}"

    @pytest.mark.parametrize(
        "forcing_idx, ext_quantities, expected_field",
        [
            (0, ["salinity"], "salinity"),
            (1, ["temperature"], "temperature"),
        ],
        ids=["salinity", "temperature"],
    )
    def test_ext_fields_have_no_delta_suffix(
        self,
        converter: SourceSinkConverter,
        source_sink_dir: Path,
        tmp_path: Path,
        forcing_idx: int,
        ext_quantities: list,
        expected_field: str,
    ):
        """Saved .ext file uses `salinity`/`temperature`, not the Delta variants.

        Test scenario:
            When each converted SourceSink block is serialised to disk via
            ExtModel, the key written in the [SourceSink] section must not
            carry the 'Delta' suffix.
        """
        old_ext = ExtOldModel(source_sink_dir / "sources_no_delta_suffix.ext")
        forcing = old_ext.forcing[forcing_idx]

        new_quantity_block = converter.convert(forcing, ext_quantities)

        ext = ExtModel(sourcesink=[new_quantity_block])
        ext_path = tmp_path / "sources_no_delta_suffix.ext"
        ext.save(ext_path)

        content = ext_path.read_text(encoding="utf-8")
        assert (
            f"{expected_field}delta" not in content.lower()
        ), f"Serialized ext must not contain '{expected_field}Delta'"
        assert (
            expected_field in content
        ), f"Serialized ext should contain '{expected_field}' as a field key"

    @pytest.mark.parametrize(
        "tim_file_name, ext_quantities, expected_quantity",
        [
            (
                "left_no_delta_suffix.tim",
                ["discharge", "salinity"],
                "sourcesink_salinity",
            ),
            (
                "right_no_delta_suffix.tim",
                ["discharge", "temperature"],
                "sourcesink_temperature",
            ),
        ],
        ids=["salinity", "temperature"],
    )
    def test_tim_model_quantities_have_no_delta_suffix(
        self,
        converter: SourceSinkConverter,
        source_sink_dir: Path,
        tim_file_name: str,
        ext_quantities: list,
        expected_quantity: str,
    ):
        """parse_tim_model returns quantity names without 'delta' suffix.

        Test scenario:
            Parsing either the salinity or temperature two-column tim file must
            yield quantity names without 'Delta' (`sourcesink_salinity` /
            `sourcesink_temperature`).
        """
        tim_model = converter.parse_tim_model(
            source_sink_dir / tim_file_name, ext_quantities
        )
        assert expected_quantity in tim_model.quantities_names
        assert not any(
            "delta" in q.lower() for q in tim_model.quantities_names
        ), f"No quantity name should contain 'delta', got: {tim_model.quantities_names}"


class TestMainConverter:
    path = "tests/data/input/source-sink/source-sink.ext"
    tim_file = Path("tests/data/input/source-sink/tim-3-columns.tim")

    def test_sources_sinks_only(
        self, mdu_parser_mock: MagicMock, old_forcing_file_boundary: dict[str, str]
    ):
        """
        The old external forcing file contains only 3 quantities `discharge_salinity_temperature_sorsin`,
        `initialsalinity`, and `initialtemperature`.

        - polyline 2*3 file `leftsor.pliz` is used to read the source and sink points.
        - tim file `tim-3-columns.tim` with 3 columns (plus the time column) the name should be the same as the
        polyline but the `tim-3-columns.tim` is mocked in the test.

        """
        converter = ExternalForcingConverter(self.path, mdu_parser=mdu_parser_mock)

        with (
            patch("pathlib.Path.with_suffix", return_value=self.tim_file),
            patch(
                "hydrolib.tools.extforce_convert.main_converter.ExternalForcingConverter._update_mdu_file"
            ),
        ):
            ext_model, inifield_model, structure_model = converter.update()

        self._compare(ext_model, inifield_model, structure_model)

    def test_sources_sinks_with_fm(
        self, mdu_parser_mock: MagicMock, old_forcing_file_boundary: Dict[str, str]
    ):
        """
        The old external forcing file contains only 3 quantities `discharge_salinity_temperature_sorsin`,
        `initialsalinity`, and `initialtemperature`, with salinity and temperature active in the FM model.

        - polyline 2*3 file `leftsor.pliz` is used to read the source and sink points.
        - tim file `tim-3-columns.tim` with 3 columns (plus the time column) the name should be the same as the
        polyline but the `tim-3-columns.tim` is mocked in the test.

        """
        mdu_parser_mock.temperature_salinity_data.update(
            {"salinity": True, "temperature": True}
        )
        converter = ExternalForcingConverter(self.path, mdu_parser=mdu_parser_mock)

        with (
            patch("pathlib.Path.with_suffix", return_value=self.tim_file),
            patch(
                "hydrolib.tools.extforce_convert.main_converter.ExternalForcingConverter._update_mdu_file"
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


class TestConvertSourceSinkWithSubstanceFile:

    def test_simple_model(self):
        mdu_file = Path(
            "tests/data/input/source-sink/substance-file/with_substance.mdu"
        )
        file_names = "with_substances"
        converter = ExternalForcingConverter.from_mdu(mdu_file, debug=True)
        ext_model, _, _ = converter.update()
        source_sink = ext_model.sourcesink[0]
        assert isinstance(source_sink, SourceSink)
        assert all(
            [
                isinstance(model, ForcingModel)
                for model in [
                    source_sink.discharge,
                    source_sink.salinity,
                    source_sink.temperature,
                ]
            ]
        )
        assert source_sink.discharge.filepath == Path(file_names).with_suffix(".bc")
        # sub_1 and sub_2 are assigned dynamically
        assert all([hasattr(source_sink, sub_name) for sub_name in ["sub_1", "sub_2"]])
        forcings = source_sink.sub_1
        assert len(forcings.forcing) == 5

        # Verify that the substance concentration units from the .sub file are
        # correctly propagated to the .bc quantity-unit pairs.
        sub_1_forcing = next(
            f
            for f in source_sink.sub_1.forcing
            if f.quantityunitpair[1].quantity == "sub_1"
        )
        sub_2_forcing = next(
            f
            for f in source_sink.sub_2.forcing
            if f.quantityunitpair[1].quantity == "sub_2"
        )
        assert sub_1_forcing.quantityunitpair[1].unit == "(gC/m3)"
        assert sub_2_forcing.quantityunitpair[1].unit == "(gN/m3)"


class TestSourceSinkConverterEdgeCases:
    """Tests for SourceSinkConverter edge cases and error handling."""

    def test_convert_raises_when_mdu_parser_is_none(self):
        """Test that convert() raises ValueError when mdu_parser is None.

        Test scenario:
            Constructing a SourceSinkConverter without an mdu_parser and then calling
            convert() should raise a clear ValueError.
        """
        converter = SourceSinkConverter(mdu_parser=None)
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.DischargeSalinityTemperatureSorSin,
            filename="tests/data/input/source-sink/leftsor.pliz",
            filetype=9,
            method="1",
            operand="override",
        )
        with pytest.raises(ValueError, match="MDU model is required"):
            converter.convert(forcing, [])

    def test_convert_raises_when_temperature_salinity_data_is_none(self):
        """Test that convert() raises ValueError when temperature_salinity_data is None.

        Test scenario:
            An mdu_parser that returns None for temperature_salinity_data should
            trigger a clear ValueError at convert time.
        """
        mock_parser = MagicMock(spec=MDUParser)
        mock_parser.temperature_salinity_data = None
        converter = SourceSinkConverter(mdu_parser=mock_parser)
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.DischargeSalinityTemperatureSorSin,
            filename="tests/data/input/source-sink/leftsor.pliz",
            filetype=9,
            method="1",
            operand="override",
        )
        with pytest.raises(ValueError, match="MDU model is required"):
            converter.convert(forcing, [])

    def test_active_substances_raises_for_missing_file(self):
        """Test that _active_substances raises FileNotFoundError for missing .sub file.

        Test scenario:
            When the MDU parser returns a SubstanceFile path that does not exist on
            disk, _active_substances should raise FileNotFoundError with a descriptive
            message.
        """
        mock_parser = MagicMock(spec=MDUParser)
        mock_parser.get_keyword.return_value = "nonexistent.sub"
        mock_parser.mdu_path = Path("tests/data/input/source-sink/mdu.mdu")

        converter = SourceSinkConverter(mdu_parser=mock_parser)
        with pytest.raises(FileNotFoundError, match="not found"):
            converter._active_substances()

    def test_active_substances_returns_none_when_no_substance_file(self):
        """Test that _active_substances returns None when no SubstanceFile is set.

        Test scenario:
            When the MDU parser returns None for SubstanceFile, _active_substances
            should return None (no substance file configured).
        """
        mock_parser = MagicMock(spec=MDUParser)
        mock_parser.get_keyword.return_value = None
        converter = SourceSinkConverter(mdu_parser=mock_parser)
        result = converter._active_substances()
        assert result is None, f"Expected None, got {result}"

    def test_resolve_active_substances_returns_names_and_units(self):
        """Test that _resolve_active_substances derives the names and unit map.

        Test scenario:
            When the MDU references a substance file with two active substances,
            the method returns their names as a list and a name -> concentration-unit
            mapping.
        """
        mock_parser = MagicMock(spec=MDUParser)
        mock_parser.get_keyword.return_value = "sub-file.sub"
        mock_parser.mdu_path = Path(
            "tests/data/input/source-sink/substance-file/with_substance.mdu"
        )
        converter = SourceSinkConverter(mdu_parser=mock_parser)

        names, units = converter._resolve_active_substances()

        assert names == ["sub_1", "sub_2"], f"Got names: {names}"
        assert units == {
            "sub_1": "(gC/m3)",
            "sub_2": "(gN/m3)",
        }, f"Got units: {units}"

    def test_resolve_active_substances_without_substance_file(self):
        """Test that _resolve_active_substances returns (None, {}) with no substance file.

        Test scenario:
            When the MDU parser returns None for SubstanceFile, the method returns
            None for the names and an empty units mapping, in lockstep.
        """
        mock_parser = MagicMock(spec=MDUParser)
        mock_parser.get_keyword.return_value = None
        converter = SourceSinkConverter(mdu_parser=mock_parser)

        names, units = converter._resolve_active_substances()

        assert names is None, f"Expected None names, got {names}"
        assert units == {}, f"Expected empty units, got {units}"


class TestCorrectSubstanceUnits:
    """Tests for SourceSinkConverter._correct_substance_units."""

    def test_replaces_placeholder_units_with_substance_units(self):
        """Test that placeholder units are replaced with substance concentration units.

        Test scenario:
            Given quantity names with 'sourcesink_' prefix and a substance_units map,
            the method should replace the placeholder '-' with the actual unit.
        """
        units = ["m3/s", "-", "-"]
        quantities_names = [
            "sourcesink_discharge",
            "sourcesink_sub_1",
            "sourcesink_sub_2",
        ]
        substance_units = {"sub_1": "(gC/m3)", "sub_2": "(gN/m3)"}

        result = SourceSinkConverter._correct_substance_units(
            units, quantities_names, substance_units
        )
        assert result == ["m3/s", "(gC/m3)", "(gN/m3)"], f"Got {result}"

    def test_returns_units_unchanged_when_substance_units_is_none(self):
        """Test that units are returned unchanged when substance_units is None.

        Test scenario:
            When no substance_units mapping is provided, the original units list
            should be returned as-is.
        """
        units = ["m3/s", "-", "-"]
        quantities_names = [
            "sourcesink_discharge",
            "sourcesink_sub_1",
            "sourcesink_sub_2",
        ]

        result = SourceSinkConverter._correct_substance_units(
            units, quantities_names, None
        )
        assert result == units, f"Expected unchanged units, got {result}"

    def test_returns_units_unchanged_when_substance_units_is_empty(self):
        """Test that units are returned unchanged when substance_units is empty dict.

        Test scenario:
            An empty substance_units dict is falsy, so units should pass through.
        """
        units = ["m3/s", "1e-3", "degC"]
        quantities_names = [
            "sourcesink_discharge",
            "sourcesink_salinitydelta",
            "sourcesink_temperaturedelta",
        ]

        result = SourceSinkConverter._correct_substance_units(
            units, quantities_names, {}
        )
        assert result == units, f"Expected unchanged units, got {result}"

    def test_keeps_original_unit_when_name_not_in_substance_units(self):
        """Test that non-substance quantities keep their original unit.

        Test scenario:
            Quantities that are not in the substance_units map (e.g. discharge,
            salinity) should keep their original unit values.
        """
        units = ["m3/s", "1e-3", "-"]
        quantities_names = [
            "sourcesink_discharge",
            "sourcesink_salinitydelta",
            "sourcesink_sub_1",
        ]
        substance_units = {"sub_1": "(gC/m3)"}

        result = SourceSinkConverter._correct_substance_units(
            units, quantities_names, substance_units
        )
        assert result == ["m3/s", "1e-3", "(gC/m3)"], f"Got {result}"
