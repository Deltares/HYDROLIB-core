from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock, patch

import pytest

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.ext.models import Boundary
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.tools.extforce_convert.converters import BoundaryConditionConverter
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from tests.utils import compare_two_files, is_macos


@pytest.fixture
def converter(input_files_dir: Path) -> BoundaryConditionConverter:
    converter = BoundaryConditionConverter()
    converter.root_dir = input_files_dir / "boundary-conditions"
    return converter


@pytest.fixture
def start_date() -> str:
    return "minutes since 2015-01-01 00:00:00"


@pytest.fixture
def tim_files(input_files_dir: Path) -> List[Path]:
    return [
        input_files_dir / "boundary-conditions/tfl_01_0001.tim",
        input_files_dir / "boundary-conditions/tfl_01_0002.tim",
    ]


@pytest.fixture
def t3d_files(input_files_dir: Path) -> List[Path]:
    return [
        input_files_dir / "boundary-conditions/tfl_01_0001.t3d",
        input_files_dir / "boundary-conditions/tfl_01_0002.t3d",
    ]


@pytest.fixture
def cmp_files(self, tmpdir: Path) -> List[Path]:
    path_list = [
        Path(tmpdir / "tfl_01_0001.cmp"),
        Path(tmpdir / "tfl_01_0002.cmp"),
    ]
    with open(path_list[0], "w") as file:
        file.write("#test content\n0.0  1.0  2.0\n")
    with open(path_list[1], "w") as file:
        file.write("#test content\n4MS10  2.0  1.0\n")
    return path_list


@pytest.fixture
def forcing(input_files_dir: Path) -> ExtOldForcing:
    return ExtOldForcing(
        quantity=ExtOldQuantity.WaterLevelBnd,
        filename=input_files_dir / "boundary-conditions/tfl_01.pli",
        filetype=9,
        method="3",
        operand="O",
    )


def verify_boundary_conditions(
    new_quantity_block, expected_quantity, forcing_model_filename, forcing
):
    assert isinstance(new_quantity_block, Boundary)
    assert new_quantity_block.quantity == expected_quantity
    forcing_model = new_quantity_block.forcingfile
    assert forcing_model.filepath.name == forcing_model_filename
    assert len(forcing_model.forcing) == 2
    names = ["L1_0001", "L1_0002"]
    assert all(f.name == name for f, name in zip(forcing_model.forcing, names))
    assert all(f.quantityunitpair[0].quantity == "time" for f in forcing_model.forcing)
    assert new_quantity_block.locationfile == DiskOnlyFileModel(str(forcing.filename))
    assert new_quantity_block.bndwidth1d is None
    assert new_quantity_block.bndbldepth is None
    assert new_quantity_block.nodeid is None

    assert forcing_model.filepath.name == "tfl_01.bc"


def test_merge_tim_files(converter: BoundaryConditionConverter, tim_files: List[Path]):
    """
    Test merging multiple tim files into a single tim model.
    """
    tim_model = converter.merge_tim_files(tim_files, "waterlevelbnd")
    assert tim_model.quantities_names == ["tfl_01_0001", "tfl_01_0002"]
    df = tim_model.as_dataframe()
    assert df.index.tolist() == [0, 120]
    assert df.columns.tolist() == ["tfl_01_0001", "tfl_01_0002"]
    assert df.values.tolist() == [[0.01, 0.01], [0.01, 0.01]]


def test_merge_cmp_files(
    converter: BoundaryConditionConverter, input_files_dir: Path, cmp_files: List[Path]
):
    """
    Test merging multiple cmp files into a single cmp model.
    """
    file_name = input_files_dir / "boundary-conditions/tfl_01.pli"
    forcing = ExtOldForcing(
        quantity=ExtOldQuantity.WaterLevelBnd,
        filename=file_name,
        filetype=9,
        method="3",
        operand="O",
    )
    cmp_model = converter.merge_cmp_files(cmp_files, forcing)
    assert cmp_model.quantities_names[0] == "tfl_01_0001"
    assert cmp_model.quantities_names[1] == "tfl_01_0002"
    assert cmp_model.components[0].harmonics[0] == {
        "period": 0.0,
        "amplitude": 1.0,
        "phase": 2.0,
    }
    assert cmp_model.components[1].astronomics[0] == {
        "name": "4MS10",
        "amplitude": 2.0,
        "phase": 1.0,
    }


class TestBoundaryConverter:

    def test_with_tim(
        self,
        converter: BoundaryConditionConverter,
        input_files_dir: Path,
        forcing: ExtOldForcing,
        tim_files: List[Path],
        start_date: str,
    ):
        """
        Test converting a boundary condition with a tim file.
        """
        t3d_files = []
        with patch.object(Path, "glob", side_effect=[tim_files, t3d_files]):
            new_quantity_block = converter.convert(forcing, start_date)

        verify_boundary_conditions(
            new_quantity_block, "waterlevelbnd", "tfl_01.bc", forcing
        )

        forcing_model = new_quantity_block.forcingfile
        assert all(
            [
                forcing_model.forcing[i].quantityunitpair[1].quantity == "waterlevelbnd"
                for i in range(2)
            ]
        )
        assert forcing_model.forcing[0].datablock == [[0, 0.01], [120, 0.01]]

    def test_with_t3d(
        self,
        converter: BoundaryConditionConverter,
        input_files_dir: Path,
        forcing: ExtOldForcing,
        t3d_files: List[Path],
        start_date: str,
    ):
        """
        Test convert a boundary condition with a t3d file.
        """
        tim_files = []
        with patch.object(Path, "glob", side_effect=[tim_files, t3d_files]):
            new_quantity_block = converter.convert(forcing, start_date)

        verify_boundary_conditions(
            new_quantity_block, "waterlevelbnd", "tfl_01.bc", forcing
        )

        forcing_model = new_quantity_block.forcingfile

        assert all(
            len(forcing_model.forcing[i].quantityunitpair) == 6 for i in range(2)
        )
        assert forcing_model.forcing[0].quantityunitpair[0].quantity == "time"
        assert (
            forcing_model.forcing[0].quantityunitpair[0].unit
            == "seconds since 2006-01-01 00:00:00 +00:00"
        )

        assert all(
            forcing_model.forcing[0].quantityunitpair[i].quantity == "waterlevelbnd"
            for i in range(1, 6)
        )
        assert all(
            forcing_model.forcing[0].quantityunitpair[i].unit == "m"
            for i in range(1, 6)
        )

        assert forcing_model.forcing[0].datablock == [
            [0.0, 40.0, 35.0, 34.5, 32.5, 30.0],
            [180.0, 80.0, 35.0, 34.5, 32.5, 30.0],
            [9999999.0, 40.0, 35.0, 34.5, 32.5, 30.0],
        ]
        assert forcing_model.forcing[1].datablock == [
            [0.0, 41.0, 36.45455, 36.0, 34.0, 31.0],
            [180.0, 41.00002, 36.45456, 36.00002, 34.00002, 31.00002],
            [9999999.0, 42.0, 37.45455, 37.0, 35.0, 32.0],
        ]


class TestMainConverter:

    def test_converter_update(
        self, old_forcing_file_boundary: Dict[str, str], start_date: str
    ):
        """
        The old external forcing file contains only 9 boundary condition quantities all with polyline location files
        and no forcing files. The update method should convert all the quantities to boundary conditions.
        """
        mdu_info = {"refdate": start_date}
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

        if not is_macos:
            # test save files
            ext_model.save(recurse=True)

            reference_files = [
                "new-external-forcing-reference.ext",
                "tfl_01-reference.bc",
            ]
            files = ["new-external-forcing.ext", "tfl_01.bc"]
            for i in range(2):
                assert (r_dir / files[i]).exists()
                diff = compare_two_files(r_dir / reference_files[i], r_dir / files[i])
                assert diff == []
                (r_dir / files[i]).unlink()
