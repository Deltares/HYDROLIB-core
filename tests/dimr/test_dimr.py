from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from hydrolib.core import __version__
from hydrolib.core.base.models import ModelSaveSettings, SerializerConfig
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
from hydrolib.core.dimr.parser import DIMRParser
from hydrolib.core.dimr.serializer import DIMRSerializer
from hydrolib.core.rr.models import RainfallRunoffModel
from tests.rr.meteo.test_bui import BuiTestData
from tests.utils import (
    assert_files_equal,
    invalid_test_data_dir,
    test_data_dir,
    test_input_dir,
    test_output_dir,
    test_reference_dir,
)


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


def test_dimr_model_save(output_files_dir: Path, reference_files_dir: Path):
    file = output_files_dir / "model/test_dimr_model_save.xml"
    reference_file = reference_files_dir / "model/test_dimr_model_save.xml"

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


def test_read_dimr_missing_component_field_raises_correct_error():
    file = "missing_dimr_component_field.xml"

    filepath = invalid_test_data_dir / file

    with pytest.raises(ValidationError) as error:
        DIMR(filepath)

    expected_message = f"`{file}`.component.1.dflowfm.FlowFM.workingdir"
    assert expected_message in str(error.value)


def test_read_dimr_missing_coupler_field_raises_correct_error():
    file = "missing_dimr_coupler_field.xml"

    filepath = invalid_test_data_dir / file

    with pytest.raises(ValidationError) as error:
        DIMR(filepath)

    expected_message = f"`{file}`.coupler.0.rr_to_flow.targetcomponent"
    assert expected_message in str(error.value)


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

    DIMRSerializer.serialize(
        file, data, config=SerializerConfig(), save_settings=ModelSaveSettings()
    )

    assert file.is_file()
    assert_files_equal(file, reference_file)


def test_serialize_float_are_formatted():
    data = {"some_key": 1.23456}

    file_path = Path(
        test_output_dir / "dimr" / "test_serialize_float_are_formatted.xml"
    )
    reference_file = Path(
        test_reference_dir / "dimr" / "test_serialize_float_are_formatted.xml"
    )

    config = SerializerConfig(float_format=".2f")
    DIMRSerializer.serialize(file_path, data, config, save_settings=ModelSaveSettings())

    assert file_path.is_file()
    assert_files_equal(file_path, reference_file)


class TestFmComponentProcess:
    @pytest.mark.parametrize(
        "input_process",
        [
            pytest.param(None),
            pytest.param(1),
            pytest.param(2),
            pytest.param(3),
            pytest.param(4),
            pytest.param(5),
        ],
    )
    def test_fmcomponent_process_after_init(self, input_process: int):
        component = FMComponent(
            name="test",
            workingDir=".",
            inputfile="test.mdu",
            process=input_process,
            mpiCommunicator="DFM_COMM_DFMWORLD",
        )
        assert component.process == input_process

    @pytest.mark.parametrize(
        "input_process",
        [
            pytest.param(None),
            pytest.param(1),
            pytest.param(2),
            pytest.param(3),
            pytest.param(4),
            pytest.param(5),
        ],
    )
    def test_fmcomponent_process_after_setting(self, input_process: int):
        component = FMComponent(
            name="test",
            workingDir=".",
            inputfile="test.mdu",
            mpiCommunicator="DFM_COMM_DFMWORLD",
        )
        component.process = input_process
        assert component.process == input_process

    def test_fmcomponent_without_process_after_init(self):
        expected_process_format = None
        component = FMComponent(
            name="test",
            workingDir=".",
            inputfile="test.mdu",
            mpiCommunicator="DFM_COMM_DFMWORLD",
        )
        assert component.process == expected_process_format

    @pytest.mark.parametrize(
        "input_process",
        [
            pytest.param("lalala"),
            pytest.param("123"),
            pytest.param(3.5),
        ],
    )
    def test_fmcomponent_process_after_init_with_invalid_type_input_raises_value_error(
        self,
        input_process,
    ):
        with pytest.raises(ValueError) as error:
            FMComponent(
                name="test",
                workingDir=".",
                inputfile="test.mdu",
                process=input_process,
                mpiCommunicator="DFM_COMM_DFMWORLD",
            )

        expected_message = (
            f"In component 'test', the keyword process '{input_process}', is incorrect."
        )
        assert expected_message in str(error.value)

    @pytest.mark.parametrize(
        "input_process",
        [
            pytest.param(0),
            pytest.param(-1),
            pytest.param(-3),
        ],
    )
    def test_fmcomponent_process_after_init_with_input_process_zero_or_negative_raises_value_error(
        self,
        input_process: int,
    ):
        with pytest.raises(ValueError) as error:
            FMComponent(
                name="test",
                workingDir=".",
                inputfile="test.mdu",
                process=input_process,
                mpiCommunicator="DFM_COMM_DFMWORLD",
            )

        expected_message = "In component 'test', the keyword process can not be 0 or negative, please specify value of 1 or greater."
        assert expected_message in str(error.value)


class TestFmComponentProcessIntegrationWithDimr:
    def get_fm_dimr_config_data(self, input_data_process):
        return f"""<?xml version="1.0" encoding="utf-8"?>
<dimrConfig xmlns="http://schemas.deltares.nl/dimr" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://schemas.deltares.nl/dimr http://content.oss.deltares.nl/schemas/dimr-1.3.xsd">
  <documentation>
    <fileVersion>1.3</fileVersion>
    <createdBy>hydrolib-core 0.7.0</createdBy>
    <creationDate>2024-04-25T10:59:21.185365</creationDate>
  </documentation>
  <component name="test">
    <library>dflowfm</library>
    <workingDir>.</workingDir>
    <inputFile>test.mdu</inputFile>
    <process>{input_data_process}</process>
    <mpiCommunicator>DFM_COMM_DFMWORLD</mpiCommunicator>
  </component>
</dimrConfig>
"""

    def get_fm_dimr_config_data_without_process(self):
        return """<?xml version="1.0" encoding="utf-8"?>
<dimrConfig xmlns="http://schemas.deltares.nl/dimr" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://schemas.deltares.nl/dimr http://content.oss.deltares.nl/schemas/dimr-1.3.xsd">
  <documentation>
    <fileVersion>1.3</fileVersion>
    <createdBy>hydrolib-core 0.7.0</createdBy>
    <creationDate>2024-04-25T10:59:21.185365</creationDate>
  </documentation>
  <component name="test">
    <library>dflowfm</library>
    <workingDir>.</workingDir>
    <inputFile>test.mdu</inputFile>
    <mpiCommunicator>DFM_COMM_DFMWORLD</mpiCommunicator>
  </component>
</dimrConfig>
"""

    def setup_temporary_files(self, tmp_path, dimr_config_data):
        temporary_dimr_config_file = tmp_path / "dimr_config.xml"
        temporary_dimr_config_file.write_text(dimr_config_data)

        temp_mdu = tmp_path / "test.mdu"
        temp_mdu.write_text("")
        temporary_save_location = tmp_path / "saved_dimr_config.xml"
        return temporary_dimr_config_file, temporary_save_location

    def test_dimr_with_fmcomponent_given_correct_style_for_setting_process_without_process(
        self, tmp_path
    ):
        dimr_config_data = self.get_fm_dimr_config_data_without_process()

        (
            temporary_dimr_config_file,
            temporary_save_location,
        ) = self.setup_temporary_files(tmp_path, dimr_config_data)

        dimr_config = DIMR(filepath=temporary_dimr_config_file)
        dimr_config.save(filepath=temporary_save_location)

        assert_files_equal(temporary_dimr_config_file, temporary_save_location)

    @pytest.mark.parametrize(
        "input_process, expected_process, expected_process_format",
        [
            pytest.param("0:1", 2, "0 1"),
            pytest.param("0:2", 3, "0 1 2"),
            pytest.param("0:3", 4, "0 1 2 3"),
            pytest.param("0:4", 5, "0 1 2 3 4"),
            pytest.param("2:4", 3, "0 1 2"),
            pytest.param("9:12", 4, "0 1 2 3"),
        ],
    )
    def test_dimr_with_fmcomponent_given_semicolon_style_for_setting_process(
        self, tmp_path, input_process, expected_process, expected_process_format
    ):
        dimr_config_data = self.get_fm_dimr_config_data(input_process)

        (
            temporary_dimr_config_file,
            temporary_save_location,
        ) = self.setup_temporary_files(tmp_path, dimr_config_data)

        dimr_config = DIMR(filepath=temporary_dimr_config_file)
        dimr_config.save(filepath=temporary_save_location)

        assert dimr_config.component[0].process == expected_process

        line_to_check = f"<process>{expected_process_format}</process>"

        with open(temporary_save_location, "r") as file:
            assert any(
                line.strip() == line_to_check for line in file
            ), f"File {temporary_save_location} does not contain the line: {line_to_check}"

    @pytest.mark.parametrize(
        "input_process",
        [
            pytest.param("0 1"),
            pytest.param("0 1 2"),
            pytest.param("0 1 2 3"),
            pytest.param("0 1 2 3 4"),
        ],
    )
    def test_dimr_with_fmcomponent_given_correct_style_for_setting_process(
        self, tmp_path, input_process
    ):
        dimr_config_data = self.get_fm_dimr_config_data(input_process)
        (
            temporary_dimr_config_file,
            temporary_save_location,
        ) = self.setup_temporary_files(tmp_path, dimr_config_data)

        dimr_config = DIMR(filepath=temporary_dimr_config_file)
        dimr_config.save(filepath=temporary_save_location)

        assert_files_equal(temporary_dimr_config_file, temporary_save_location)

    def test_dimr_with_fmcomponent_given_correct_style_for_setting_process_for_zero(
        self, tmp_path
    ):
        dimr_config_data = self.get_fm_dimr_config_data("0")

        (
            temporary_dimr_config_file,
            temporary_save_location,
        ) = self.setup_temporary_files(tmp_path, dimr_config_data)

        dimr_config_data_expected = self.get_fm_dimr_config_data_without_process()
        temporary_expected_dimr_config_file = tmp_path / "dimr_expected_config.xml"
        temporary_expected_dimr_config_file.write_text(dimr_config_data_expected)

        dimr_config = DIMR(filepath=temporary_dimr_config_file)
        dimr_config.save(filepath=temporary_save_location)

        assert_files_equal(temporary_expected_dimr_config_file, temporary_save_location)

    @pytest.mark.parametrize(
        "input_process, expected_process",
        [
            pytest.param("0", 1),
            pytest.param("0 1", 2),
            pytest.param("0 1 2", 3),
            pytest.param("0 1 2 3", 4),
            pytest.param("0 1 2 3 4", 5),
            pytest.param("0:1", 2),
            pytest.param("0:2", 3),
            pytest.param("0:3", 4),
            pytest.param("0:4", 5),
            pytest.param("2:4", 3),
        ],
    )
    def test_dimr_with_fmcomponent_process_component_set_correctly(
        self, tmp_path, input_process, expected_process
    ):
        dimr_config_data = self.get_fm_dimr_config_data(input_process)
        (
            temporary_dimr_config_file,
            temporary_save_location,
        ) = self.setup_temporary_files(tmp_path, dimr_config_data)

        dimr_config = DIMR(filepath=temporary_dimr_config_file)
        dimr_config.save(filepath=temporary_save_location)

        assert dimr_config.component[0].process == expected_process

    def test_dimr_with_fmcomponent_given_old_invalid_style_for_setting_process_raises_value_error(
        self, tmp_path
    ):
        process_number_single_int: int = 4
        dimr_config_data = self.get_fm_dimr_config_data(process_number_single_int)
        temporary_dimr_config_file, _ = self.setup_temporary_files(
            tmp_path, dimr_config_data
        )

        with pytest.raises(ValueError) as error:
            DIMR(filepath=temporary_dimr_config_file)

        expected_message = f"In component 'test', the keyword process '{process_number_single_int}', is incorrect."
        errormessage = str(error.value)
        assert expected_message in errormessage

    @pytest.mark.parametrize(
        "input_process",
        [
            pytest.param("This is incorrect"),
            pytest.param(1.4234),
            pytest.param("1234556"),
        ],
    )
    def test_dimr_with_fmcomponent_given_invalid_style_for_setting_process_raises_value_error(
        self, tmp_path, input_process
    ):
        dimr_config_data = self.get_fm_dimr_config_data(input_process)
        temporary_dimr_config_file, _ = self.setup_temporary_files(
            tmp_path, dimr_config_data
        )

        with pytest.raises(ValueError) as error:
            DIMR(filepath=temporary_dimr_config_file)

        expected_message = (
            f"In component 'test', the keyword process '{input_process}', is incorrect."
        )
        errormessage = str(error.value)
        assert expected_message in errormessage

    @pytest.mark.parametrize(
        "input_process, expected_process_format",
        [
            pytest.param(2, "0 1"),
            pytest.param(3, "0 1 2"),
            pytest.param(4, "0 1 2 3"),
            pytest.param(5, "0 1 2 3 4"),
        ],
    )
    def test_dimr_with_fmcomponent_saving_process(
        self, tmp_path, input_process: int, expected_process_format: str
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

    @pytest.mark.parametrize(
        "input_process, expected_process_format",
        [
            pytest.param(2, "0 1"),
            pytest.param(3, "0 1 2"),
            pytest.param(4, "0 1 2 3"),
            pytest.param(5, "0 1 2 3 4"),
        ],
    )
    def test_dimr_with_multiple_fmcomponent_saving_process(
        self, tmp_path, input_process: int, expected_process_format: str
    ):
        component = FMComponent(
            name="test",
            workingDir=".",
            inputfile="test.mdu",
            process=6,
            mpiCommunicator="DFM_COMM_DFMWORLD",
        )
        line_to_check_first_component = "<process>0 1 2 3 4 5</process>"

        component2 = FMComponent(
            name="test2",
            workingDir=".",
            inputfile="test.mdu",
            process=input_process,
            mpiCommunicator="DFM_COMM_DFMWORLD",
        )

        dimr = DIMR(component=[component, component2])
        save_location: Path = tmp_path / "dimr_config.xml"
        dimr.save(filepath=save_location)

        line_to_check = f"<process>{expected_process_format}</process>"

        with open(save_location, "r") as file:
            assert any(
                line.strip() == line_to_check_first_component for line in file
            ), f"File {save_location} does not contain the line: {line_to_check_first_component}"
            assert any(
                line.strip() == line_to_check for line in file
            ), f"File {save_location} does not contain the line: {line_to_check}"

    @pytest.mark.parametrize(
        "input_process",
        [
            pytest.param(None),
            pytest.param(1),
        ],
    )
    def test_dimr_with_fmcomponent_saving_process_when_process_should_be_left_out(
        self, tmp_path, input_process
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

        process = "<process>"

        with open(save_location, "r") as file:
            assert (
                process not in file
            ), f"File {save_location} does contain the line: {process}"
