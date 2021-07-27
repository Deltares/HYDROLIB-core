from hydrolib.core.io.bc.models import Forcing, Function
from hydrolib.core.io.ini.parser import Parser, ParserConfig
from pydantic.generics import GenericModel
from typing import TypeVar, Generic

import inspect


TWrapper = TypeVar("TWrapper")


class TestWrapper(GenericModel, Generic[TWrapper]):
    val: TWrapper


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

    wrapper = TestWrapper[Forcing].parse_obj({"val": document.sections[0]})
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
