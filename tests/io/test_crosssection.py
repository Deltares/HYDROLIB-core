import inspect
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import Any, Callable, List, Union

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.ini.models import (
    CircleCrsDef,
    CrossDefModel,
    CrossSectionDefinition,
    RectangleCrsDef,
    XYZCrsDef,
    YZCrsDef,
    ZWCrsDef,
    ZWRiverCrsDef,
)
from hydrolib.core.io.ini.parser import Parser, ParserConfig

from ..utils import WrapperTest, test_data_dir


def test_crossdef_model():
    filepath = test_data_dir / "input/TMP_dflowfm_individual_files/crsdef1.ini"
    m = CrossDefModel(filepath)
    assert len(m.definition) == 4

    assert isinstance(m.definition[0], CircleCrsDef)
    assert m.definition[0].id == "Prof1"
    assert m.definition[0].thalweg == 0.0
    assert m.definition[0].diameter == 2.0
    assert m.definition[0].frictionid == "Brick"


def test_create_a_circlecrsdef_from_scratch():
    cd = CircleCrsDef(
        id="Prof1",
        diameter=3.14,
        frictiontype="wallLawNikuradse",
        frictionvalue=1.5,
    )
    assert cd.id == "Prof1"
    assert cd.type == "circle"
    assert cd.diameter == 3.14
    assert cd.frictiontype == "wallLawNikuradse"
    assert cd.frictionvalue == 1.5


def test_create_a_circlecrsdef_with_duplicate_frictionspec():
    csdefid = "Prof1"
    with pytest.raises(ValidationError) as error:
        cd = CircleCrsDef(
            id=csdefid,
            diameter=3.14,
            frictionid="Brick",
            frictiontype="wallLawNikuradse",
            frictionvalue=1.5,
        )
    expected_message = (
        f'Cross section with id "{csdefid}" has duplicate friction specification'
    )

    assert expected_message in str(error.value)


def test_create_a_rectanglecrsdef_from_scratch():
    cd = RectangleCrsDef(
        id="Prof1",
        width=3.14,
        height=2.718,
        frictiontype="wallLawNikuradse",
        frictionvalue=1.5,
    )
    assert cd.id == "Prof1"
    assert cd.type == "rectangle"
    assert cd.width == 3.14
    assert cd.height == 2.718
    assert cd.frictiontype == "wallLawNikuradse"
    assert cd.frictionvalue == 1.5


def test_create_a_rectanglecrsdef_without_frictionspec():
    csdefid = "Prof1"
    with pytest.raises(ValidationError) as error:
        cd = RectangleCrsDef(
            id=csdefid,
            width=3.14,
            height=2.718,
        )
    expected_message = (
        f'Cross section with id "{csdefid}" is missing any friction specification.'
    )

    assert expected_message in str(error.value)


def test_create_a_zwrivercrsdef_from_scratch():
    cd = ZWRiverCrsDef(
        id="Prof1",
        numlevels=2,
        levels=[-2, 3],
        flowwidths=[
            11,
            44,
            12,
        ],  # Intentional error, to try and trigger make_list_length_validator()
        frictiontypes=["Manning"],
        frictionvalues=[0.03],
    )
    assert cd.id == "Prof1"
    assert cd.type == "zwRiver"
    assert cd.numlevels == 2
    assert cd.levels == [-2, 3]
    assert cd.flowwidths == [11, 44]
    assert cd.frictiontypes == ["Manning"]
    assert cd.frictionvalues == [0.03]


def test_create_a_zwrivercrsdef_without_frictionspec():
    csdefid = "Prof1"
    with pytest.raises(ValidationError) as error:
        cd = ZWRiverCrsDef(
            id=csdefid,
            numlevels=2,
            levels=[-2, 3],
            flowwidths=[11, 44],
        )
    expected_message = (
        f'Cross section with id "{csdefid}" is missing any friction specification.'
    )

    assert expected_message in str(error.value)
