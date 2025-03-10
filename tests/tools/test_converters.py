from pathlib import Path
from typing import List

import numpy as np
import pytest

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.ext.models import (
    Boundary,
    Meteo,
    MeteoForcingFileType,
    MeteoInterpolationMethod,
)
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.core.dflowfm.inifield.models import InitialField, ParameterField
from hydrolib.tools.extforce_convert.converters import (
    BoundaryConditionConverter,
    InitialConditionConverter,
    MeteoConverter,
    ParametersConverter,
    save_mdu_file,
    update_extforce_file_new,
)


class TestConvertInitialCondition:
    def test_sample_data_file(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.InitialWaterLevel,
            filename="iniwaterlevel.xyz",
            filetype=7,  # "Polyline"
            method="5",  # "Interpolate space",
            operand="O",
        )

        new_quantity_block = InitialConditionConverter().convert(forcing)
        assert isinstance(new_quantity_block, InitialField)
        assert new_quantity_block.datafiletype == "sample"
        assert new_quantity_block.interpolationmethod == "triangulation"

    def test_polygon_data_file(self, polylines_dir: Path):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.InitialWaterLevel,
            filename=polylines_dir / "boundary-polyline-no-z-no-label.pli",
            value=0.0,
            filetype=10,
            method="4",
            operand="O",
        )
        new_quantity_block = InitialConditionConverter().convert(forcing)
        assert new_quantity_block.datafiletype == "polygon"
        assert new_quantity_block.interpolationmethod == "constant"
        assert np.isclose(new_quantity_block.value, 0.0)


class TestConvertParameters:
    def test_sample_data_file(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.FrictionCoefficient,
            filename="iniwaterlevel.xyz",
            filetype=7,  # "Polyline"
            method="5",  # "Interpolate space",
            operand="O",
        )

        new_quantity_block = ParametersConverter().convert(forcing)
        assert isinstance(new_quantity_block, ParameterField)
        assert new_quantity_block.datafiletype == "sample"
        assert new_quantity_block.interpolationmethod == "triangulation"


class TestConvertMeteo:
    def test_default(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WindX,
            filename="windtest.amu",
            filetype=4,
            method="2",
            operand="O",
        )

        new_quantity_block = MeteoConverter().convert(forcing)
        assert isinstance(new_quantity_block, Meteo)
        assert new_quantity_block.quantity == "windx"
        assert new_quantity_block.operand == Operand.override
        assert new_quantity_block.forcingfile == DiskOnlyFileModel("windtest.amu")
        assert new_quantity_block.forcingfiletype == MeteoForcingFileType.arcinfo
        assert (
            new_quantity_block.interpolationmethod
            == MeteoInterpolationMethod.linearSpaceTime
        )


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

    def test_merge_cmp_files(self, input_files_dir: Path, cmp_files: List[Path]):
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
        cmp_model = BoundaryConditionConverter.merge_cmp_files(cmp_files, forcing)
        assert cmp_model.components[0].quantity_name == "tfl_01_0001"
        assert cmp_model.components[1].quantity_name == "tfl_01_0002"
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


def test_update_mdu_on_the_fly(input_files_dir: Path):
    mdu_filename = (
        input_files_dir / "e02/f011_wind/c081_combi_uniform_curvi/windcase.mdu"
    )
    new_mdu_file = mdu_filename.with_stem(f"{mdu_filename.stem}-updated")
    updated_mdu_file = update_extforce_file_new(mdu_filename, "test.ext")
    assert updated_mdu_file[149] == "[external forcing]\n"
    assert (
        updated_mdu_file[150]
        == "ExtForceFileNew                      = test.ext                              # New format for external forcings file *.ext, link with bc     -format boundary conditions specification\n"
    )
    # test the save mdu file function
    save_mdu_file(updated_mdu_file, new_mdu_file)
    assert new_mdu_file.exists()
    try:
        new_mdu_file.unlink()
    except PermissionError:
        pass
