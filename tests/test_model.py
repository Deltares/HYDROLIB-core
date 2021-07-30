from pathlib import Path

import pytest
from devtools import debug

from hydrolib.core.io.dimr.models import DIMR, FMComponent, RRComponent
from hydrolib.core.io.mdu.models import FMModel
from hydrolib.core.io.xyz.models import XYZModel

from .utils import test_data_dir, test_output_dir


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
    debug(model)
    model.filepath = output_fn
    model.save()
    assert model.filepath.is_file()
