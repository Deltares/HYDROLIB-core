import inspect
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import Any, List, Union

import pytest
from pydantic.error_wrappers import ValidationError
from pydantic.types import FilePath

from hydrolib.core.io.ini.parser import Parser, ParserConfig
from hydrolib.core.io.inifield.models import (
    AveragingType,
    DataFileType,
    IniFieldGeneral,
    IniFieldModel,
    InitialField,
    InterpolationMethod,
    LocationType,
    Operand,
    ParameterField,
)

from ..utils import WrapperTest, invalid_test_data_dir, test_data_dir


class TestIniField:
    def _get_datafiletype_cases() -> List:
        return [
            ("dataFileType", "ARCINFO", "arcinfo"),
            ("dataFileType", "geotiff", "GeoTIFF"),
            ("dataFileType", "samPLE", "sample"),
            ("dataFileType", "1dfield", "1dField"),
            ("dataFileType", "poLYGOn", "polygon"),
        ]

    def _get_interpolationmethod_cases() -> List:
        return [
            ("interpolationMethod", "conSTant", "constant"),
            ("interpolationMethod", "trianguLATION", "triangulation"),
            ("interpolationMethod", "averAGING", "averaging"),
        ]

    def _get_operand_cases() -> List:
        return [
            ("operand", "o", "O"),
            ("operand", "a", "A"),
            ("operand", "x", "X"),
            ("operand", "N", "N"),
        ]

    def _get_averagingtype_cases() -> List:
        return [
            ("averagingType", "MEAN", "mean"),
            ("averagingType", "nearestnb", "nearestNb"),
            ("averagingType", "MAX", "max"),
            ("averagingType", "MIN", "min"),
            ("averagingType", "invdist", "invDist"),
            ("averagingType", "minabs", "minAbs"),
        ]

    def _get_locationtype_cases() -> List:
        return [
            ("locationType", "1D", "1d"),
            ("locationType", "2D", "2d"),
            ("locationType", "All", "all"),
        ]

    def _create_required_inifield_values(self) -> dict:
        inifield_values = dict(
            quantity="waterlevel",
            datafile="iniwlev.xyz",
            datafiletype="sample",
        )

        return inifield_values

    @pytest.mark.parametrize(
        "attribute,input,expected",
        _get_datafiletype_cases()
        + _get_interpolationmethod_cases()
        + _get_operand_cases()
        + _get_averagingtype_cases()
        + _get_locationtype_cases(),
    )
    def test_initialfield_parses_flowdirection_case_insensitive(
        self, attribute: str, input, expected
    ):
        inifield_values = self._create_required_inifield_values()
        inifield_values[attribute.lower()] = input
        inifield = InitialField(**inifield_values)

        assert getattr(inifield, attribute.lower()) == expected

    def test_inifield_model(self):
        filepath = test_data_dir / "input/dflowfm_individual_files/initialFields.ini"
        m = IniFieldModel(filepath)

        assert len(m.initial) == 2
        assert isinstance(m.initial[0], InitialField)
        assert m.initial[0].quantity == "waterlevel"
        assert m.initial[0].datafile == Path("iniwaterlevels.asc")
        assert m.initial[0].datafiletype == DataFileType.arcinfo
        assert m.initial[0].interpolationmethod == InterpolationMethod.triangulation
        assert m.initial[0].locationtype == LocationType.twod

        assert isinstance(m.initial[1], InitialField)
        assert m.initial[1].quantity == "bedlevel"
        assert m.initial[1].datafile == Path("inibedlevel.ini")
        assert m.initial[1].datafiletype == DataFileType.onedfield

        assert len(m.parameter) == 2
        assert isinstance(m.parameter[0], ParameterField)
        assert m.parameter[0].quantity == "frictioncoefficient"
        assert m.parameter[0].datafile == Path("manning.xyz")
        assert m.parameter[0].datafiletype == DataFileType.sample
        assert m.parameter[0].interpolationmethod == InterpolationMethod.triangulation

        assert isinstance(m.parameter[1], ParameterField)
        assert m.parameter[1].quantity == "frictioncoefficient"
        assert m.parameter[1].datafile == Path("calibration1.pol")
        assert m.parameter[1].datafiletype == DataFileType.polygon
        assert m.parameter[1].interpolationmethod == InterpolationMethod.constant
        assert m.parameter[1].value == 0.03
        assert m.parameter[1].operand == Operand.mult

    def test_initialfield_construction_with_parser(self):
        parser = Parser(ParserConfig())

        input_str = inspect.cleandoc(
            """
            [Initial]
            quantity          = waterDepth
            dataFile          = depth.xyz
            dataFileType      = sample
            """
        )

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        wrapper = WrapperTest[InitialField].parse_obj({"val": document.sections[0]})
        inifield = wrapper.val

        assert inifield.quantity == "waterDepth"
        assert inifield.datafile == Path("depth.xyz")
        assert inifield.datafiletype == DataFileType.sample

        # Check for auto-set default values:
        assert inifield.operand == Operand.override
        assert inifield.interpolationmethod == None
        assert inifield.extrapolationmethod == False

    def test_initialfield_value_with_wrong_datafiletype(self):
        inifield_values = self._create_required_inifield_values()
        inifield_values["value"] = 1.23
        inifield_values["datafiletype"] = "sample"

        with pytest.raises(ValidationError) as error:
            _ = InitialField(**inifield_values)

        expected_message = f"When value=1.23 is given, dataFileType={DataFileType.polygon} is required."

        assert expected_message in str(error.value)
