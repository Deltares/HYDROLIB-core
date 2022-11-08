import inspect
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import Any, Callable, List, Union

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.dflowfm.friction.models import (
    FrictBranch,
    FrictGlobal,
    FrictionModel,
    FrictionType,
)
from hydrolib.core.io.dflowfm.ini.parser import Parser, ParserConfig

from ...utils import (
    WrapperTest,
    assert_files_equal,
    test_data_dir,
    test_output_dir,
    test_reference_dir,
)


def _get_frictiontype_cases() -> List:
    return [
        ("CHEZY", "Chezy"),
        ("MANNING", "Manning"),
        ("WALLLAWNIKURADSE", "wallLawNikuradse"),
        ("WHITECOLEBROOK", "WhiteColebrook"),
        ("STRICKLERNIKURADSE", "StricklerNikuradse"),
        ("STRICKLER", "Strickler"),
        ("DEBOSBIJKERK", "deBosBijkerk"),
    ]


@pytest.mark.parametrize(
    "input,expected",
    _get_frictiontype_cases(),
)
def test_frictglobal_parses_frictiontype_case_insensitive(input, expected):
    fg = FrictGlobal(
        frictiontype=input,
        frictionid="strucid",
        frictionvalue=1.0,
    )

    assert fg.frictiontype == expected


def test_friction_model():
    filepath = test_data_dir / "input/dflowfm_individual_files/roughness.ini"
    m = FrictionModel(filepath)
    assert len(m.global_) == 1
    assert len(m.branch) == 2

    assert isinstance(m.branch[0], FrictBranch)
    assert m.branch[0].branchid == "Channel1"
    assert m.branch[0].frictiontype == FrictionType.manning
    assert m.branch[0].functiontype == "constant"
    assert m.branch[0].numlocations == 2
    assert m.branch[0].chainage == [0.0, 100.0]
    assert m.branch[0].frictionvalues == [0.2, 0.3]

    assert isinstance(m.branch[1], FrictBranch)
    assert m.branch[1].branchid == "Channel4"
    assert m.branch[1].frictiontype == FrictionType.chezy
    assert m.branch[1].functiontype == "constant"
    assert m.branch[1].numlocations == 0
    assert m.branch[1].chainage == None
    assert m.branch[1].frictionvalues == [40]

    # TODO: Enable this block once issue #143 is done.
    # assert isinstance(m.branch[2], FrictBranch)
    # assert m.branch[2].branchid == "Channel7"
    # assert m.branch[2].frictiontype == FrictionType.chezy
    # assert m.branch[2].functiontype == "absDischarge"
    # assert m.branch[2].numlocations == 2
    # assert m.branch[2].chainage == [0, 300]
    # assert m.branch[2].numlevels == 3
    # assert m.branch[2].levels == [100, 200, 300]

    # # TODO: once the friction values have been changed into a List[List[float]],
    # # the expected value is [[45, 55], [41, 52], [40, 50]], see issue #143.
    # assert m.branch[2].frictionvalues == [
    #     45,
    #     55,
    # ]


def test_create_a_frictbranch_from_scratch():
    fb = FrictBranch(
        branchid="B1",
        frictiontype=FrictionType.walllawnikuradse,
        frictionvalues=[1.5],
    )
    assert fb.branchid == "B1"
    assert fb.numlocations == 0  # default
    assert fb.functiontype == "constant"  # default
    assert fb.frictiontype == FrictionType.walllawnikuradse
    assert fb.frictionvalues == [1.5]


def test_create_a_frictbranch_with_incorrect_levels_or_locations():
    branchid = "B1"
    with pytest.raises(ValidationError) as error:
        _ = FrictBranch(
            branchid=branchid,
            frictiontype=FrictionType.walllawnikuradse,
            chainage=[10, 20],  # intentional wrong len(), should be 1
            levels=[-42],  # intentional wrong len(), should be absent/not given.
            frictionvalues=[1.5, 2.5, 3.5],  # intentional wrong len(), should be 1
        )
    expected_message0 = f"Number of values for levels should be equal to the numLevels value (branchId={branchid})."
    expected_message1 = f"Number of values for chainage should be equal to the numLocations value (branchId={branchid})."
    expected_message2 = f"Number of values for frictionValues should be equal to the numLocations*numLevels value (branchId={branchid})."

    assert expected_message0 in str(error.value)
    assert expected_message1 in str(error.value)
    assert expected_message2 in str(error.value)


def test_save():

    filepath = test_data_dir / "input/dflowfm_individual_files/roughness.ini"
    m = FrictionModel(filepath)

    output_file = Path(test_output_dir / "fm" / "serialize_roughness.ini")
    reference_file = Path(test_reference_dir / "fm" / "serialize_roughness.ini")

    m.filepath = output_file
    m.save()

    assert_files_equal(output_file, reference_file, [0])
