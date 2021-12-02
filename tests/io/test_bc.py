import inspect
from pathlib import Path

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.bc.models import (
    T3D,
    Constant,
    ForcingBase,
    ForcingModel,
    Harmonic,
    HarmonicCorrection,
    QHTable,
    QuantityUnitPair,
    TimeInterpolation,
    TimeSeries,
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
        assert pair.quantity == "some_quantity"
        assert pair.unit == "some_unit"


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


def _create_time_series_values():
    return dict(
        name="boundary_timeseries",
        function="timeseries",
        timeinterpolation="blockTo",
        offset="1.23",
        factor="2.34",
        quantityunitpair=[
            ("time", "minutes since 2015-01-01 00:00:00"),
            ("dischargebnd", "m³/s"),
        ],
        datablock=[["0", "1.23"], ["60", "2.34"], ["120", "3.45"]],
    )


def _create_harmonic_values(iscorrection: bool):
    function = "harmonic-correction" if iscorrection else "harmonic"
    return dict(
        name=f"boundary_{function}",
        function=function,
        quantityunitpair=[
            ("harmonic component", "minutes"),
            ("waterlevelbnd amplitude", "m"),
            ("waterlevelbnd phase", "deg"),
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
            ("astronomic component", "-"),
            ("waterlevelbnd amplitude", "m"),
            ("waterlevelbnd phase", "deg"),
        ],
        datablock=[
            ["A0", "1.23", "2.34"],
            ["M4", "3.45", "4.56"],
            ["N2", "5.67", "6.78"],
        ],
    )


def _create_t3d_values():
    return dict(
        name="boundary_t3d",
        function="t3d",
        offset="1.23",
        factor="2.34",
        verticalpositions=["3.45", "4.56", "5.67"],
        verticalinterpolation="log",
        verticalpositiontype="percBed",
        quantityunitpair=[
            ("time", "m"),
            ("salinitybnd", "ppt"),
            ("salinitybnd", "ppt"),
            ("salinitybnd", "ppt"),
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
            ("qhbnd discharge", "m3/s"),
            ("qhbnd waterlevel", "m"),
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
            ("waterlevelbnd", "m"),
        ],
        datablock=[
            ["3.45"],
        ],
    )
