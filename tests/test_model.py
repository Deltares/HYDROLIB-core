import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Union

import pytest
from pydantic.v1.error_wrappers import ValidationError

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingBase, ForcingModel, QuantityUnitPair
from hydrolib.core.dflowfm.ext.models import Boundary, ExtModel
from hydrolib.core.dflowfm.friction.models import FrictGeneral
from hydrolib.core.dflowfm.mdu.models import (
    Calibration,
    ExternalForcing,
    FMModel,
    Geometry,
    Output,
    Particles,
    Processes,
    Restart,
    Sediment,
)
from hydrolib.core.dflowfm.xyz.models import XYZModel
from hydrolib.core.dimr.models import (
    DIMR,
    ComponentOrCouplerRef,
    CoupledItem,
    Coupler,
    FMComponent,
    Logger,
    Parallel,
    RRComponent,
    StartGroup,
)
from hydrolib.core.rr.models import RainfallRunoffModel

from .rr.meteo.test_bui import BuiTestData
from .utils import (
    assert_files_equal,
    invalid_test_data_dir,
    test_data_dir,
    test_input_dir,
    test_output_dir,
    test_reference_dir,
)


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
    save_path = test_output_dir / test_dimr_model.__name__ / DIMR._generate_name()

    d.save(filepath=save_path, recurse=True)

    assert d.save_location == save_path
    assert d.save_location.is_file()

    assert d.component[1].model is not None
    assert d.component[1].model.save_location.is_file()


def test_parse_rr_model_returns_correct_model():
    test_file = test_input_dir / "rr_sample_trimmed" / "dimr_config.xml"
    result = DIMR(filepath=test_file)

    assert len(result.component) == 1

    model = result.component[0].model
    assert isinstance(model, RainfallRunoffModel)

    # verify some non-default names altered in the source file.
    assert model.control_file.filepath == Path("not-delft_3b.ini")

    expected_bui_model = BuiTestData.bui_model()
    # we expect the path to not be absolute, as such we need to adjust that.
    expected_bui_model.filepath = Path(expected_bui_model.filepath.name)
    assert model.bui_file == expected_bui_model
    assert model.rr_ascii_restart_openda.filepath == Path("ASCIIRestartOpenDA.txt")


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
    dimr.control.append(
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
    assert_files_equal(file, reference_file)


def test_mdu_model():
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

    output_dir = test_output_dir / test_mdu_model.__name__
    output_fn = output_dir / FMModel._generate_name()

    if output_dir.exists():
        shutil.rmtree(output_dir)

    model.save(filepath=output_fn, recurse=True)

    assert model.save_location == output_fn
    assert model.save_location.is_file()

    assert model.geometry.frictfile is not None
    frictfile = model.geometry.frictfile[0]
    assert model.geometry.frictfile[0] is not None
    assert model.geometry.frictfile[0].filepath is not None

    assert frictfile.save_location == output_dir / frictfile.filepath
    assert frictfile.save_location.is_file()

    assert model.geometry.structurefile is not None
    structurefile = model.geometry.structurefile[0]
    assert structurefile is not None
    assert structurefile.filepath is not None

    assert structurefile.save_location == output_dir / structurefile.filepath
    assert structurefile.save_location.is_file()


def test_load_model_recurse_false():
    model = FMModel(
        filepath=Path(
            test_data_dir
            / "input"
            / "e02"
            / "c11_korte-woerden-1d"
            / "dimr_model"
            / "dflowfm"
            / "FlowFM.mdu"
        ),
        recurse=False,
    )

    # Assert that references to child models are preserved, but child models are not loaded
    assert model.geometry.structurefile is not None
    assert len(model.geometry.structurefile) == 1
    assert model.geometry.structurefile[0].filepath == Path("structures.ini")
    assert not any(model.geometry.structurefile[0].structure)


def test_model_with_duplicate_file_references_use_same_instances():
    model = ExtModel(
        filepath=(
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


@pytest.mark.filterwarnings("ignore:File.*not found:UserWarning")
def test_read_ext_missing_boundary_field_raises_correct_error():
    file = "missing_boundary_field.ext"
    identifier = "Boundary2"
    field = "quantity"

    filepath = invalid_test_data_dir / file

    with pytest.raises(ValidationError) as error:
        ExtModel(filepath)

    expected_message = f"{file} -> boundary -> 1 -> {identifier} -> {field}"
    assert expected_message in str(error.value)


def test_read_ext_missing_lateral_field_raises_correct_error():
    file = "missing_lateral_field.ext"
    identifier = "Lateral2"
    field = "discharge"

    filepath = invalid_test_data_dir / file

    with pytest.raises(ValidationError) as error:
        ExtModel(filepath)

    expected_message = f"{file} -> lateral -> 1 -> {identifier} -> {field}"
    assert expected_message in str(error.value)


def test_read_dimr_missing_component_field_raises_correct_error():
    file = "missing_dimr_component_field.xml"
    identifier = "FlowFM"
    field = "workingdir"

    filepath = invalid_test_data_dir / file

    with pytest.raises(ValidationError) as error:
        DIMR(filepath)

    expected_message = f"{file} -> component -> 1 -> {identifier} -> {field}"
    assert expected_message in str(error.value)


def test_read_dimr_missing_coupler_field_raises_correct_error():
    file = "missing_dimr_coupler_field.xml"
    identifier = "rr_to_flow"
    field = "targetcomponent"

    filepath = invalid_test_data_dir / file

    with pytest.raises(ValidationError) as error:
        DIMR(filepath)

    expected_message = f"{file} -> coupler -> 0 -> {identifier} -> {field}"
    assert expected_message in str(error.value)


def test_boundary_with_forcing_file_returns_forcing():
    forcing1 = _create_forcing("bnd1", "waterlevelbnd")
    forcing2 = _create_forcing("bnd2", "dischargebnd")
    forcing3 = _create_forcing("bnd3", "qhbnd discharge")

    forcing_file = ForcingModel(forcing=[forcing1, forcing2, forcing3])

    boundary2 = Boundary(
        nodeid="bnd2", quantity="dischargebnd", forcingfile=forcing_file
    )

    assert boundary2.forcing is forcing2


def test_boundary_with_forcing_file_without_match_returns_none():
    forcing1 = _create_forcing("bnd1", "waterlevelbnd")
    forcing2 = _create_forcing("bnd2", "dischargebnd")

    forcing_file = ForcingModel(forcing=[forcing1, forcing2])

    boundary = Boundary(nodeid="bnd3", quantity="qhbnd", forcingfile=forcing_file)

    assert boundary.forcing is None
    assert boundary.nodeid == "bnd3"
    assert boundary.quantity == "qhbnd"


def _create_forcing(name: str, quantity: str) -> ForcingBase:
    return ForcingBase(
        name=name,
        quantityunitpair=[QuantityUnitPair(quantity=quantity, unit="")],
        function="",
    )


def _create_boundary(data: Dict) -> Boundary:
    data["quantity"] = ""
    data["forcingfile"] = ForcingModel()

    if data["locationfile"] is None:
        data["nodeid"] = "id"

    return Boundary(**data)


@pytest.mark.parametrize(
    "input",
    [
        pytest.param(None, id="None"),
        pytest.param(Path("some/path/extforce.file"), id="Path"),
        pytest.param(
            DiskOnlyFileModel(Path("some/other/path/extforce.file")), id="Model"
        ),
    ],
)
@pytest.mark.parametrize(
    "input_field, create_model, retrieve_field",
    [
        pytest.param(
            "restartfile",
            lambda d: Restart(**d),
            lambda m: m.restartfile,
            id="restartfile",
        ),
        pytest.param(
            "morfile", lambda d: Sediment(**d), lambda m: m.morfile, id="morfile"
        ),
        pytest.param(
            "sedfile", lambda d: Sediment(**d), lambda m: m.sedfile, id="sedfile"
        ),
        pytest.param(
            "flowgeomfile",
            lambda d: Output(**d),
            lambda m: m.flowgeomfile,
            id="flowgeomfile",
        ),
        pytest.param(
            "hisfile", lambda d: Output(**d), lambda m: m.hisfile, id="hisfile"
        ),
        pytest.param(
            "mapfile", lambda d: Output(**d), lambda m: m.mapfile, id="mapfile"
        ),
        pytest.param(
            "mapoutputtimevector",
            lambda d: Output(**d),
            lambda m: m.mapoutputtimevector,
            id="mapoutputtimevector",
        ),
        pytest.param(
            "classmapfile",
            lambda d: Output(**d),
            lambda m: m.classmapfile,
            id="classmapfile",
        ),
        pytest.param(
            "waterlevinifile",
            lambda d: Geometry(**d),
            lambda m: m.waterlevinifile,
            id="waterlevinifile",
        ),
        pytest.param(
            "oned2dlinkfile",
            lambda d: Geometry(**d),
            lambda m: m.oned2dlinkfile,
            id="oned2dlinkfile",
        ),
        pytest.param(
            "proflocfile",
            lambda d: Geometry(**d),
            lambda m: m.proflocfile,
            id="proflocfile",
        ),
        pytest.param(
            "profdeffile",
            lambda d: Geometry(**d),
            lambda m: m.profdeffile,
            id="profdeffile",
        ),
        pytest.param(
            "profdefxyzfile",
            lambda d: Geometry(**d),
            lambda m: m.profdefxyzfile,
            id="profdefxyzfile",
        ),
        pytest.param(
            "manholefile",
            lambda d: Geometry(**d),
            lambda m: m.manholefile,
            id="manholefile",
        ),
        pytest.param(
            "definitionfile",
            lambda d: Calibration(**d),
            lambda m: m.definitionfile,
            id="definitionfile",
        ),
        pytest.param(
            "areafile",
            lambda d: Calibration(**d),
            lambda m: m.areafile,
            id="definitionfile",
        ),
        pytest.param(
            "substancefile",
            lambda d: Processes(**d),
            lambda m: m.substancefile,
            id="substancefile",
        ),
        pytest.param(
            "additionalhistoryoutputfile",
            lambda d: Processes(**d),
            lambda m: m.additionalhistoryoutputfile,
            id="additionalhistoryoutputfile",
        ),
        pytest.param(
            "statisticsfile",
            lambda d: Processes(**d),
            lambda m: m.statisticsfile,
            id="statisticsfile",
        ),
        pytest.param(
            "particlesreleasefile",
            lambda d: Particles(**d),
            lambda m: m.particlesreleasefile,
            id="particlesreleasefile",
        ),
        pytest.param(
            "locationfile",
            _create_boundary,
            lambda m: m.locationfile,
            id="locationfile",
        ),
        pytest.param(
            "frictionvaluesfile",
            lambda d: FrictGeneral(**d),
            lambda m: m.frictionvaluesfile,
            id="frictionvaluesfile",
        ),
    ],
)
def test_model_diskonlyfilemodel_field_is_constructed_correctly(
    input: Union[None, Path, DiskOnlyFileModel],
    input_field: str,
    create_model: Callable[[Dict], object],
    retrieve_field: Callable[[object], DiskOnlyFileModel],
):
    data = {input_field: input}
    model = create_model(data)
    relevant_field = retrieve_field(model)

    assert isinstance(relevant_field, DiskOnlyFileModel)

    if isinstance(input, DiskOnlyFileModel):
        assert relevant_field == input
    else:
        assert relevant_field.filepath == input


@pytest.mark.parametrize(
    "input_process, expected_process_format",
    [
        pytest.param(1, "0"),
        pytest.param(2, "0 1"),
        pytest.param(3, "0 1 2"),
        pytest.param(4, "0 1 2 3"),
        pytest.param(5, "0 1 2 3 4"),
    ],
)
def test_dimr_with_fmcomponent_saving_process(
    tmp_path, input_process: int, expected_process_format: str
):
    component = FMComponent(
        name="test",
        workingDir=".",
        inputfile="test.mdu",
        process=input_process,
        mpiCommunicator="DFM_COMM_DFMWORLD",
    )
    dimr = DIMR(component=component)
    save_location: Path = tmp_path / "dimr_config.xml"
    dimr.save(filepath=save_location)

    line_to_check = f"<process>{expected_process_format}</process>"

    with open(save_location, "r") as file:
        assert any(
            line.strip() == line_to_check for line in file
        ), f"File {save_location} does not contain the line: {line_to_check}"


def test_dimr_with_fmcomponent_saving_process_when_process_zero(tmp_path):
    component = FMComponent(
        name="test",
        workingDir=".",
        inputfile="test.mdu",
        process=0,
        mpiCommunicator="DFM_COMM_DFMWORLD",
    )
    dimr = DIMR(component=component)
    save_location: Path = tmp_path / "dimr_config.xml"
    dimr.save(filepath=save_location)

    process = "<process>"

    with open(save_location, "r") as file:
        assert (
            process not in file
        ), f"File {save_location} does contain the line: {process}"


@pytest.mark.parametrize(
    "input_process, expected_process_format",
    [
        pytest.param(0, None),
        pytest.param(1, "0"),
        pytest.param(2, "0 1"),
        pytest.param(3, "0 1 2"),
        pytest.param(4, "0 1 2 3"),
        pytest.param(5, "0 1 2 3 4"),
    ],
)
def test_fmcomponent_process_after_init(
    input_process: int, expected_process_format: str
):
    component = FMComponent(
        name="test",
        workingDir=".",
        inputfile="test.mdu",
        process=input_process,
        mpiCommunicator="DFM_COMM_DFMWORLD",
    )
    assert component.process == expected_process_format
