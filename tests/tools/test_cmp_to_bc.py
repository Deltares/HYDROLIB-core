from pathlib import Path

import pytest

from hydrolib.core.dflowfm.bc.models import (
    Astronomic,
    ForcingModel,
    Harmonic,
    QuantityUnitPair,
)
from hydrolib.core.dflowfm.cmp.models import CMPModel
from hydrolib.tools.extforce_convert.converters import CMPToForcingConverter
from tests.utils import compare_two_files


@pytest.fixture
def cmp_model() -> CMPModel:
    data = {
        "comments": ["# Example comment"],
        "components": [
            {
                "harmonics": [
                    {"period": 0.0, "amplitude": 1.0, "phase": 2.0},
                    {"period": 3.0, "amplitude": 2.0, "phase": 1.0},
                ],
            },
            {
                "astronomics": [
                    {"name": "4MS10", "amplitude": 1.0, "phase": 2.0},
                    {"name": "KO0", "amplitude": 1.0, "phase": 2.0},
                ],
            },
        ],
        "quantities_names": ["dischargebnd", "waterlevelbnd"],
    }
    cmp_model = CMPModel(**data)
    return cmp_model


@pytest.fixture
def cmp_file(tmpdir: Path) -> Path:
    cmp_file = tmpdir / "test.cmp"
    with open(cmp_file, "w") as file:
        file.write(
            "#test content\n0.0  1.0  2.0\n3.0  2.0  1.0\n4MS10  1.0  2.0\nKO0    1.0  2.0\n"
        )
    return cmp_file


@pytest.fixture
def reference_path(tmpdir: Path) -> Path:
    reference_path = tmpdir / "reference.bc"
    with open(reference_path, "w") as file:
        file.write(
            "# written by HYDROLIB-core 0.8.1\n\n"
            "[General]\n"
            "fileVersion = 1.01\n"
            "fileType    = boundConds\n\n"
            "[Forcing]\n"
            "name     = waterlevelbnd\n"
            "function = harmonic\n"
            "factor   = 1.0\n"
            "quantity = harmonic component\n"
            "unit     = minutes\n"
            "quantity = waterlevelbnd\n"
            "unit     = m\n"
            "quantity = waterlevelbnd\n"
            "unit     = deg\n"
            "0.0  1.0  2.0\n"
            "3.0  2.0  1.0\n\n"
            "[Forcing]\n"
            "name     = waterlevelbnd\n"
            "function = astronomic\n"
            "factor   = 1.0\n"
            "quantity = astronomic component\n"
            "unit     = -\n"
            "quantity = waterlevelbnd\n"
            "unit     = m\n"
            "quantity = waterlevelbnd\n"
            "unit     = deg\n"
            "4MS10  1.0  2.0\n"
            "KO0    1.0  2.0\n"
        )
    return reference_path


def test_cmp_to_forcing_converter(cmp_model: CMPModel):
    # Convert CmpModel to ForcingModel
    forcing_model = CMPToForcingConverter.convert(cmp_model)

    # Expected ForcingModel
    expected_forcing_model = [
        Harmonic(
            name="dischargebnd",
            function="harmonic",
            quantityunitpair=[
                QuantityUnitPair(quantity="harmonic component", unit="minutes"),
                QuantityUnitPair(quantity="dischargebnd", unit="m3/s"),
                QuantityUnitPair(quantity="dischargebnd", unit="deg"),
            ],
            datablock=[[0.0, 1.0, 2.0], [3.0, 2.0, 1.0]],
        ),
        Astronomic(
            name="waterlevelbnd",
            function="astronomic",
            quantityunitpair=[
                QuantityUnitPair(quantity="astronomic component", unit="-"),
                QuantityUnitPair(quantity="waterlevelbnd", unit="m"),
                QuantityUnitPair(quantity="waterlevelbnd", unit="deg"),
            ],
            datablock=[["4MS10", 1.0, 2.0], ["KO0", 1.0, 2.0]],
        ),
    ]
    assert forcing_model == expected_forcing_model


def test_cmp_to_forcing_converter_file(
    cmp_file: Path, reference_path: Path, tmpdir: Path
):
    cmp_model = CMPModel(cmp_file)
    cmp_model.quantities_names = ["waterlevelbnd"]

    converted_bc_path = tmpdir / "converted.bc"
    model = CMPToForcingConverter.convert(cmp_model)
    forcing = ForcingModel(forcing=model)
    forcing.save(converted_bc_path)

    diff = compare_two_files(converted_bc_path, reference_path)
    assert diff == []
