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
        frictionvalue=[1.5],
    )
    assert cd.id == "Prof1"
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

    # assert cd.id == "Prof1"
    # assert cd.diameter == 3.14
    # assert cd.frictiontype == "wallLawNikuradse"
    # assert cd.frictionvalue == 1.5
