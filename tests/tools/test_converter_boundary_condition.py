from pathlib import Path
from typing import Dict
from unittest.mock import Mock

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.ext.models import Boundary
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.tools.extforce_convert.converters import BoundaryConditionConverter
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from tests.utils import compare_two_files


class TestBoundaryConverter:

    def test_merge_tim_files(self, input_files_dir: Path):
        """
        Test merging multiple tim files into a single tim model.
        """
        file_name = input_files_dir / "boundary-conditions/tfl_01.pli"
        path_list = [
            input_files_dir / "boundary-conditions/tfl_01_0001.tim",
            input_files_dir / "boundary-conditions/tfl_01_0002.tim",
        ]
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename=file_name,
            filetype=9,
            method="3",
            operand="O",
        )
        tim_model = BoundaryConditionConverter.merge_tim_files(path_list, forcing)
        assert tim_model.quantities_names == ["tfl_01_0001", "tfl_01_0002"]
        df = tim_model.as_dataframe()
        assert df.index.tolist() == [0, 120]
        assert df.columns.tolist() == ["tfl_01_0001", "tfl_01_0002"]
        assert df.values.tolist() == [[0.01, 0.01], [0.01, 0.01]]

    def test_with_pli(self, input_files_dir):
        """
        Old quantity block:

        ```
        QUANTITY =waterlevelbnd
        FILENAME =tfl_01.pli
        FILETYPE =9
        METHOD   =3
        OPERAND  =O
        ```
        """
        file_name = input_files_dir / "boundary-conditions/tfl_01.pli"
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename=file_name,
            filetype=9,  # "Polyline"
            method="3",  # "Interpolate space",
            operand="O",
        )

        converter = BoundaryConditionConverter()
        converter.root_dir = input_files_dir / "boundary-conditions"
        start_date = "minutes since 2015-01-01 00:00:00"
        new_quantity_block = converter.convert(forcing, start_date)
        assert isinstance(new_quantity_block, Boundary)
        assert new_quantity_block.quantity == "waterlevelbnd"
        forcing_model = new_quantity_block.forcingfile
        assert new_quantity_block.locationfile == DiskOnlyFileModel(file_name)
        assert new_quantity_block.nodeid is None
        assert new_quantity_block.bndwidth1d is None
        assert new_quantity_block.bndbldepth is None
        assert len(forcing_model.forcing) == 2
        names = ["L1_0001", "L1_0002"]
        assert all(
            forcing.name == name for forcing, name in zip(forcing_model.forcing, names)
        )
        assert all(
            [
                forcing_model.forcing[i].quantityunitpair[0].quantity == "time"
                for i in range(2)
            ]
        )
        # check forcing model file path
        assert forcing_model.filepath.name == "tfl_01.bc"
        assert all(
            [
                forcing_model.forcing[i].quantityunitpair[1].quantity == "waterlevelbnd"
                for i in range(2)
            ]
        )
        assert forcing_model.forcing[0].datablock == [[0, 0.01], [120, 0.01]]


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
