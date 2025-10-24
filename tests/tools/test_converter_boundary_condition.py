from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock, patch

import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.ext.models import Boundary
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.tools.extforce_convert.converters import BoundaryConditionConverter
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser
from tests.utils import compare_two_files, ignore_version_lines, is_linux, is_macos


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
def cmp_files(tmpdir: Path) -> List[Path]:
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
    forcing_model = new_quantity_block.forcingfile[0]
    assert forcing_model.filepath.name == forcing_model_filename
    names = ["L1_0001", "L1_0002"]
    assert all(f.name == name for f, name in zip(forcing_model.forcing, names))
    assert new_quantity_block.locationfile == DiskOnlyFileModel(str(forcing.filename))
    assert new_quantity_block.bndwidth1d is None
    assert new_quantity_block.bndbldepth is None
    assert new_quantity_block.nodeid is None

    assert forcing_model.filepath.name == "tfl_01.bc"


@pytest.mark.e2e
def test_merge_tim_files(converter: BoundaryConditionConverter, tim_files: List[Path]):
    """
    Tests that merging multiple tim files using the converter results in a single TimModel
    with the correct quantity names, index, and values.

    Args:
        converter (BoundaryConditionConverter):
            The converter instance.
        tim_files (List[Path]):
            List of tim file paths to merge.
    """
    tim_model = converter.merge_tim_files(tim_files, "waterlevelbnd")
    assert tim_model.quantities_names == ["tfl_01_0001", "tfl_01_0002"]
    df = tim_model.as_dataframe()
    assert df.index.tolist() == [0, 120]
    assert df.columns.tolist() == ["tfl_01_0001", "tfl_01_0002"]
    assert df.values.tolist() == [[0.01, 0.01], [0.01, 0.01]]


class TestBoundaryConverter:
    tim_data = [[[0, 0.01], [120, 0.01]], [[0, 0.01], [120, 0.01]]]
    t3d_data = [
        [
            [0.0, 40.0, 35.0, 34.5, 32.5, 30.0],
            [180.0, 80.0, 35.0, 34.5, 32.5, 30.0],
            [9999999.0, 40.0, 35.0, 34.5, 32.5, 30.0],
        ],
        [
            [0.0, 41.0, 36.45455, 36.0, 34.0, 31.0],
            [180.0, 41.00002, 36.45456, 36.00002, 34.00002, 31.00002],
            [9999999.0, 42.0, 37.45455, 37.0, 35.0, 32.0],
        ],
    ]
    cmp_data = [[[0.0, 1.0, 2.0]], [["4MS10", 2.0, 1.0]]]
    boundary_parameters = [
        pytest.param(["tim_files", [], []], tim_data, id="tim_files_case"),
        pytest.param([[], "t3d_files", []], t3d_data, id="t3d_files_case"),
        pytest.param([[], [], "cmp_files"], cmp_data, id="cmp_files_case"),
        pytest.param(
            ["tim_files", "t3d_files", []],
            tim_data + t3d_data,
            id="tim_and_t3d_files_case",
        ),
        pytest.param(
            ["tim_files", [], "cmp_files"],
            tim_data + cmp_data,
            id="tim_and_cmp_files_case",
        ),
        pytest.param(
            [[], "t3d_files", "cmp_files"],
            t3d_data + cmp_data,
            id="t3d_and_cmp_files_case",
        ),
        pytest.param(
            ["tim_files", "t3d_files", "cmp_files"],
            tim_data + t3d_data + cmp_data,
            id="all_files_case",
        ),
    ]

    @pytest.mark.parametrize("files, contents", boundary_parameters)
    def test_boundary_converter(
        self,
        request,
        files: List[str],
        contents,
        converter: BoundaryConditionConverter,
        forcing: ExtOldForcing,
        start_date: str,
    ):
        """
        Tests the conversion of boundary conditions for all combinations of tim, t3d, and cmp files.
        Verifies that the resulting boundary block and its forcing model have the expected structure and data.

        Args:
            request:
                Pytest request fixture for dynamic fixture access.
            files (List[str]):
                List of fixture names for file types.
            contents:
                Expected datablock contents for each forcing.
            converter (BoundaryConditionConverter):
                The converter instance.
            forcing (ExtOldForcing):
                The old forcing block.
            start_date (str):
                The reference start date.
        """
        resolved_files = [
            (
                request.getfixturevalue(fixture_name)
                if isinstance(fixture_name, str)
                else fixture_name
            )
            for fixture_name in files
        ]

        with patch.object(Path, "glob", side_effect=resolved_files):
            new_quantity_block = converter.convert(forcing, start_date)

        verify_boundary_conditions(
            new_quantity_block, "waterlevelbnd", "tfl_01.bc", forcing
        )

        forcing_model = new_quantity_block.forcingfile[0]
        for forcing, content in zip(forcing_model.forcing, contents):
            assert forcing.datablock == content

    def test_with_tim(
        self,
        converter: BoundaryConditionConverter,
        input_files_dir: Path,
        forcing: ExtOldForcing,
        tim_files: List[Path],
        start_date: str,
    ):
        """
        Tests conversion of a boundary condition when only tim files are present.
        Verifies correct legacy file tracking, quantityunitpair, and datablock content.

        Args:
            converter (BoundaryConditionConverter): The converter instance.
            input_files_dir (Path): Directory containing input files.
            forcing (ExtOldForcing): The old forcing block.
            tim_files (List[Path]): List of tim file paths.
            start_date (str): The reference start date.
        """
        t3d_files = []
        cmp_files = []
        with patch.object(Path, "glob", side_effect=[tim_files, t3d_files, cmp_files]):
            new_quantity_block = converter.convert(forcing, start_date)

        verify_boundary_conditions(
            new_quantity_block, "waterlevelbnd", "tfl_01.bc", forcing
        )
        assert converter.legacy_files == tim_files
        forcing_model = new_quantity_block.forcingfile[0]
        assert forcing_model.forcing[0].quantityunitpair[0].quantity == "time"
        assert all(
            [
                forcing_model.forcing[i].quantityunitpair[1].quantity == "waterlevelbnd"
                for i in range(2)
            ]
        )
        assert forcing_model.forcing[0].datablock == [[0, 0.01], [120, 0.01]]

    def test_with_cmp(
        self,
        converter: BoundaryConditionConverter,
        forcing: ExtOldForcing,
        cmp_files: List[Path],
        start_date: str,
    ):
        """
        Tests conversion of a boundary condition when only cmp files are present.
        Verifies correct legacy file tracking, quantityunitpair, and datablock content for cmp.

        Args:
            converter (BoundaryConditionConverter):
                The converter instance.
            forcing (ExtOldForcing):
                The old forcing block.
            cmp_files (List[Path]):
                List of cmp file paths.
            start_date (str):
                The reference start date.
        """
        t3d_files = []
        tim_files = []
        with patch.object(Path, "glob", side_effect=[tim_files, t3d_files, cmp_files]):
            new_quantity_block = converter.convert(forcing, start_date)

        verify_boundary_conditions(
            new_quantity_block, "waterlevelbnd", "tfl_01.bc", forcing
        )
        assert converter.legacy_files == cmp_files
        forcing_model = new_quantity_block.forcingfile[0]
        assert all(
            [
                forcing_model.forcing[i].quantityunitpair[1].quantity
                == "waterlevelbnd amplitude"
                for i in range(2)
            ]
        )
        assert all(
            [
                forcing_model.forcing[i].quantityunitpair[2].quantity
                == "waterlevelbnd phase"
                for i in range(2)
            ]
        )
        assert forcing_model.forcing[0].datablock == [[0.0, 1.0, 2.0]]

    def test_with_t3d(
        self,
        converter: BoundaryConditionConverter,
        input_files_dir: Path,
        forcing: ExtOldForcing,
        t3d_files: List[Path],
        start_date: str,
    ):
        """
        Tests conversion of a boundary condition when only t3d files are present.
        Verifies correct legacy file tracking, quantityunitpair, and datablock content for t3d.

        Args:
            converter (BoundaryConditionConverter):
                The converter instance.
            input_files_dir (Path):
                Directory containing input files.
            forcing (ExtOldForcing):
                The old forcing block.
            t3d_files (List[Path]):
                List of t3d file paths.
            start_date (str):
                The reference start date.
        """
        tim_files = []
        cmp_files = []
        with patch.object(Path, "glob", side_effect=[tim_files, t3d_files, cmp_files]):
            new_quantity_block = converter.convert(forcing, start_date)

        verify_boundary_conditions(
            new_quantity_block, "waterlevelbnd", "tfl_01.bc", forcing
        )
        assert converter.legacy_files == t3d_files
        forcing_model = new_quantity_block.forcingfile[0]

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
        Tests the update method of ExternalForcingConverter for a file containing only boundary conditions.
        Verifies that all quantities are converted to boundary conditions and saved correctly.

        Args:
            old_forcing_file_boundary (Dict[str, str]):
                Dictionary with test file paths and expected data.
            start_date (str):
                The reference start date.
        """
        mock_mdu_parser = MagicMock(spec=MDUParser)
        mock_mdu_parser.temperature_salinity_data = {"refdate": start_date}
        mock_mdu_parser.mdu_path = old_forcing_file_boundary["path"].parent / "mdu.mdu"
        converter = ExternalForcingConverter(
            old_forcing_file_boundary["path"], mdu_parser=mock_mdu_parser
        )

        with patch(
            "hydrolib.tools.extforce_convert.main_converter.ExternalForcingConverter._update_mdu_file"
        ):
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

        if not is_macos() and not is_linux():
            # test save files
            ext_model.save(recurse=True, exclude_unset=True)

            reference_files = [
                "new-external-forcing-reference.ext",
                "tfl_01-reference.bc",
            ]
            files = ["new-external-forcing.ext", "tfl_01.bc"]
            for i in range(2):
                assert (r_dir / files[i]).exists()
                diff = compare_two_files(
                    r_dir / reference_files[i],
                    r_dir / files[i],
                    ignore_line=ignore_version_lines,
                )
                assert diff == []
                (r_dir / files[i]).unlink()
