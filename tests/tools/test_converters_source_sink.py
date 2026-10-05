from pathlib import Path
from typing import Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

from hydrolib.core.dflowfm.bc.models import TimeInterpolation
from hydrolib.core.dflowfm.ext.models import ExtModel, SourceSink, ForcingModel
from hydrolib.core.dflowfm.extold.models import (
    ExtOldForcing,
    ExtOldModel,
    ExtOldQuantity,
)
from hydrolib.tools.extforce_convert import converters as converters_module
from hydrolib.tools.extforce_convert.converters import (
    SourceSinkConverter,
    TimQuantityNamesBuilder,
)
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
                "tracerbndanyname",
            ],
            None,
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "sourcesink_traceranyname": [4.0] * 5,
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
            ["discharge", "salinity", "tracerbndanyname"],
            None,
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [3.0] * 5,
                "sourcesink_traceranyname": [4.0] * 5,
            },
            id="no_temperature",
        ),
        # The tim file has 3 columns (plus the time column), and the list of ext quantities has only 3 quantities.
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_or_salinity.tim"),
            ["discharge", "temperature", "tracerbndanyname"],
            None,
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "sourcesink_traceranyname": [4.0] * 5,
            },
            id="no_salinity",
        ),
        # The tim file has 2 columns (plus the time column), and the list of ext quantities has only 2 quantities.
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_no_salinity.tim"),
            ["discharge", "tracerbndanyname"],
            None,
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_traceranyname": [4.0] * 5,
            },
            id="no_temperature_no_salinity",
        ),
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_no_salinity.tim"),
            ["sourcesink_discharge", "tracerbndanyname", "tracerbndanyname"],
            None,
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_traceranyname": [4.0] * 5,
            },
            id="2_unique_quantities_in_ext_file_list",
        ),
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_no_salinity.tim"),
            [
                "sourcesink_discharge",
                "temperature",
                "tracerbndanyname",
                "tracerbndanyname",
            ],
            None,
            None,
            id="3_unique_quantities_in_ext_file_list_missing_column_in_tim",
        ),
        # An empty substance list behaves like None: no extra columns are expected.
        pytest.param(
            Path("tests/data/input/source-sink/no_temperature_no_salinity.tim"),
            ["discharge", "tracerbndanyname"],
            [],
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_traceranyname": [4.0] * 5,
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
                "sourcesink_tracersubstance_a": [4.0] * 5,
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
                "sourcesink_tracersubstance_a": [3.0] * 5,
                "sourcesink_tracersubstance_b": [4.0] * 5,
            },
            id="two_active_substances",
        ),
        # Substances that push the quantity count past the tim columns raise a ValueError.
        # leftsor.tim already fills its 4 columns without the extra substance.
        pytest.param(
            tim_file,
            ["discharge", "salinity", "temperature", "tracerbndanyname"],
            ["substance_a"],
            None,
            id="active_substance_exceeds_tim_columns",
        ),
        # regression: `tracerbndsubstance_a` duplicates the active `substance_a`, counted once
        pytest.param(
            tim_file,
            ["discharge", "salinity", "temperature", "tracerbndsubstance_a"],
            ["substance_a"],
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "sourcesink_tracersubstance_a": [4.0] * 5,
            },
            id="substance_and_tracerbnd_not_double_counted",
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


@pytest.mark.parametrize(
    "quantity, expected",
    [
        ("tracerbndIM1", "IM1"),  # tracer boundary prefix stripped
        ("sedfracbndMud", "Mud"),  # sediment-fraction boundary prefix stripped
        ("TracerBndIM1", "IM1"),  # prefix match is case-insensitive
        ("discharge", "discharge"),  # no known prefix -> returned unchanged
    ],
)
def test_substance_name_from_quantity(quantity, expected):
    """The bare substance name is recovered by stripping any known source/sink prefix."""
    assert TimQuantityNamesBuilder._substance_name_from_quantity(quantity) == expected


@pytest.mark.parametrize(
    "quantity, expected",
    [
        ("tracerbndIM1", "tracer"),
        ("initialtracerIM1", "tracer"),
        ("sedfracbndMud", "sedfrac"),
        ("InitialSedFracMud", "sedfrac"),
    ],
)
def test_role_prefix(quantity, expected):
    assert TimQuantityNamesBuilder._role_prefix(quantity) == expected


@pytest.mark.parametrize(
    "quantity_name, expected",
    [
        ("sourcesink_tracerOXY", "OXY"),
        ("sourcesink_sedfracMud", "Mud"),
        ("sourcesink_discharge", "discharge"),
        ("sourcesink_tracerDetC", "DetC"),
    ],
)
def test_bare_constituent_name(quantity_name, expected):
    assert SourceSinkConverter._bare_constituent_name(quantity_name) == expected


def test_build_quantities_names_keeps_tracer_and_sedfrac_with_the_same_name():
    """A tracer and a sediment fraction that share a bare name are different constituents.

    The kernel keeps tracers and sediment fractions in separate constituent groups, so
    `tracerbndX` and `sedfracbndX` each keep their column, while `initialtracerX` and the
    substance `X` still collapse into the one `tracerX`.
    """
    names = TimQuantityNamesBuilder(
        ext_file_quantity_list=["tracerbndX", "sedfracbndX", "initialtracerX"],
        active_substance_names=["X"],
        mdu_quantities={},
    ).build()

    assert names == [
        "sourcesink_discharge",
        "sourcesink_tracerX",
        "sourcesink_sedfracX",
    ]


def test_substance_name_from_quantity_strips_longest_prefix():
    """When prefixes overlap, the longest one is stripped, not the first in tuple order.

    With an overlapping set ordered `("tracer", "tracerbnd")`, a first-match strategy
    would strip `tracer` from `tracerbndIM1` and wrongly yield `bndIM1`. The longest
    match yields `IM1`.
    """
    overlapping_prefixes = ("tracer", "tracerbnd")
    with patch.object(
        converters_module,
        "SOURCE_SINKS_QUANTITIES_VALID_PREFIXES",
        overlapping_prefixes,
    ):
        assert (
            TimQuantityNamesBuilder._substance_name_from_quantity("tracerbndIM1") == "IM1"
        )


def test_build_quantities_names_dedups_substance_and_tracerbnd(
    converter: SourceSinkConverter,
):
    """An ext `tracerbnd*` quantity naming an active substance is not counted twice.

    `tracerbndIM1` resolves to active substance `IM1`; the substance file is
    authoritative, so the ext quantity is dropped and `IM1` appears exactly once,
    after discharge/salinity/temperature.
    """
    names = TimQuantityNamesBuilder(
        ext_file_quantity_list=["discharge", "salinity", "temperature", "tracerbndIM1"],
        active_substance_names=["IM1"],
        mdu_quantities={},
    ).build()

    assert names == [
        "sourcesink_discharge",
        "sourcesink_salinity",
        "sourcesink_temperature",
        "sourcesink_tracerIM1",
    ]


def test_build_quantities_names_preserves_tracer_order_with_substance(
    converter: SourceSinkConverter,
):
    """Multiple non-substance tracers keep their ext order; the substance stays last.

    With two non-substance `tracerbnd*` quantities plus an active substance, the
    deduped tracer names must keep their first-seen (ext-file) order rather than the
    non-deterministic order of a `set`, and the active substance is appended last.
    """
    names = TimQuantityNamesBuilder(
        ext_file_quantity_list=[
            "discharge",
            "salinity",
            "temperature",
            "tracerbndA",
            "tracerbndB",
            "tracerbndIM1",
        ],
        active_substance_names=["IM1"],
        mdu_quantities={},
    ).build()

    # ext prefixes are stripped, and `tracerbndIM1` dedups against the active IM1
    assert names == [
        "sourcesink_discharge",
        "sourcesink_salinity",
        "sourcesink_temperature",
        "sourcesink_tracerA",
        "sourcesink_tracerB",
        "sourcesink_tracerIM1",
    ]


def test_build_quantities_names_includes_initial_condition_prefixes(
    converter: SourceSinkConverter,
):
    """`initialtracer*` / `initialsedfrac*` contribute to the TIM tracer ordering.

    They are converted to `[Spatial]` blocks by `SpatialConverter`, but still take a slot
    in the kernel's tracer indexing (confirmed with the FM team). Each quantity
    contributes its substance name after prefix stripping; relative order is preserved.
    """
    names = TimQuantityNamesBuilder(
        ext_file_quantity_list=[
            "discharge",
            "initialtracerFoo",
            "tracerbndBar",
            "initialsedfracMud",
            "sedfracbndSilt",
        ],
        active_substance_names=None,
        mdu_quantities={},
    ).build()

    assert names == [
        "sourcesink_discharge",
        "sourcesink_tracerFoo",
        "sourcesink_tracerBar",
        "sourcesink_sedfracMud",
        "sourcesink_sedfracSilt",
    ]


def test_build_quantities_names_four_source_precedence(
    converter: SourceSinkConverter,
):
    """Tracer ordering follows the kernel's 4-source first-seen-wins precedence.

    Reproduces the scenario discussed on issue #1225 (comment-5908835061): a tracer's
    position is set by the highest-precedence source that mentions it, and lower
    sources contribute only tracers not yet seen. Precedence: inifield -> new ext ->
    old ext -> substance file.
    """
    names = TimQuantityNamesBuilder(
        ext_file_quantity_list=[
            "discharge",
            "initialtracerDetC",
            "initialtracerDetN",
            "initialtracerDetP",
            "initialtracerSi",
            "initialtracerDiat",
        ],
        active_substance_names=["IM1", "IM2", "CBOD5", "AAP", "DetSi"],
        mdu_quantities={},
        new_ext_tracer_quantities=[
            "tracerbndIM1",
            "tracerbndIM2",
            "tracerbndOXY",
            "tracerbndNH4",
            "tracerbndNO3",
            "tracerbndPO4",
            "tracerbndGreen",
        ],
        inifield_tracer_quantities=None,
    ).build()

    # new ext: IM1..Green, old ext initial*: DetC..Diat, substance file: CBOD5, AAP, DetSi
    assert names == [
        "sourcesink_discharge",
        "sourcesink_tracerIM1",
        "sourcesink_tracerIM2",
        "sourcesink_tracerOXY",
        "sourcesink_tracerNH4",
        "sourcesink_tracerNO3",
        "sourcesink_tracerPO4",
        "sourcesink_tracerGreen",
        "sourcesink_tracerDetC",
        "sourcesink_tracerDetN",
        "sourcesink_tracerDetP",
        "sourcesink_tracerSi",
        "sourcesink_tracerDiat",
        "sourcesink_tracerCBOD5",
        "sourcesink_tracerAAP",
        "sourcesink_tracerDetSi",
    ]


def test_build_quantities_names_inifield_wins_position(
    converter: SourceSinkConverter,
):
    """Inifield-file tracers hold their positions over new ext / old ext / sub.

    A substance that appears first in the inifield file keeps its early position,
    even when later sources list it in a different order.
    """
    names = TimQuantityNamesBuilder(
        ext_file_quantity_list=["discharge", "tracerbndA"],
        active_substance_names=["B", "A"],
        mdu_quantities={},
        new_ext_tracer_quantities=["tracerbndB"],
        inifield_tracer_quantities=["initialtracerA"],
    ).build()

    # inifield: A -> new ext: B -> old ext: (A already seen) -> sub: (B, A already seen).
    assert names == ["sourcesink_discharge", "sourcesink_tracerA", "sourcesink_tracerB"]


@pytest.mark.parametrize(
    "tim_file, ext_file_quantity_list, mdu_quantities, expected_data",
    [
        pytest.param(
            tim_file,
            ["sourcesink_discharge", "tracerbndanyname"],
            {"salinity": True, "temperature": True},
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "sourcesink_traceranyname": [4.0] * 5,
            },
            id="all_quantities_from_mdu",
        ),
        pytest.param(
            tim_file,
            ["sourcesink_discharge", "temperature", "tracerbndanyname"],
            {"salinity": True, "temperature": False},
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "sourcesink_traceranyname": [4.0] * 5,
            },
            id="temp_from_ext_salinity_from_mdu",
        ),
        pytest.param(
            tim_file,
            ["sourcesink_discharge", "salinity", "tracerbndanyname"],
            {"salinity": False, "temperature": True},
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "sourcesink_traceranyname": [4.0] * 5,
            },
            id="temp_from_mdu_salinity_from_ext",
        ),
        pytest.param(
            tim_file,
            ["sourcesink_discharge", "salinity", "tracerbndanyname"],
            {"salinity": True, "temperature": True},
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "sourcesink_traceranyname": [4.0] * 5,
            },
            id="temp_salinity_from_mdu",
        ),
        pytest.param(
            tim_file,
            [
                "sourcesink_discharge",
                "salinity",
                "temperature",
                "tracerbndanyname",
            ],
            {"salinity": False, "temperature": True},
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "sourcesink_traceranyname": [4.0] * 5,
            },
            id="temp_from_mdu_temp_salinity_from_ext",
        ),
        pytest.param(
            tim_file,
            [
                "sourcesink_discharge",
                "salinity",
                "temperature",
                "tracerbndanyname",
                "tracerbndanyname",
            ],
            {"salinity": False, "temperature": True},
            {
                "sourcesink_discharge": [1.0] * 5,
                "sourcesink_salinity": [2.0] * 5,
                "sourcesink_temperature": [3.0] * 5,
                "sourcesink_traceranyname": [4.0] * 5,
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
        "traceranyname",
    ]

    assert all(hasattr(new_quantity_block, quantity) for quantity in quantity_list)
    # all the quantities are stored in discharge attribute (one forcing model that has all the Forcings)
    # and this forcingModel is duplicated in the sourcesink_salinity, sourcesink_temperature, and anyname
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
    # tracerbndanyname
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
        - temperature, salinity, and tracerbndanyname are other quantities in the ext file.
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

        QUANTITY=tracerbndanyname
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
            "tracerbndanyname",
        ]

        new_quantity_block = converter.convert(forcing, ext_file_other_quantities)

        assert new_quantity_block.zsink == [-4.2]
        assert new_quantity_block.zsource == [-3]
        assert converter.legacy_files == [location_file.with_suffix(".tim")]

        # check the converted bc_forcing
        compare_data(new_quantity_block)

    def test_method_zero_uses_block_from(
        self, converter: SourceSinkConverter, source_sink_dir: Path
    ):
        """METHOD=0 converts the source/sink .bc TimeSeries to block-From (issue #1197).

        `METHOD=0` means no time interpolation (hold the last value), which maps to
        `timeInterpolation = block-From` in the generated `.bc` forcings.
        """
        location_file = (source_sink_dir / "leftsor.pliz").resolve()
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.DischargeSalinityTemperatureSorSin,
            filename=location_file,
            filetype=9,
            method=0,
            operand="override",
            area=1.0,
        )

        new_quantity_block = converter.convert(
            forcing, ["salinity", "temperature", "tracerbndanyname"]
        )

        assert all(
            f.timeinterpolation == TimeInterpolation.block_from
            for f in new_quantity_block.discharge.forcing
        )

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
            "tracerbndanyname",
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
            "tracerbndanyname",
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
            "tracerbndanyname",
        ]

        tim_file = source_sink_dir / "no_temperature_no_salinity.tim"
        with patch("pathlib.Path.with_suffix", return_value=tim_file):
            new_quantity_block = converter.convert(forcing, ext_file_other_quantities)

        assert new_quantity_block.zsink == [-4.2]
        assert new_quantity_block.zsource == [-3]

        validation_list = ["sourcesink_discharge", "sourcesink_traceranyname"]

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
        # tracerbndanyname
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
        converter = ExternalForcingConverter(
            extold_model=self.path, mdu_parser=mdu_parser_mock
        )

        with (
            patch("pathlib.Path.with_suffix", return_value=self.tim_file),
            patch(
                "hydrolib.tools.extforce_convert.main_converter.ExternalForcingConverter._update_mdu_file"
            ),
        ):
            ext_model, structure_model = converter.update()

        self._compare(ext_model, structure_model)

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
        converter = ExternalForcingConverter(
            extold_model=self.path, mdu_parser=mdu_parser_mock
        )

        with (
            patch("pathlib.Path.with_suffix", return_value=self.tim_file),
            patch(
                "hydrolib.tools.extforce_convert.main_converter.ExternalForcingConverter._update_mdu_file"
            ),
        ):
            ext_model, structure_model = converter.update()

        self._compare(ext_model, structure_model)

    @staticmethod
    def _compare(ext_model, structure_model):
        # The old external file has 1 source-sink and 2 initial conditions (initialsalinity, initialtemperature).
        # Initial conditions are converted to Spatial blocks in the ext model (new format).
        num_quantities = 1
        assert len(ext_model.sourcesink) == num_quantities
        # initialsalinity and initialtemperature are converted to Spatial blocks in the ext model
        assert len(ext_model.spatial) == 2
        # no other structures, lateral or meteo data
        assert len(ext_model.lateral) == 0
        assert len(ext_model.meteo) == 0
        assert len(structure_model.structure) == 0
        quantities = ext_model.sourcesink
        quantities[0].name = "discharge_salinity_temperature_sorsin"


class TestConvertSourceSinkWithSubstanceFile:

    def test_simple_model(self):
        mdu_file = Path(
            "tests/data/input/source-sink/substance-file/with_substance.mdu"
        )
        file_names = "with_substances"
        converter = ExternalForcingConverter.from_mdu(mdu_file, debug=True)
        ext_model, _ = converter.update()
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
        # dynamic fields carry the `tracer` role prefix (issue #1224)
        assert all(
            [hasattr(source_sink, sub_name) for sub_name in ["tracersub_1", "tracersub_2"]]
        )
        forcings = source_sink.tracersub_1
        assert len(forcings.forcing) == 5

        # Verify that the substance concentration units from the .sub file are
        # correctly propagated to the .bc quantity-unit pairs.
        sub_1_forcing = next(
            f
            for f in source_sink.tracersub_1.forcing
            if f.quantityunitpair[1].quantity == "sourcesink_tracersub_1"
        )
        sub_2_forcing = next(
            f
            for f in source_sink.tracersub_2.forcing
            if f.quantityunitpair[1].quantity == "sourcesink_tracersub_2"
        )
        assert sub_1_forcing.quantityunitpair[1].unit == "(gC/m3)"
        assert sub_2_forcing.quantityunitpair[1].unit == "(gN/m3)"

    def test_four_source_tracer_ordering_e2e(self, tmp_path: Path):
        """End-to-end: an MDU referencing all four tracer sources yields the kernel's precedence ordering.

        Builds a self-contained model whose MDU references:
        - a substance file (`TrA, TrB, TrC, TrX, TrD` — all active)
        - an inifield file (`initialtracerTrX`)
        - a pre-existing new ext file (`tracerbndTrA`, `tracerbndTrB`)
        - an old ext file (sorsin block only)

        After running the full `extforce-convert` flow the resulting `SourceSink` must
        carry its tracer columns in first-seen-wins order across the four sources
        (inifield -> new ext -> old ext -> substance file):

            TrX  (inifield wins position 1)
            TrA  (new ext, position 2 — substance file does not reorder)
            TrB  (new ext, position 3)
            TrC  (substance-file-only — contributed last)
            TrD  (substance-file-only — contributed last)
        """
        # Lay out the test model entirely in a temp directory so the test is idempotent.
        model_dir = tmp_path / "four_sources"
        model_dir.mkdir()
        bc_dir = model_dir / "bc"
        bc_dir.mkdir()

        # substance order deliberately differs from the inifield/new-ext order
        (model_dir / "subs.sub").write_text(
            "substance 'TrA' active\n"
            "   concentration-unit '(gA/m3)'\n"
            "   waste-load-unit    '-'\n"
            "end-substance\n"
            "substance 'TrB' active\n"
            "   concentration-unit '(gB/m3)'\n"
            "   waste-load-unit    '-'\n"
            "end-substance\n"
            "substance 'TrC' active\n"
            "   concentration-unit '(gC/m3)'\n"
            "   waste-load-unit    '-'\n"
            "end-substance\n"
            "substance 'TrX' active\n"
            "   concentration-unit '(gX/m3)'\n"
            "   waste-load-unit    '-'\n"
            "end-substance\n"
            "substance 'TrD' active\n"
            "   concentration-unit '(gD/m3)'\n"
            "   waste-load-unit    '-'\n"
            "end-substance\n"
        )

        # only the quantity name matters for ordering, so a placeholder data file is enough
        (model_dir / "trx_init.xyz").write_text("0.0 0.0 1.0\n")
        (model_dir / "ini_fields.ini").write_text(
            "[General]\n"
            "fileVersion = 2.00\n"
            "fileType = iniField\n"
            "\n"
            "[Initial]\n"
            "quantity = initialtracerTrX\n"
            "dataFile = trx_init.xyz\n"
            "dataFileType = sample\n"
            "interpolationMethod = triangulation\n"
        )

        # the `.bc` only needs to exist for file-model resolution
        (bc_dir / "tracers.bc").write_text(
            "[General]\nfileVersion = 1.01\nfileType = boundConds\n"
        )
        (model_dir / "tra_bnd.pli").write_text("TrA\n     1     2\n      0.0      0.0\n")
        (model_dir / "trb_bnd.pli").write_text("TrB\n     1     2\n      1.0      0.0\n")
        (model_dir / "existing_new.ext").write_text(
            "[General]\n"
            "fileVersion = 2.01\n"
            "fileType    = extForce\n"
            "\n"
            "[Boundary]\n"
            "quantity    = tracerbndTrA\n"
            "locationFile = tra_bnd.pli\n"
            "forcingFile = bc/tracers.bc\n"
            "\n"
            "[Boundary]\n"
            "quantity    = tracerbndTrB\n"
            "locationFile = trb_bnd.pli\n"
            "forcingFile = bc/tracers.bc\n"
        )

        # Old ext file: a single sorsin block, no additional tracer QUANTITYs.
        (model_dir / "sorsin.pli").write_text(
            "L1\n     1     2\n      5.0      5.0\n"
        )
        (model_dir / "sorsin.tim").write_text(
            "* Time Flow Salinity Temperature TrX TrA TrB TrC TrD\n"
            "0.0 1.0 2.0 3.0 10.0 11.0 12.0 13.0 14.0\n"
            "60.0 1.0 2.0 3.0 10.0 11.0 12.0 13.0 14.0\n"
            "120.0 1.0 2.0 3.0 10.0 11.0 12.0 13.0 14.0\n"
        )
        (model_dir / "old.ext").write_text(
            "QUANTITY     =discharge_salinity_temperature_sorsin\n"
            "FILENAME     =sorsin.pli\n"
            "FILETYPE     =9\n"
            "METHOD       =1\n"
            "OPERAND      =O\n"
        )

        # MDU wiring all four sources together.
        (model_dir / "model.mdu").write_text(
            "[General]\n"
            "Program                             = D-Flow FM\n"
            "FileVersion                         = 1.09\n"
            "\n"
            "[physics]\n"
            "Salinity                            = 1\n"
            "Temperature                         = 1\n"
            "\n"
            "[processes]\n"
            "SubstanceFile                       = subs.sub\n"
            "\n"
            "[time]\n"
            "RefDate                             = 20160101\n"
            "\n"
            "[geometry]\n"
            "IniFieldFile                        = ini_fields.ini\n"
            "\n"
            "[external forcing]\n"
            "ExtForceFile                        = old.ext\n"
            "ExtForceFileNew                     = existing_new.ext\n"
        )

        # Run the full extforce-convert flow.
        converter = ExternalForcingConverter.from_mdu(
            model_dir / "model.mdu", debug=True
        )
        ext_model, _ = converter.update()

        # tracer columns follow the 4-source precedence
        source_sink = ext_model.sourcesink[0]
        column_names = [
            f.quantityunitpair[1].quantity for f in source_sink.discharge.forcing
        ]
        assert column_names == [
            "sourcesink_discharge",
            "sourcesink_salinity",
            "sourcesink_temperature",
            "sourcesink_tracerTrX",
            "sourcesink_tracerTrA",
            "sourcesink_tracerTrB",
            "sourcesink_tracerTrC",
            "sourcesink_tracerTrD",
        ]
        # each tracer is a dynamic attribute with the `tracer` role prefix (issue #1224)
        for tracer in ("tracerTrX", "tracerTrA", "tracerTrB", "tracerTrC", "tracerTrD"):
            assert hasattr(source_sink, tracer)

    def test_old_ext_initialtracer_takes_tracer_slot_e2e(self, tmp_path: Path):
        """End-to-end: an old-ext `initialtracer*` quantity takes a TIM column slot.

        `initialtracerTrY` appears only in the old ext file (no inifield, no new ext,
        not in the substance file). It is converted to a `[Spatial]` block by the
        `SpatialConverter`, but it still defines a tracer, so it must be counted when
        ordering the source/sink TIM columns. The old ext outranks the substance file,
        so the expected tracer order is:

            TrY  (old ext)
            TrA  (substance file)
            TrB  (substance file)
        """
        model_dir = tmp_path / "old_ext_initialtracer"
        model_dir.mkdir()

        (model_dir / "subs.sub").write_text(
            "substance 'TrA' active\n"
            "   concentration-unit '(gA/m3)'\n"
            "   waste-load-unit    '-'\n"
            "end-substance\n"
            "substance 'TrB' active\n"
            "   concentration-unit '(gB/m3)'\n"
            "   waste-load-unit    '-'\n"
            "end-substance\n"
        )
        (model_dir / "try_init.xyz").write_text("0.0 0.0 1.0\n")
        (model_dir / "sorsin.pli").write_text(
            "L1\n     1     2\n      5.0      5.0\n"
        )
        (model_dir / "sorsin.tim").write_text(
            "* Time Flow Salinity Temperature TrY TrA TrB\n"
            "0.0 1.0 2.0 3.0 10.0 11.0 12.0\n"
            "60.0 1.0 2.0 3.0 10.0 11.0 12.0\n"
            "120.0 1.0 2.0 3.0 10.0 11.0 12.0\n"
        )
        (model_dir / "old.ext").write_text(
            "QUANTITY     =discharge_salinity_temperature_sorsin\n"
            "FILENAME     =sorsin.pli\n"
            "FILETYPE     =9\n"
            "METHOD       =1\n"
            "OPERAND      =O\n"
            "\n"
            "QUANTITY     =initialtracerTrY\n"
            "FILENAME     =try_init.xyz\n"
            "FILETYPE     =7\n"
            "METHOD       =5\n"
            "OPERAND      =O\n"
        )
        (model_dir / "model.mdu").write_text(
            "[General]\n"
            "Program                             = D-Flow FM\n"
            "FileVersion                         = 1.09\n"
            "\n"
            "[physics]\n"
            "Salinity                            = 1\n"
            "Temperature                         = 1\n"
            "\n"
            "[processes]\n"
            "SubstanceFile                       = subs.sub\n"
            "\n"
            "[time]\n"
            "RefDate                             = 20160101\n"
            "\n"
            "[external forcing]\n"
            "ExtForceFile                        = old.ext\n"
        )

        converter = ExternalForcingConverter.from_mdu(
            model_dir / "model.mdu", debug=True
        )
        ext_model, _ = converter.update()

        source_sink = ext_model.sourcesink[0]
        column_names = [
            f.quantityunitpair[1].quantity for f in source_sink.discharge.forcing
        ]
        assert column_names == [
            "sourcesink_discharge",
            "sourcesink_salinity",
            "sourcesink_temperature",
            "sourcesink_tracerTrY",
            "sourcesink_tracerTrA",
            "sourcesink_tracerTrB",
        ]
        # The initialtracer quantity itself is converted by the SpatialConverter.
        assert [spatial.quantity for spatial in ext_model.spatial] == [
            "initialtracerTrY"
        ]

    def test_old_ext_tracers_keep_old_ext_file_order_e2e(self, tmp_path: Path):
        """Old-ext tracers keep the old ext file order, even though they are converted before the sorsin.

        Scenario: there is no pre-existing new ext file. `old.ext` lists `initialtracerX`, then
        `tracerbndA`, then the sorsin, and `sorsin.tim` has the tracer columns `X` (10.0) and `A` (11.0).

        Expected: the kernel registers the tracers of an old ext file in file order (the `readprovider` loop
        in `findexternalboundarypoints`, `fm_external_forcings.f90`, calls `add_bndtracer` for both
        `tracerbnd*` and `initialtracer*`), so the `.tim` columns are `X, A`.

        What went wrong (review finding M1): `initialtracerX` is converted to a `[Spatial]` and `tracerbndA`
        to a `[Boundary]` before the sorsin is reached. Reading the half-converted new ext model gave
        `new_ext_tracer_quantities = ['tracerbndA', 'initialtracerX']` (`(*boundary, *spatial)`), although
        there is no new ext file. The builder ranks the new ext above the old ext, so it labelled the columns
        `A, X`: no error, but column 4 (X's data, 10.0) was named `tracerA`, swapping the two tracers' values.

        The new ext tracers are now a snapshot taken before `update()` starts, so here the list is empty and
        the old ext order `X, A` is used.
        """
        model_dir = tmp_path / "old_ext_file_order"
        model_dir.mkdir()

        (model_dir / "x_init.xyz").write_text("0.0 0.0 1.0\n")
        (model_dir / "a_bnd.pli").write_text("A\n     1     2\n      0.0      0.0\n")
        (model_dir / "a_bnd_0001.tim").write_text("0.0 5.0\n60.0 5.0\n")
        (model_dir / "sorsin.pli").write_text(
            "L1\n     1     2\n      5.0      5.0\n"
        )
        (model_dir / "sorsin.tim").write_text(
            "* Time Flow Salinity Temperature X A\n"
            "0.0 1.0 2.0 3.0 10.0 11.0\n"
            "60.0 1.0 2.0 3.0 10.0 11.0\n"
        )
        (model_dir / "old.ext").write_text(
            "QUANTITY     =initialtracerX\n"
            "FILENAME     =x_init.xyz\n"
            "FILETYPE     =7\n"
            "METHOD       =5\n"
            "OPERAND      =O\n"
            "\n"
            "QUANTITY     =tracerbndA\n"
            "FILENAME     =a_bnd.pli\n"
            "FILETYPE     =9\n"
            "METHOD       =3\n"
            "OPERAND      =O\n"
            "\n"
            "QUANTITY     =discharge_salinity_temperature_sorsin\n"
            "FILENAME     =sorsin.pli\n"
            "FILETYPE     =9\n"
            "METHOD       =1\n"
            "OPERAND      =O\n"
        )
        (model_dir / "model.mdu").write_text(
            "[General]\n"
            "Program                             = D-Flow FM\n"
            "FileVersion                         = 1.09\n"
            "\n"
            "[physics]\n"
            "Salinity                            = 1\n"
            "Temperature                         = 1\n"
            "\n"
            "[time]\n"
            "RefDate                             = 20160101\n"
            "\n"
            "[external forcing]\n"
            "ExtForceFile                        = old.ext\n"
        )

        converter = ExternalForcingConverter.from_mdu(
            model_dir / "model.mdu", debug=True
        )
        ext_model, _ = converter.update()

        first_value = {
            f.quantityunitpair[1].quantity: f.datablock[0][1]
            for f in ext_model.sourcesink[0].discharge.forcing
        }
        # `.tim` columns 4 and 5 hold 10.0 (first tracer, X) and 11.0 (second tracer, A)
        assert first_value["sourcesink_tracerX"] == 10.0
        assert first_value["sourcesink_tracerA"] == 11.0

    def test_invalid_inifield_does_not_affect_run_without_source_sink(
        self, tmp_path: Path
    ):
        """The inifield file is read lazily, so an invalid one does not break a run without a source/sink.

        Only the source/sink conversion needs the inifield tracer quantities for the TIM column order
        (review finding M2). The old ext file here has no source/sink, and the inifield file the MDU
        references is invalid (unknown `dataFileType`): the conversion must still succeed and never load it.
        """
        model_dir = tmp_path / "invalid_inifield"
        model_dir.mkdir()

        (model_dir / "x_init.xyz").write_text("0.0 0.0 1.0\n")
        (model_dir / "bad_inifield.ini").write_text(
            "[General]\n"
            "fileVersion = 2.00\n"
            "fileType = iniField\n"
            "\n"
            "[Initial]\n"
            "quantity = initialtracerX\n"
            "dataFile = x_init.xyz\n"
            "dataFileType = notatype\n"
            "interpolationMethod = triangulation\n"
        )
        (model_dir / "old.ext").write_text(
            "QUANTITY     =initialtracerX\n"
            "FILENAME     =x_init.xyz\n"
            "FILETYPE     =7\n"
            "METHOD       =5\n"
            "OPERAND      =O\n"
        )
        (model_dir / "model.mdu").write_text(
            "[General]\n"
            "Program                             = D-Flow FM\n"
            "FileVersion                         = 1.09\n"
            "\n"
            "[physics]\n"
            "Salinity                            = 0\n"
            "Temperature                         = 0\n"
            "\n"
            "[time]\n"
            "RefDate                             = 20160101\n"
            "\n"
            "[geometry]\n"
            "IniFieldFile                        = bad_inifield.ini\n"
            "\n"
            "[external forcing]\n"
            "ExtForceFile                        = old.ext\n"
        )

        converter = ExternalForcingConverter.from_mdu(
            model_dir / "model.mdu", debug=True
        )
        ext_model, _ = converter.update()

        assert [spatial.quantity for spatial in ext_model.spatial] == [
            "initialtracerX"
        ]
        assert converter._inifield_loaded is False


def write_tracer_model(
    model_dir: Path,
    inifield_file: str | None = None,
    inifield_content: str | None = None,
    new_ext_content: str | None = None,
) -> Path:
    """Write a minimal model whose MDU optionally references an inifield file and a new ext file."""
    model_dir.mkdir(exist_ok=True)
    (model_dir / "x.xyz").write_text("0.0 0.0 1.0\n")
    (model_dir / "a_bnd.pli").write_text("A\n     1     2\n      0.0      0.0\n")
    (model_dir / "tracers.bc").write_text(
        "[General]\nfileVersion = 1.01\nfileType = boundConds\n"
    )
    (model_dir / "old.ext").write_text(
        "QUANTITY     =initialtracerX\n"
        "FILENAME     =x.xyz\n"
        "FILETYPE     =7\n"
        "METHOD       =5\n"
        "OPERAND      =O\n"
    )
    mdu = (
        "[General]\nProgram = D-Flow FM\nFileVersion = 1.09\n\n"
        "[physics]\nSalinity = 0\nTemperature = 0\n\n"
        "[time]\nRefDate = 20160101\n\n"
    )
    if inifield_file is not None:
        mdu += f"[geometry]\nIniFieldFile = {inifield_file}\n\n"
    if inifield_content is not None:
        (model_dir / inifield_file).write_text(inifield_content)
    mdu += "[external forcing]\nExtForceFile = old.ext\n"
    if new_ext_content is not None:
        (model_dir / "existing_new.ext").write_text(new_ext_content)
        mdu += "ExtForceFileNew = existing_new.ext\n"
    (model_dir / "model.mdu").write_text(mdu)
    return model_dir / "model.mdu"


class TestExternalForcingConverterTracerQuantities:
    """The tracer quantity collectors that feed the source/sink TIM column ordering."""

    def test_inifield_quantities_list_initial_then_parameter_in_file_order(
        self, tmp_path: Path
    ):
        mdu = write_tracer_model(
            tmp_path,
            inifield_file="ini_fields.ini",
            inifield_content=(
                "[General]\nfileVersion = 2.00\nfileType = iniField\n\n"
                "[Parameter]\nquantity = frictionCoefficient\ndataFile = x.xyz\n"
                "dataFileType = sample\ninterpolationMethod = triangulation\n\n"
                "[Initial]\nquantity = initialtracerB\ndataFile = x.xyz\n"
                "dataFileType = sample\ninterpolationMethod = triangulation\n\n"
                "[Initial]\nquantity = initialtracerA\ndataFile = x.xyz\n"
                "dataFileType = sample\ninterpolationMethod = triangulation\n"
            ),
        )

        converter = ExternalForcingConverter.from_mdu(mdu, debug=True)

        assert converter._inifield_tracer_quantities() == [
            "initialtracerB",
            "initialtracerA",
            "frictionCoefficient",
        ]

    def test_inifield_quantities_empty_when_mdu_has_no_inifield_file(
        self, tmp_path: Path
    ):
        mdu = write_tracer_model(tmp_path)

        converter = ExternalForcingConverter.from_mdu(mdu, debug=True)

        assert converter._inifield_tracer_quantities() == []

    def test_inifield_quantities_empty_when_inifield_file_is_missing_on_disk(
        self, tmp_path: Path
    ):
        mdu = write_tracer_model(tmp_path, inifield_file="missing.ini")

        converter = ExternalForcingConverter.from_mdu(mdu, debug=True)

        assert converter._inifield_tracer_quantities() == []

    def test_new_ext_quantities_list_boundaries_before_spatial(self, tmp_path: Path):
        """The kernel registers the new ext boundaries first, then the spatial fields, each in file order."""
        mdu = write_tracer_model(
            tmp_path,
            new_ext_content=(
                "[General]\nfileVersion = 2.01\nfileType = extForce\n\n"
                "[Spatial]\nquantity = initialtracerS\ndataFile = x.xyz\n"
                "dataFileType = sample\ninterpolationMethod = triangulation\n\n"
                "[Boundary]\nquantity = tracerbndB\nlocationFile = a_bnd.pli\n"
                "forcingFile = tracers.bc\n"
            ),
        )

        converter = ExternalForcingConverter.from_mdu(mdu, debug=True)

        assert converter._new_ext_tracer_quantities() == [
            "tracerbndB",
            "initialtracerS",
        ]

    def test_new_ext_quantities_snapshot_follows_the_ext_model_setter(
        self, tmp_path: Path
    ):
        """Replacing the ext model refreshes the snapshot, and `update()` does not change it."""
        mdu = write_tracer_model(tmp_path)
        converter = ExternalForcingConverter.from_mdu(mdu, debug=True)
        assert converter._new_ext_tracer_quantities() == []

        (tmp_path / "other_new.ext").write_text(
            "[General]\nfileVersion = 2.01\nfileType = extForce\n\n"
            "[Spatial]\nquantity = initialtracerZ\ndataFile = x.xyz\n"
            "dataFileType = sample\ninterpolationMethod = triangulation\n"
        )
        converter.ext_model = tmp_path / "other_new.ext"
        assert converter._new_ext_tracer_quantities() == ["initialtracerZ"]

        converter.update()

        assert converter._new_ext_tracer_quantities() == ["initialtracerZ"]


class TestSourceSinkConverterEdgeCases:
    """Tests for SourceSinkConverter edge cases and error handling."""

    def test_constructor_raises_when_mdu_parser_is_none(self):
        """Test that constructor raises TypeError when mdu_parser is None."""
        with pytest.raises(TypeError, match="mdu_parser is required"):
            SourceSinkConverter(mdu_parser=None)

    def test_convert_raises_when_refdate_is_missing(self):
        """Test that convert() raises ValueError when refdate is missing."""
        mock_parser = MagicMock(spec=MDUParser)
        mock_parser.temperature_salinity_data = {}
        converter = SourceSinkConverter(mdu_parser=mock_parser)
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.DischargeSalinityTemperatureSorSin,
            filename="tests/data/input/source-sink/leftsor.pliz",
            filetype=9,
            method="1",
            operand="override",
        )
        with pytest.raises(
            ValueError,
            match="temperature_salinity_data'.*'refdate",
        ):
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
