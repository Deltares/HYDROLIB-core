from pathlib import Path

import pytest

from hydrolibcore import __version__
from hydrolibcore.io.dimr.models import DIMR
from hydrolibcore.io.dimr.parser import DIMRParser
from hydrolibcore.io.dimr.serializer import DIMRSerializer
from tests.utils import (
    assert_files_equal,
    test_input_dir,
    test_output_dir,
    test_reference_dir,
)


def test_parse_returns_correct_data():
    test_file = (
        test_input_dir
        / "e02"
        / "c11_korte-woerden-1d"
        / "dimr_model"
        / "dimr_config.xml"
    )
    result = DIMRParser.parse(test_file)

    documentation = result["documentation"]
    assert documentation["fileVersion"] == "1.2"
    assert documentation["createdBy"] == "Deltares, Coupling Team"
    assert documentation["creationDate"] == "2020-03-17T10:02:49.4520672Z"

    start_group = result["control"]["parallel"]["startGroup"]
    assert start_group["time"] == "0 60 7200"
    assert start_group["start"]["name"] == "Rainfall Runoff"
    assert start_group["coupler"]["name"] == "rr_to_flow"

    components = result["component"]
    assert isinstance(components, list)
    assert len(components) == 2
    assert components[0]["name"] == "Rainfall Runoff"
    assert components[0]["library"] == "rr_dll"
    assert components[0]["workingDir"] == "rr"
    assert components[0]["inputFile"] == "Sobek_3b.fnm"
    assert components[1]["name"] == "FlowFM"
    assert components[1]["library"] == "dflowfm"
    assert components[1]["workingDir"] == "dflowfm"
    assert components[1]["inputFile"] == "FlowFM.mdu"

    assert result["coupler"]["name"] == "rr_to_flow"
    assert result["coupler"]["sourceComponent"] == "Rainfall Runoff"
    assert result["coupler"]["targetComponent"] == "FlowFM"

    items = result["coupler"]["item"]
    assert isinstance(items, list)
    assert len(items) == 72

    assert items[0]["sourceName"] == "catchments/10634/water_discharge"
    assert items[0]["targetName"] == "laterals/10634/water_discharge"
    assert items[1]["sourceName"] == "catchments/10635/water_discharge"
    assert items[1]["targetName"] == "laterals/10635/water_discharge"
    assert items[70]["sourceName"] == "catchments/13697/water_discharge"
    assert items[70]["targetName"] == "laterals/13697/water_discharge"
    assert items[71]["sourceName"] == "catchments/16650Bc2/water_discharge"
    assert items[71]["targetName"] == "laterals/16650Bc2/water_discharge"


def test_parse_when_file_does_not_exist_raises_exception():
    with pytest.warns(UserWarning):
        DIMRParser.parse(Path("does/not/exist.xml"))


def test_serialize():
    file = Path(test_output_dir / "dimr" / "test_serialize.xml")
    reference_file = Path(test_reference_dir / "dimr" / "test_serialize.xml")

    data = {
        "documentation": {
            "fileVersion": "1.3",
            "createdBy": f"hydrolib-core {__version__}",
            "creationDate": "2020-03-17T10:02:49.4520672Z",
        },
        "control": {
            "parallel": {
                "startGroup": {
                    "time": "0 60 7200",
                    "start": {"name": "Rainfall Runoff"},
                    "coupler": {"name": "rr_to_flow"},
                },
                "start": {"name": "FlowFM"},
            }
        },
        "component": [
            {
                "name": "Rainfall Runoff",
                "library": "rr_dll",
                "workingDir": "rr",
                "inputFile": "Sobek_3b.fnm",
            },
            {
                "name": "FlowFM",
                "library": "dflowfm",
                "workingDir": "dflowfm",
                "inputFile": "FlowFM.mdu",
            },
        ],
        "coupler": {
            "name": "rr_to_flow",
            "sourceComponent": "Rainfall Runoff",
            "targetComponent": "FlowFM",
            "item": [
                {
                    "sourceName": "catchments/10634/water_discharge",
                    "targetName": "laterals/10634/water_discharge",
                },
                {
                    "sourceName": "catchments/10635/water_discharge",
                    "targetName": "laterals/10635/water_discharge",
                },
            ],
            "logger": {"workingDir": ".", "outputFile": "rr_to_flow.nc"},
        },
    }

    DIMRSerializer.serialize(file, data)

    assert file.is_file()
    assert_files_equal(file, reference_file)
