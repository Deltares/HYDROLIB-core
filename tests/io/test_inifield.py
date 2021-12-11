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


def test_inifield_model():
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


def test_initialfield_construction_with_parser():
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
