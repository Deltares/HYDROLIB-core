from pathlib import Path
from typing import List, Tuple

import numpy as np
import pytest

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.ext.models import (
    Meteo,
    MeteoForcingFileType,
    MeteoInterpolationMethod,
)
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.core.dflowfm.inifield.models import InitialField, ParameterField
from hydrolib.tools.extforce_convert.converters import (
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


@pytest.mark.parametrize(
    "input_file, on_line, expected_line, ext_file",
    [
        (
            "dflowfm_individual_files/with_optional_sections.mdu",
            (232, 233),
            "ExtForceFileNew                           = test.ext\n",
            "test.ext",
        ),
        (
            "e02/f011_wind/c081_combi_uniform_curvi/windcase.mdu",
            (149, 150),
            "ExtForceFileNew                      = test.ext                              # New format for external forcings file *.ext, link with bc     -format boundary conditions specification\n",
            "test.ext",
        ),
        (
            "e02/f011_wind/c081_combi_uniform_curvi/windcase.mdu",
            (149, 150),
            "ExtForceFileNew                      = really_long_external_forcing_file_results_name.ext # r external forcings file *.ext, link with bc     -format boundary conditions specification\n",
            "really_long_external_forcing_file_results_name.ext",
        ),
    ],
    ids=["without comment", "with comment", "overflow comment"],
)
def test_update_mdu_on_the_fly(
    input_files_dir: Path,
    input_file: str,
    on_line: Tuple[int, int],
    expected_line: str,
    ext_file: str,
):
    mdu_filename = input_files_dir / input_file
    new_mdu_file = mdu_filename.with_stem(f"{mdu_filename.stem}-updated")
    updated_mdu_file = update_extforce_file_new(mdu_filename, ext_file)
    assert updated_mdu_file[on_line[0]] == "[external forcing]\n"
    assert updated_mdu_file[on_line[1]] == expected_line
    # test the save mdu file function
    save_mdu_file(updated_mdu_file, new_mdu_file)
    assert new_mdu_file.exists()
    try:
        new_mdu_file.unlink()
    except PermissionError:
        pass
