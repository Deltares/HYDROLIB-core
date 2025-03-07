from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from hydrolib.core.dflowfm.bc.models import (
    Astronomic,
    ForcingModel,
    Harmonic,
    QuantityUnitPair,
)
from hydrolib.core.dflowfm.cmp.models import CmpModel
from hydrolib.tools.ext_old_to_new.converters import CmpToForcingConverter
from tests.utils import compare_two_files


@pytest.fixture
def cmp_model() -> CmpModel:
    data = {
        "comments": ["# Example comment"],
        "components": {
            "harmonics": [{"period": 0.0, "amplitude": 1.0, "phase": 2.0}],
            "astronomics": [{"name": "4MS10", "amplitude": 1.0, "phase": 2.0}],
        },
    }
    cmp_model = CmpModel(**data)
    return cmp_model


@pytest.fixture
def reference() -> str:
    return (
        "# written by HYDROLIB-core 0.8.1\n\n"
        "[General]\n"
        "fileVersion = 1.01\n"
        "fileType    = boundConds\n\n"
        "[Forcing]\n"
        "name     = boundary_harmonic\n"
        "function = harmonic\n"
        "factor   = 1.0\n"
        "quantity = harmonic component\n"
        "unit     = minutes\n"
        "quantity = waterlevelbnd amplitude\n"
        "unit     = m\n"
        "quantity = waterlevelbnd phase\n"
        "unit     = deg\n"
        "0.0  1.0  2.0\n\n"
        "[Forcing]\n"
        "name     = boundary_astronomic\n"
        "function = astronomic\n"
        "factor   = 1.0\n"
        "quantity = astronomic component\n"
        "unit     = string\n"
        "quantity = waterlevelbnd amplitude\n"
        "unit     = m\n"
        "quantity = waterlevelbnd phase\n"
        "unit     = deg\n"
        "4MS10  1.0  2.0\n\n"
    )


def test_cmp_to_forcing_converter(cmp_model):
    # Convert CmpModel to ForcingModel
    forcing_model = CmpToForcingConverter.convert(cmp_model)

    # Expected ForcingModel
    expected_forcing_model = ForcingModel(
        forcing=[
            Harmonic(
                name="boundary_harmonic",
                function="harmonic",
                quantityunitpair=[
                    QuantityUnitPair(quantity="harmonic component", unit="minutes"),
                    QuantityUnitPair(quantity="waterlevelbnd amplitude", unit="m"),
                    QuantityUnitPair(quantity="waterlevelbnd phase", unit="deg"),
                ],
                datablock=[[0.0, 1.0, 2.0]],
            ),
            Astronomic(
                name="boundary_astronomic",
                function="astronomic",
                quantityunitpair=[
                    QuantityUnitPair(quantity="astronomic component", unit="string"),
                    QuantityUnitPair(quantity="waterlevelbnd amplitude", unit="m"),
                    QuantityUnitPair(quantity="waterlevelbnd phase", unit="deg"),
                ],
                datablock=[["4MS10", 1.0, 2.0]],
            ),
        ]
    )
    assert forcing_model == expected_forcing_model


def test_cmp_to_forcing_converter_file(
    cmp_model: CmpModel, reference: str, fs: FakeFilesystem
):
    # Convert CmpModel to ForcingModel and save to file
    converted_bc_path = Path("tests/data/output/converted.bc")
    reference_bc_path = Path("tests/data/reference/reference.bc")
    CmpToForcingConverter.convert(cmp_model).save(converted_bc_path)
    with open(converted_bc_path, "r") as f:
        print(f.read())
    fs.create_file(reference_bc_path, contents=reference)
    diff = compare_two_files(converted_bc_path, reference_bc_path)
    assert diff == []
