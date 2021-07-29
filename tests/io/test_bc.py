import inspect

from hydrolib.core.io.bc.models import (
    Forcing,
    Function,
    FunctionData,
    TimeInterpolation,
)
from hydrolib.core.io.ini.parser import Parser, ParserConfig
from ..utils import WrapperTest


def test_create_a_forcing_from_scratch():
    forcing = Forcing(
        name="F001",
        function=Function.TimeSeries(
            time_interpolation=TimeInterpolation.linear,
            function_data=[
                FunctionData(quantity="time", unit="s", values=[1.0, 2.0, 3.0])
            ],
        ),
    )

    assert forcing.name == "F001"
    assert isinstance(forcing.function, Function.TimeSeries)
    assert forcing.function.offset == 0.0
    assert forcing.function.factor == 1.0
    assert forcing.function.time_interpolation == TimeInterpolation.linear
    assert "time" in forcing.function.function_data
    assert forcing.function.function_data["time"].quantity == "time"
    assert forcing.function.function_data["time"].unit == "s"
    assert forcing.function.function_data["time"].values == [1.0, 2.0, 3.0]


def test_read_bc_expected_result():
    input_str = inspect.cleandoc(
        """
        [Forcing]
            name              = right01_0001
            function          = timeSeries
            timeInterpolation = linear
            quantity          = time
            unit              = minutes since 2001-01-01
            quantity          = waterlevelbnd
            unit              = m
               0.000000 2.50
            1440.000000 2.50
        """
    )

    parser = Parser(ParserConfig(parse_comments=False, parse_datablocks=True))

    for line in input_str.splitlines():
        parser.feed_line(line)

    document = parser.finalize()

    wrapper = WrapperTest[Forcing].parse_obj({"val": document.sections[0]})
    forcing = wrapper.val

    assert forcing.name == "right01_0001"
    assert forcing.function.function == "timeSeries"
    assert isinstance(forcing.function, Function.TimeSeries)
    assert "time" in forcing.function.function_data
    assert forcing.function.function_data["time"].quantity == "time"
    assert forcing.function.function_data["time"].unit == "minutes since 2001-01-01"
    assert forcing.function.function_data["time"].values == [0.0, 2.5]
    assert "waterlevelbnd" in forcing.function.function_data
    assert forcing.function.function_data["waterlevelbnd"].quantity == "waterlevelbnd"
    assert forcing.function.function_data["waterlevelbnd"].unit == "m"
    assert forcing.function.function_data["waterlevelbnd"].values == [1440.0, 2.5]
