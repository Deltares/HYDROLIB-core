from typing import Dict
from unittest.mock import Mock

from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from tests.utils import compare_two_files


def test_converter_update(old_forcing_file_boundary: Dict[str, str]):
    """
    The old external forcing file contains only 9 boundary condition quantities all with polyline location files
    and no forcing files. The update method should convert all the quantities to boundary conditions.
    """
    mdu_info = {
        "refdate": "minutes since 2015-01-01 00:00:00",
    }
    converter = ExternalForcingConverter(
        old_forcing_file_boundary["path"], mdu_info=mdu_info
    )

    # Mock the fm_model
    mock_fm_model = Mock()
    converter._fm_model = mock_fm_model
    ext_model, inifield_model, structure_model = converter.update()

    # all the quantities in the old external file are initial conditions
    # check that all the quantities (3) were converted to initial conditions
    num_quantities = len(old_forcing_file_boundary["quantities"])
    assert len(ext_model.boundary) == num_quantities
    # no parameters or any other structures, lateral or meteo data
    assert len(inifield_model.parameter) == 0
    assert len(ext_model.lateral) == 0
    assert len(ext_model.meteo) == 0
    assert len(structure_model.structure) == 0
    quantities = ext_model.boundary
    assert [
        str(quantities[i].locationfile.filepath) for i in range(num_quantities)
    ] == old_forcing_file_boundary["locationfile"]
    r_dir = converter.root_dir
    # test save files
    ext_model.save(recurse=True)

    reference_files = ["new-external-forcing-reference.ext", "tfl_01-reference.bc"]
    files = ["new-external-forcing.ext", "tfl_01.bc"]
    for i in range(2):
        assert (r_dir / files[i]).exists()
        diff = compare_two_files(r_dir / reference_files[i], r_dir / files[i])
        assert diff == []
        (r_dir / files[i]).unlink()
