from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pytest
from devtools import debug

from hydrolib.core.io.bc.models import ForcingBase, ForcingModel
from hydrolib.core.io.dimr.models import (
    DIMR,
    ComponentOrCouplerRef,
    Control,
    CoupledItem,
    Coupler,
    FMComponent,
    Logger,
    Parallel,
    RRComponent,
    StartGroup,
)
from hydrolib.core.io.fnm.models import RainfallRunoffModel
from hydrolib.core.io.mdu.models import Boundary, ExtModel, FMModel
from hydrolib.core.io.xyz.models import XYZModel

from .utils import test_data_dir, test_input_dir, test_output_dir, test_reference_dir
from .io.test_bui import BuiTestData


def test_dimr_model():
    test_file = (
        test_data_dir
        / "input"
        / "e02"
        / "c11_korte-woerden-1d"
        / "dimr_model"
        / "dimr_config.xml"
    )
    # Confirm parsing results in correct
    # components for each type of submodel
    d = DIMR(filepath=test_file)
    assert len(d.component) == 2
    assert isinstance(d.component[0], RRComponent)
    assert isinstance(d.component[1], FMComponent)

    # Confirm saving creates new files and
    # files for child model
    d.save(folder=test_output_dir / "tmp")
    assert d.filepath.is_file()
    assert d.component[1].model.filepath.is_file()


def test_parse_rr_model_returns_correct_model():
    test_file = test_input_dir / "rr_sample_trimmed" / "dimr_config.xml"
    result = DIMR(filepath=test_file)

    assert len(result.component) == 1

    model = result.component[0].model
    assert isinstance(model, RainfallRunoffModel)

    # verify some non-default names altered in the source file.
    assert model.control_file == Path("not-delft_3b.ini")
    assert model.bui_file == BuiTestData.bui_model()
    assert model.rr_ascii_restart_openda == Path("ASCIIRestartOpenDA.txt")


def test_dimr_validate():
    d = DIMR(
        coupler={
            "name": "test",
            "sourcecomponent": "test",
            "targetcomponent": "test",
            "item": [],
        }
    )
    assert isinstance(d.coupler, list)
    assert len(d.coupler) == 1


def test_initialize_default_dimr_does_not_raise_exception():
    DIMR()


def test_dimr_model_save():
    file = Path(test_output_dir / "model" / "test_dimr_model_save.xml")
    reference_file = Path(test_reference_dir / "model" / "test_dimr_model_save.xml")

    dimr = DIMR()
    dimr.documentation.creationDate = datetime(2021, 7, 29, 12, 45)
    dimr.control = Control()
    dimr.control.parallel.append(
        Parallel(
            startGroup=StartGroup(
                time="0 60 7200",
                start=ComponentOrCouplerRef(name="Rainfall Runoff"),
                coupler=ComponentOrCouplerRef(name="rr_to_flow"),
            ),
            start=ComponentOrCouplerRef(name="FlowFM"),
        )
    )

    dimr.component.append(
        RRComponent(
            name="Rainfall Runoff",
            library="rr_dll",
            workingDir="rr",
            inputFile="Sobek_3b.fnm",
        )
    )
    dimr.component.append(
        FMComponent(
            name="FlowFM",
            library="dflowfm",
            workingDir="dflowfm",
            inputFile="FlowFM.mdu",
        )
    )

    dimr.coupler.append(
        Coupler(
            name="rr_to_flow",
            sourceComponent="Rainfall Runoff",
            targetComponent="FlowFM",
            logger=Logger(workingDir=".", outputFile="rr_to_flow.nc"),
        )
    )

    dimr.coupler[0].item.append(
        CoupledItem(
            sourceName="catchments/10634/water_discharge",
            targetName="laterals/10634/water_discharge",
        )
    )
    dimr.coupler[0].item.append(
        CoupledItem(
            sourceName="catchments/10635/water_discharge",
            targetName="laterals/10635/water_discharge",
        )
    )

    dimr.filepath = file
    dimr.save()

    assert file.is_file() == True

    with file.open() as af:
        actual_lines = af.readlines()

    with reference_file.open() as rf:
        reference_lines = rf.readlines()

    assert len(actual_lines) == len(reference_lines)

    for i in range(len(reference_lines)):
        assert actual_lines[i] == reference_lines[i]


def test_xyz_model():
    output_fn = Path(test_output_dir / "test.xyz")
    if output_fn.is_file():
        output_fn.unlink()

    # Confirm succesfull parse and initialization
    model = XYZModel(filepath=Path(test_data_dir / "input/test.xyz"))
    assert len(model.points) == 7, model

    # Confirm saving to new file
    model.filepath = output_fn
    assert not model.filepath.is_file()
    model.save()
    assert model.filepath.is_file()


def test_mdu_model():
    output_fn = Path(test_output_dir / "test.mdu")
    if output_fn.is_file():
        output_fn.unlink()

    model = FMModel(
        filepath=Path(
            test_data_dir
            / "input"
            / "e02"
            / "c11_korte-woerden-1d"
            / "dimr_model"
            / "dflowfm"
            / "FlowFM.mdu"
        )
    )
    assert model.geometry.comments.uniformwidth1d == "test"

    model.filepath = output_fn
    model.save()

    assert model.filepath.is_file()
    assert model.geometry.frictfile[0].filepath.is_file()
    assert model.geometry.structurefile[0].filepath.is_file()


def test_model_with_duplicate_file_references_use_same_instances():
    model = ExtModel(
        filepath=Path(
            test_data_dir
            / "input"
            / "e02"
            / "c11_korte-woerden-1d"
            / "dimr_model"
            / "dflowfm"
            / "FlowFM_bnd.ext"
        )
    )

    boundary1 = model.boundary[0]
    boundary2 = model.boundary[1]

    # Set a field for first boundary
    boundary1.forcingfile.forcing[0].name = "some_new_value"

    # Field for second boundary is also updated (same instance)
    assert boundary2.forcingfile.forcing[0].name == "some_new_value"


def test_mdu_from_scratch():
    output_fn = Path(test_output_dir / "scratch.mdu")
    model = FMModel()
    model.filepath = output_fn
    model.save()


def test_boundary_with_forcingfile_returns_forcing():
    forcing1 = _create_forcing("bnd1", "waterlevelbnd")
    forcing2 = _create_forcing("bnd2", "dischargebnd")
    forcing3 = _create_forcing("bnd3", "qhbnd discharge")

    forcingfile = ForcingModel(forcing=[forcing1, forcing2, forcing3])

    boundary2 = Boundary(
        nodeId="bnd2", quantity="dischargebnd", forcingfile=forcingfile
    )

    assert boundary2.forcing is forcing2


def test_boundary_without_forcingfile_returns_none():
    boundary = Boundary(nodeId="boundary", quantity="waterlevelbnd")

    assert boundary.forcingfile is None
    assert boundary.forcing is None


def test_boundary_with_forcingfile_without_match_returns_none():
    forcing1 = _create_forcing("bnd1", "waterlevelbnd")
    forcing2 = _create_forcing("bnd2", "dischargebnd")

    forcingfile = ForcingModel(forcing=[forcing1, forcing2])

    boundary = Boundary(nodeId="bnd3", quantity="qhbnd", forcingfile=forcingfile)

    assert boundary.forcing is None


def _create_forcing(name: str, quantity: str) -> ForcingBase:
    return ForcingBase(name=name, quantity=[quantity], function="", unit=[])
