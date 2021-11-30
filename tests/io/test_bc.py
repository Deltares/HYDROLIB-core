import inspect

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.bc.models import (
    ForcingBase,
    ForcingModel,
    TimeInterpolation,
    TimeSeries,
)
from hydrolib.core.io.ini.parser import Parser, ParserConfig

from ..utils import test_data_dir


class TestTimeSeries:
    def test_create_a_forcing_from_scratch(self):
        forcing = TimeSeries(
            name="F001",
            function="timeseries",
            timeinterpolation=TimeInterpolation.linear,
            quantity="time",
            unit="s",
            datablock=[[1.0, 2.0, 3.0]],
        )

        assert forcing.name == "F001"
        assert isinstance(forcing, TimeSeries)
        assert forcing.offset == 0.0
        assert forcing.factor == 1.0
        assert forcing.timeinterpolation == TimeInterpolation.linear
        assert forcing.quantities[0].quantity == "time"
        assert forcing.quantities[0].unit == "s"
        assert forcing.datablock[0] == [1.0, 2.0, 3.0]

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
        assert forcing.quantities[0].quantity == "time"
        assert forcing.quantities[0].unit == "minutes since 2001-01-01"
        assert forcing.datablock[0] == [0.0, 2.5]
        assert forcing.quantities[1].quantity == "waterlevelbnd"
        assert forcing.quantities[1].unit == "m"
        assert forcing.datablock[1] == [1440.0, 2.5]


class TestForcingBase:
    @pytest.mark.parametrize(
        "input,expected",
        [
            ("TimeSeries", "timeseries"),
            ("haRmoniC", "harmonic"),
            ("ASTRONOMIC", "astronomic"),
            ("harmonicCorrection", "harmoniccorrection"),
            ("AstronomicCorrection", "astronomiccorrection"),
            ("t3D", "t3d"),
            ("QHtable", "qhtable"),
            ("Constant", "constant"),
            ("DOESNOTEXIST", "DOESNOTEXIST"),
            ("doesnotexist", "doesnotexist"),
        ],
    )
    def test_parses_function_case_insensitive(self, input, expected):
        forcing = ForcingBase(function=input, name="somename", quantity=[], unit=[])

        assert forcing.function == expected


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

        filepath = test_data_dir / "input/invalid_files" / file

        with pytest.raises(ValidationError) as error:
            ForcingModel(filepath)

        expected_message1 = f"{file} -> forcing -> 1 -> {identifier}"
        expected_message2 = "quantity is not provided"
        assert expected_message1 in str(error.value)
        assert expected_message2 in str(error.value)
