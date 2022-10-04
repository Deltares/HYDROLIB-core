import inspect
from pathlib import Path
from typing import List

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.ini.models import BaseModel
from hydrolib.core.io.bc.models import (
    T3D,
    Astronomic,
    AstronomicCorrection,
    Constant,
    ForcingBase,
    ForcingModel,
    Harmonic,
    HarmonicCorrection,
    QHTable,
    QuantityUnitPair,
    TimeInterpolation,
    TimeSeries,
    VerticalInterpolation,
    VerticalPositionType,
)
from hydrolib.core.io.ini.parser import Parser, ParserConfig

from ..utils import (
    assert_files_equal,
    invalid_test_data_dir,
    test_data_dir,
    test_output_dir,
    test_reference_dir,
)


class TestQuantityUnitPair:
    def test_create_quantityunitpair(self):
        pair = QuantityUnitPair(quantity="some_quantity", unit="some_unit")
        assert isinstance(pair, BaseModel)
        assert pair.quantity == "some_quantity"
        assert pair.unit == "some_unit"
        assert pair.verticalpositionindex is None

    def test_create_quantityunitpair_with_verticalpositionindex(self):
        pair = QuantityUnitPair(
            quantity="some_quantity", unit="some_unit", verticalpositionindex=123
        )
        assert isinstance(pair, BaseModel)
        assert pair.quantity == "some_quantity"
        assert pair.unit == "some_unit"
        assert pair.verticalpositionindex == 123


class TestTimeSeries:
    def test_create_a_forcing_from_scratch(self):
        forcing = TimeSeries(**_create_time_series_values())

        assert isinstance(forcing, TimeSeries)
        assert forcing.name == "boundary_timeseries"
        assert forcing.offset == 1.23
        assert forcing.factor == 2.34
        assert forcing.timeinterpolation == TimeInterpolation.block_to
        assert len(forcing.quantityunitpair) == 2
        assert forcing.quantityunitpair[0].quantity == "time"
        assert forcing.quantityunitpair[0].unit == "minutes since 2015-01-01 00:00:00"
        assert forcing.quantityunitpair[1].quantity == "dischargebnd"
        assert forcing.quantityunitpair[1].unit == "m³/s"
        assert len(forcing.datablock) == 3
        assert forcing.datablock[0] == [0, 1.23]
        assert forcing.datablock[1] == [60, 2.34]
        assert forcing.datablock[2] == [120, 3.45]

    def test_read_bc_expected_result(self):
        input_str = inspect.cleandoc(
            """
            [Forcing]
                name              = right01_0001
                function          = timeseries  # what about casing?
                timeInterpolation = linear
                quantity          = time
                unit              = minutes since 2001-01-01
                quantity          = waterlevelbnd
                unit              = m
                   0.000000 2.50
                1440.000000 2.50
            """
        )

        parser = Parser(ParserConfig(parse_comments=True, parse_datablocks=True))

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()
        sec = document.sections[0].flatten()
        forcing = TimeSeries.parse_obj(sec)

        assert forcing.name == "right01_0001"
        assert forcing.function == "timeseries"
        assert isinstance(forcing, TimeSeries)
        assert forcing.quantityunitpair[0].quantity == "time"
        assert forcing.quantityunitpair[0].unit == "minutes since 2001-01-01"
        assert forcing.datablock[0] == [0.0, 2.5]
        assert forcing.quantityunitpair[1].quantity == "waterlevelbnd"
        assert forcing.quantityunitpair[1].unit == "m"
        assert forcing.datablock[1] == [1440.0, 2.5]


class TestForcingBase:
    @pytest.mark.parametrize(
        "input,expected",
        [
            ("TimeSeries", "timeseries"),
            ("haRmoniC", "harmonic"),
            ("ASTRONOMIC", "astronomic"),
            ("harmonic-Correction", "harmonic-correction"),
            ("Astronomic-Correction", "astronomic-correction"),
            ("t3D", "t3d"),
            ("QHtable", "qhtable"),
            ("Constant", "constant"),
            ("DOESNOTEXIST", "DOESNOTEXIST"),
            ("doesnotexist", "doesnotexist"),
        ],
    )
    def test_parses_function_case_insensitive(self, input, expected):
        forcing = ForcingBase(function=input, name="somename", quantityunitpair=[])

        assert forcing.function == expected

    @pytest.mark.parametrize(
        "missing_field",
        [
            "quantity",
            "unit",
        ],
    )
    def test_create_forcingbase_missing_field_raises_correct_error(
        self, missing_field: str
    ):
        values = dict(
            name="Boundary2",
            function="constant",
            quantity="dischargebnd",
            unit="m³/s",
            datablock=[["100"]],
        )

        del values[missing_field]

        with pytest.raises(ValidationError) as error:
            ForcingBase(**values)

        expected_message = f"{missing_field} is not provided"
        assert expected_message in str(error.value)

    @pytest.mark.parametrize(
        "quantities,units",
        [
            (["time", "dischargebnd"], "m³/s"),
            (
                ["time", "dischargebnd", "extra"],
                ["minutes since 2021-01-01 00:00:00", "m³/s"],
            ),
        ],
    )
    def test_create_forcingbase_mismatch_number_of_quantities_units_raises_correct_error(
        self, quantities, units
    ):
        values = dict(
            name="Boundary2",
            function="constant",
            quantity=quantities,
            unit=units,
            datablock=[["100"]],
        )

        with pytest.raises(ValidationError) as error:
            ForcingBase(**values)

        expected_message = "Number of quantities should be equal to number of units"
        assert expected_message in str(error.value)


class TestForcingModel:
    """
    Wrapper class to test the logic of the ForcingModel class in hydrolib.core.io.bc.models.py.
    """

    def test_forcing_model(self):
        filepath = (
            test_data_dir
            / "input/e02/f101_1D-boundaries/c01_steady-state-flow/BoundaryConditions.bc"
        )
        m = ForcingModel(filepath)
        assert len(m.forcing) == 13
        assert isinstance(m.forcing[-1], TimeSeries)

    def test_read_bc_missing_field_raises_correct_error(self):
        file = "missing_field.bc"
        identifier = "Boundary2"

        filepath = invalid_test_data_dir / file

        with pytest.raises(ValidationError) as error:
            ForcingModel(filepath)

        expected_message1 = f"{file} -> forcing -> 1 -> {identifier}"
        expected_message2 = "quantity is not provided"
        assert expected_message1 in str(error.value)
        assert expected_message2 in str(error.value)

    def test_save_forcing_model(self):
        file = Path(test_output_dir / "test.bc")
        reference_file = Path(test_reference_dir / "bc" / "test.bc")
        forcingmodel = ForcingModel()
        forcingmodel.filepath = file

        timeseries = TimeSeries(**_create_time_series_values())
        harmonic = Harmonic(**_create_harmonic_values(False))
        harmoniccorrection = HarmonicCorrection(**_create_harmonic_values(True))
        t3d = T3D(**_create_t3d_values())
        qhtable = QHTable(**_create_qhtable_values())
        constant = Constant(**_create_constant_values())

        forcingmodel.forcing.append(timeseries)
        forcingmodel.forcing.append(harmonic)
        forcingmodel.forcing.append(harmoniccorrection)
        forcingmodel.forcing.append(t3d)
        forcingmodel.forcing.append(qhtable)
        forcingmodel.forcing.append(constant)
        forcingmodel.save()

        assert file.is_file() == True
        assert_files_equal(file, reference_file, skip_lines=[0, 3])

    @pytest.mark.parametrize("cls", [Astronomic, AstronomicCorrection])
    def test_astronomic_values_with_strings_in_datablock_are_parsed_correctly(
        self, cls
    ):
        try:
            is_correction = cls == AstronomicCorrection
            _ = cls(**_create_astronomic_values(is_correction))
        except ValidationError:
            pytest.fail(
                f"No validation error should be raised when creating an {cls.__name__}"
            )


class TestT3D:
    @pytest.mark.parametrize(
        "vertical_position_type, exp_vertical_position_type",
        [
            ("percBed", VerticalPositionType.percentage_bed),
            ("ZBed", VerticalPositionType.z_bed),
            ("ZDatum", VerticalPositionType.z_datum),
            ("ZSurf", VerticalPositionType.z_surf),
        ],
    )
    def test_initialize_t3d(
        self,
        vertical_position_type: str,
        exp_vertical_position_type: VerticalPositionType,
    ):
        values = _create_t3d_values()
        values["verticalpositiontype"] = vertical_position_type

        t3d = T3D(**values)

        assert t3d.name == "boundary_t3d"
        assert t3d.function == "t3d"
        assert t3d.offset == 1.23
        assert t3d.factor == 2.34
        assert t3d.timeinterpolation == TimeInterpolation.linear

        assert len(t3d.verticalpositions) == 3
        assert t3d.verticalpositions[0] == 3.45
        assert t3d.verticalpositions[1] == 4.56
        assert t3d.verticalpositions[2] == 5.67

        assert t3d.verticalinterpolation == VerticalInterpolation.log
        assert t3d.verticalpositiontype == exp_vertical_position_type

        assert len(t3d.quantityunitpair) == 4
        assert t3d.quantityunitpair[0] == QuantityUnitPair(quantity="time", unit="m")
        assert t3d.quantityunitpair[1] == QuantityUnitPair(
            quantity="salinitybnd", unit="ppt", verticalpositionindex=1
        )
        assert t3d.quantityunitpair[2] == QuantityUnitPair(
            quantity="salinitybnd", unit="ppt", verticalpositionindex=2
        )
        assert t3d.quantityunitpair[3] == QuantityUnitPair(
            quantity="salinitybnd", unit="ppt", verticalpositionindex=3
        )

        assert len(t3d.datablock) == 3
        assert t3d.datablock[0] == [0, 1, 2, 3]
        assert t3d.datablock[1] == [60, 4, 5, 6]
        assert t3d.datablock[2] == [120, 7, 8, 9]

    def test_create_t3d_first_quantity_not_time_raises_error(self):
        values = _create_t3d_values()

        values["quantityunitpair"] = [
            _create_quantityunitpair("salinitybnd", "ppt"),
            _create_quantityunitpair("time", "m"),
        ]

        with pytest.raises(ValidationError) as error:
            T3D(**values)

        expected_message = "First quantity should be `time`"
        assert expected_message in str(error.value)

    def test_create_t3d_time_quantity_with_verticalpositionindex_raises_error(self):
        values = _create_t3d_values()

        values["quantityunitpair"] = [
            _create_quantityunitpair("time", "m", 1),
        ]

        with pytest.raises(ValidationError) as error:
            T3D(**values)

        expected_message = "`time` quantity cannot have vertical position index"
        assert expected_message in str(error.value)

    def test_create_t3d_verticalpositionindex_missing_for_non_time_unit_raises_error(
        self,
    ):
        values = _create_t3d_values()

        values["quantityunitpair"] = [
            _create_quantityunitpair("time", "m"),
            _create_quantityunitpair("salinitybnd", "ppt", None),
        ]

        with pytest.raises(ValidationError) as error:
            T3D(**values)

        expected_maximum_index = len(values["verticalpositions"])
        expected_message = (
            f"Vertical position index should be between 1 and {expected_maximum_index}"
        )
        assert expected_message in str(error.value)

    @pytest.mark.parametrize(
        "verticalpositions, verticalpositionindexes",
        [
            pytest.param([1.23, 4.56], [0, 1], id="verticalpositionindex is one-based"),
            pytest.param(
                [1.23, 4.56],
                [1, 3],
                id="verticalpositionindex bigger than verticalpositions length",
            ),
            pytest.param([1.23, 4.56], [1, None], id="too few verticalpositionindexes"),
            pytest.param(
                [1.23, 4.56], [1, 2, 3], id="too many verticalpositionindexes"
            ),
        ],
    )
    def test_create_t3d_verticalpositionindex_has_invalid_value_raises_error(
        self, verticalpositions: List[float], verticalpositionindexes: List[int]
    ):
        values = _create_t3d_values()

        time_quantityunitpair = [_create_quantityunitpair("time", "m")]
        other_quantutyunitpairs = []
        for i in range(len(verticalpositionindexes)):
            other_quantutyunitpairs.append(
                _create_quantityunitpair(
                    "randomQuantity", "randomUnit", verticalpositionindexes[i]
                )
            )

        values["quantityunitpair"] = time_quantityunitpair + other_quantutyunitpairs
        values["verticalpositions"] = verticalpositions

        with pytest.raises(ValidationError) as error:
            T3D(**values)

        maximum_verticalpositionindex = len(verticalpositions)
        expected_message = f"Vertical position index should be between 1 and {maximum_verticalpositionindex}"
        assert expected_message in str(error.value)

    @pytest.mark.parametrize(
        "number_of_quantities_and_units, number_of_verticalpositionindexes",
        [(4, 2), (2, 4)],
    )
    def test_create_t3d_number_of_verticalindexpositions_not_as_expected_raises_error(
        self,
        number_of_quantities_and_units: int,
        number_of_verticalpositionindexes: int,
    ):
        values = _create_t3d_values()

        del values["quantityunitpair"]

        onebased_index_offset = 1

        values["quantity"] = ["time"] + [
            str(i + onebased_index_offset)
            for i in range(number_of_quantities_and_units)
        ]
        values["unit"] = ["m"] + [
            str(i + onebased_index_offset)
            for i in range(number_of_quantities_and_units)
        ]
        values["verticalpositionindex"] = [None] + [
            str(i + onebased_index_offset)
            for i in range(number_of_verticalpositionindexes)
        ]

        with pytest.raises(ValidationError) as error:
            T3D(**values)

        expected_message = "Number of vertical positions should be equal to the number of units or equal to the number of units - 1"
        assert expected_message in str(error.value)


def _create_time_series_values():
    return dict(
        name="boundary_timeseries",
        function="timeseries",
        timeinterpolation="blockTo",
        offset="1.23",
        factor="2.34",
        quantityunitpair=[
            _create_quantityunitpair("time", "minutes since 2015-01-01 00:00:00"),
            _create_quantityunitpair("dischargebnd", "m³/s"),
        ],
        datablock=[["0", "1.23"], ["60", "2.34"], ["120", "3.45"]],
    )


def _create_harmonic_values(iscorrection: bool):
    function = "harmonic-correction" if iscorrection else "harmonic"
    return dict(
        name=f"boundary_{function}",
        function=function,
        quantityunitpair=[
            _create_quantityunitpair("harmonic component", "minutes"),
            _create_quantityunitpair("waterlevelbnd amplitude", "m"),
            _create_quantityunitpair("waterlevelbnd phase", "deg"),
        ],
        datablock=[
            ["0", "1.23", "2.34"],
            ["60", "3.45", "4.56"],
        ],
    )


def _create_astronomic_values(iscorrection: bool):
    function = "astronomic-correction" if iscorrection else "astronomic"
    return dict(
        name=f"boundary_{function}",
        function=function,
        quantityunitpair=[
            _create_quantityunitpair("astronomic component", "-"),
            _create_quantityunitpair("waterlevelbnd amplitude", "m"),
            _create_quantityunitpair("waterlevelbnd phase", "deg"),
        ],
        datablock=[
            ["A0", "1.23", "2.34"],
            ["M4", "3.45", "4.56"],
            ["N2", "5.67", "6.78"],
        ],
    )


def _create_quantityunitpair(quantity, unit, verticalpositionindex=None):
    return QuantityUnitPair(
        quantity=quantity, unit=unit, verticalpositionindex=verticalpositionindex
    )


def _create_t3d_values():
    return dict(
        name="boundary_t3d",
        function="t3d",
        offset="1.23",
        factor="2.34",
        verticalpositions="3.45 4.56 5.67",
        verticalinterpolation="log",
        verticalpositiontype="percBed",
        timeinterpolation="linear",
        quantityunitpair=[
            _create_quantityunitpair("time", "m"),
            _create_quantityunitpair("salinitybnd", "ppt", 1),
            _create_quantityunitpair("salinitybnd", "ppt", 2),
            _create_quantityunitpair("salinitybnd", "ppt", 3),
        ],
        datablock=[
            ["0", "1", "2", "3"],
            ["60", "4", "5", "6"],
            ["120", "7", "8", "9"],
        ],
    )


def _create_qhtable_values():
    return dict(
        name="boundary_qhtable",
        function="qhtable",
        quantityunitpair=[
            _create_quantityunitpair("qhbnd discharge", "m3/s"),
            _create_quantityunitpair("qhbnd waterlevel", "m"),
        ],
        datablock=[
            ["1.23", "2.34"],
            ["3.45", "4.56"],
        ],
    )


def _create_constant_values():
    return dict(
        name="boundary_constant",
        function="constant",
        offset="1.23",
        factor="2.34",
        timeinterpolation="linear",
        quantityunitpair=[
            _create_quantityunitpair("waterlevelbnd", "m"),
        ],
        datablock=[
            ["3.45"],
        ],
    )
