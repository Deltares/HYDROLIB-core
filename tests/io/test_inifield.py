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

from ..utils import (
    WrapperTest,
    assert_files_equal,
    invalid_test_data_dir,
    test_data_dir,
    test_output_dir,
    test_reference_dir,
)


class TestIniField:
    _datafiletype_cases = [
        ("dataFileType", "ARCINFO", "arcinfo"),
        ("dataFileType", "geotiff", "GeoTIFF"),
        ("dataFileType", "samPLE", "sample"),
        ("dataFileType", "1dfield", "1dField"),
        ("dataFileType", "poLYGOn", "polygon"),
    ]

    _interpolationmethod_cases = [
        ("interpolationMethod", "conSTant", "constant"),
        ("interpolationMethod", "trianguLATION", "triangulation"),
        ("interpolationMethod", "averAGING", "averaging"),
    ]

    _operand_cases = [
        ("operand", "o", "O"),
        ("operand", "a", "A"),
        ("operand", "x", "X"),
        ("operand", "N", "N"),
    ]

    _averagingtype_cases = [
        ("averagingType", "MEAN", "mean"),
        ("averagingType", "nearestnb", "nearestNb"),
        ("averagingType", "MAX", "max"),
        ("averagingType", "MIN", "min"),
        ("averagingType", "invdist", "invDist"),
        ("averagingType", "minabs", "minAbs"),
    ]

    _locationtype_cases = [
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
        _datafiletype_cases
        + _interpolationmethod_cases
        + _operand_cases
        + _averagingtype_cases
        + _locationtype_cases,
    )
    def test_initialfield_parses_flowdirection_case_insensitive(
        self, attribute: str, input, expected
    ):
        inifield_values = self._create_required_inifield_values()
        inifield_values[attribute.lower()] = input

        datafiletype = inifield_values.get("datafiletype")
        if datafiletype and datafiletype.lower() == DataFileType.polygon.lower():
            inifield_values["value"] = 1.23  # optionally required

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

    def test_load_and_save(self):
        """Test whether a model loaded from file is serialized correctly.
        Particularly intended to test writing of default enum values."""

        filepath = test_data_dir / "input/dflowfm_individual_files/initialFields.ini"
        m = IniFieldModel(filepath)

        output_file = Path(test_output_dir / "fm" / "serialize_initialFields.ini")
        reference_file = Path(test_reference_dir / "fm" / "serialize_initialFields.ini")

        m.filepath = output_file
        m.save()

        assert_files_equal(output_file, reference_file, [0])

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
        inifield_values["datafiletype"] = DataFileType.sample

        with pytest.raises(ValidationError) as error:
            _ = InitialField(**inifield_values)

        expected_message = f"When value=1.23 is given, dataFileType={DataFileType.polygon} is required."

        assert expected_message in str(error.value)

    def test_initialfield_value_with_missing_value(self):
        inifield_values = self._create_required_inifield_values()
        inifield_values["datafiletype"] = DataFileType.polygon

        with pytest.raises(ValidationError) as error:
            _ = InitialField(**inifield_values)

        expected_message = (
            f"value should be provided when datafiletype is {DataFileType.polygon}"
        )

        assert expected_message in str(error.value)
