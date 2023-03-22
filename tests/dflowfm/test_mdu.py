import inspect
from pathlib import Path
from typing import Callable, Dict, Union

import pytest

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.ini.parser import Parser, ParserConfig
from hydrolib.core.dflowfm.mdu.models import (
    FMModel,
    Geometry,
    InfiltrationMethod,
    Output,
    ParticlesThreeDType,
    ProcessFluxIntegration,
    VegetationModelNr,
)
from hydrolib.core.dflowfm.obscrosssection.models import (
    ObservationCrossSection,
    ObservationCrossSectionModel,
)
from hydrolib.core.dflowfm.polyfile.models import (
    Description,
    Metadata,
    Point,
    PolyFile,
    PolyObject,
)

from ..utils import WrapperTest, assert_objects_equal, test_input_dir


class TestModels:
    """Test class to test all classes and methods contained in the
    hydrolib.core.dflowfm.mdu.models.py module"""

    def test_mdu_file_with_network_is_read_correctly(self):
        input_mdu = (
            test_input_dir
            / "e02"
            / "c11_korte-woerden-1d"
            / "dimr_model"
            / "dflowfm"
            / "FlowFM.mdu"
        )
        fm_model = FMModel(input_mdu)
        assert fm_model.geometry.netfile is not None

        mesh = fm_model.geometry.netfile._mesh1d
        assert len(mesh.branches) > 0

    def test_mdu_with_optional_sections(self):
        input_mdu = (
            test_input_dir / "dflowfm_individual_files" / "with_optional_sections.mdu"
        )

        fm_model = FMModel(input_mdu)
        assert fm_model.calibration is not None
        assert fm_model.calibration.usecalibration is False
        assert fm_model.calibration.definitionfile.filepath is None
        assert fm_model.calibration.areafile.filepath is None

        assert fm_model.grw is not None
        assert fm_model.grw.groundwater is False
        assert fm_model.grw.infiltrationmodel == InfiltrationMethod.NoInfiltration
        assert fm_model.grw.hinterceptionlayer == 0.0
        assert fm_model.grw.unifinfiltrationcapacity == 0.0
        assert fm_model.grw.conductivity == 0.0
        assert fm_model.grw.h_aquiferuni == 20.0
        assert fm_model.grw.h_unsatini == 0.200000002980232

        assert fm_model.processes is not None
        assert fm_model.processes.substancefile.filepath is None
        assert fm_model.processes.additionalhistoryoutputfile.filepath is None
        assert fm_model.processes.statisticsfile.filepath is None
        assert fm_model.processes.thetavertical == 0.0
        assert fm_model.processes.dtprocesses == 0.0
        assert fm_model.processes.dtmassbalance == 0.0
        assert fm_model.processes.processfluxintegration == ProcessFluxIntegration.WAQ
        assert fm_model.processes.wriwaqbot3doutput is False
        assert fm_model.processes.volumedrythreshold == 1e-3
        assert fm_model.processes.depthdrythreshold == 1e-3

        assert fm_model.particles is not None
        assert fm_model.particles.particlesfile is None
        assert fm_model.particles.particlesreleasefile.filepath is None
        assert fm_model.particles.addtracer is False
        assert fm_model.particles.starttime == 0.0
        assert fm_model.particles.timestep == 0.0
        assert fm_model.particles.threedtype == ParticlesThreeDType.DepthAveraged

        assert fm_model.veg is not None
        assert fm_model.veg.vegetationmodelnr == VegetationModelNr.No
        assert fm_model.veg.clveg == 0.8
        assert fm_model.veg.cdveg == 0.7
        assert fm_model.veg.cbveg == 0.0
        assert fm_model.veg.rhoveg == 0.0
        assert fm_model.veg.stemheightstd == 0.0

    def test_disk_only_file_model_list_fields_are_initialized_correctly(self):
        data = {"landboundaryfile": [Path("test.ldb")]}

        model = Geometry(**data)

        assert model.landboundaryfile is not None
        assert len(model.landboundaryfile) == 1
        assert isinstance(model.landboundaryfile[0], DiskOnlyFileModel)


class PyTestMatchAny:
    def __eq__(self, other):
        return True


class TestOutput:
    """Test class to test the [output] section in an MDU file."""

    def test_obs_crs_from_mdu(self):
        fmmodel = FMModel(
            filepath=test_input_dir
            / "e02"
            / "f101_1D-boundaries"
            / "c01_steady-state-flow"
            / "Boundary.mdu"
        )

        assert isinstance(fmmodel.output.crsfile[0], ObservationCrossSectionModel)

        # Check recursive construction of ObservationCrossSectionModel object
        assert len(fmmodel.output.crsfile[0].observationcrosssection) == 4
        assert (
            fmmodel.output.crsfile[0].observationcrosssection[0].name
            == "ObservCross_Chg_T1"
        )
        assert (
            len(fmmodel.output.crsfile[0].observationcrosssection[3].xcoordinates) == 2
        )

    def _get_expected_polyobjects(self):
        """Get PolyObject list that corresponds with example test file.

        Use this for testing correct reading of PolyFile
        `tests/data/input/obscrsfile_cases/test_crs.pli`.

        Returns:
            [PolyObject]: the objects contained in the fully loaded polyfile."""

        objects = [
            PolyObject(
                description=Description(content="\n description\n more description\n"),
                metadata=Metadata(name="name1", n_rows=2, n_columns=2),
                points=[Point(x=1, y=2, data=[]), Point(x=3, y=4, data=[])],
            ),
            PolyObject(
                description=Description(
                    content=r" oneline description (and last polyline will have NO comment)"
                ),
                metadata=Metadata(name="name2", n_rows=2, n_columns=2),
                points=[Point(x=11, y=2, data=[]), Point(x=13, y=4, data=[])],
            ),
            PolyObject(
                description=None,
                metadata=Metadata(name="name3", n_rows=2, n_columns=2),
                points=[Point(x=21, y=2, data=[]), Point(x=23, y=4, data=[])],
            ),
        ]

        return objects

    def _get_expected_observationcrosssections(self):
        """Get ObservationCrossSection list that corresponds with example test file.

        Use this for testing correct reading of PolyFile
        `tests/data/input/obscrsfile_cases/ObservationPoints_crs.ini`.

        Returns:
            [ObservationCrossSection]: the objects contained in the fully loaded obs_crs.ini file."""

        objects = [
            ObservationCrossSection(
                name="ObservCross_Chg_T1",
                branchid="T1",
                chainage=1000,
            ),
            ObservationCrossSection(
                name="ObservCross_xy_T2",
                numcoordinates=2,
                xcoordinates=[1000.0, 1000.0],
                ycoordinates=[300.0, 200.0],
            ),
            ObservationCrossSection(
                name="ObservCross_Chg_T3", branchid="T3", chainage=1000
            ),
            ObservationCrossSection(
                name="ObservCross_xy_T4",
                numcoordinates=2,
                xcoordinates=[1000.0, 1000.0],
                ycoordinates=[800.0, 700.0],
            ),
        ]

        return objects

    def _check_correct_polyobjects(self, loaded_polyfile: PolyFile):
        expected_polyobjects = self._get_expected_polyobjects()

        assert isinstance(loaded_polyfile, PolyFile)

        # Check recursive construction of PolyFile object
        assert loaded_polyfile.objects == expected_polyobjects

    def _check_correct_obscrsobjects(
        self, loaded_obscrsmodel: ObservationCrossSectionModel
    ):
        expected_obscrsobjects = self._get_expected_observationcrosssections()

        assert isinstance(loaded_obscrsmodel, ObservationCrossSectionModel)

        assert_objects_equal(
            loaded_obscrsmodel.observationcrosssection,
            expected_obscrsobjects,
            ["comments"],
        )

    def test_loading_fmmodel_model_with_single_ini_crsfile(self):
        file_path = (
            test_input_dir
            / "obscrsfile_cases"
            / "single_ini"
            / "emptymodel_with_obscrs.mdu"
        )
        model = FMModel(file_path)

        assert len(model.output.crsfile) == 1

        self._check_correct_obscrsobjects(model.output.crsfile[0])

    def test_loading_fmmodel_model_with_single_pli_crsfiles(self):
        file_path = (
            test_input_dir
            / "obscrsfile_cases"
            / "single_pli"
            / "emptymodel_with_obscrs.mdu"
        )
        model = FMModel(file_path)

        assert len(model.output.crsfile) == 1

        self._check_correct_polyobjects(model.output.crsfile[0])

    def test_loading_fmmodel_model_with_both_ini_and_pli_crsfiles(self):
        file_path = (
            test_input_dir
            / "obscrsfile_cases"
            / "both_ini_and_pli"
            / "emptymodel_with_obscrs.mdu"
        )
        model = FMModel(file_path)

        assert len(model.output.crsfile) == 2

        self._check_correct_polyobjects(model.output.crsfile[0])

        self._check_correct_obscrsobjects(model.output.crsfile[1])
