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
from hydrolib.core.dflowfm.obscrosssection.models import ObservationCrossSectionModel
from hydrolib.core.dflowfm.polyfile.models import PolyFile

from ..utils import WrapperTest, test_input_dir


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

    def test_mixed_obs_crs_files(self):
        """Test the construction of correct types of observation crosssection
        objects, when both old and new formatted input files are given."""

        input = inspect.cleandoc(
            f"""
            [output]
            CrsFile = {test_input_dir / 'dflowfm_individual_files/test.pli'} {test_input_dir / 'e02/f101_1D-boundaries/c01_steady-state-flow/ObservationPoints_crs.ini'}
            """
        )
        parser = Parser(ParserConfig())
        for l in input.splitlines():
            parser.feed_line(l)

        document = parser.finalize()
        wrapper = WrapperTest[Output].parse_obj({"val": document.sections[0]})
        output = wrapper.val

        assert len(output.crsfile) == 2

        assert isinstance(output.crsfile[0], PolyFile)
        assert isinstance(output.crsfile[1], ObservationCrossSectionModel)

        # Check recursive construction of PolyFile object
        assert len(output.crsfile[0].objects) == 3
        assert output.crsfile[0].objects[0].metadata.name == "name1"
        assert len(output.crsfile[0].objects[2].points) == 2

        # Check recursive construction of ObservationCrossSectionModel object
        assert len(output.crsfile[1].observationcrosssection) == 4
        assert output.crsfile[1].observationcrosssection[0].name == "ObservCross_Chg_T1"
        assert len(output.crsfile[1].observationcrosssection[3].xcoordinates) == 2
