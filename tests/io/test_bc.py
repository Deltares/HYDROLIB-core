import inspect

from hydrolib.core.io.bc.models import (
    ForcingBase,
    ForcingModel,
    TimeInterpolation,
    TimeSeries,
)
from hydrolib.core.io.ini.parser import Parser, ParserConfig

from ..utils import WrapperTest, test_data_dir


def test_forcing_model():
    filepath = (
        test_data_dir
        / "input/e02/f101_1D-boundaries/c01_steady-state-flow/BoundaryConditions.bc"
    )
    m = ForcingModel(filepath)
    assert len(m.forcing) == 13
    assert isinstance(m.forcing[-1], TimeSeries)


def test_create_a_forcing_from_scratch():
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
    assert forcing.quantity[0] == "time"
    assert forcing.unit[0] == "s"
    assert forcing.datablock[0] == [1.0, 2.0, 3.0]


def test_read_bc_expected_result():
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
    assert forcing.quantity[0] == "time"
    assert forcing.unit[0] == "minutes since 2001-01-01"
    assert forcing.datablock[0] == [0.0, 2.5]
    assert forcing.quantity[1] == "waterlevelbnd"
    assert forcing.unit[1] == "m"
    assert forcing.datablock[1] == [1440.0, 2.5]
