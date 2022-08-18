from pathlib import Path
from typing import Callable, Dict, Union

import pytest

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.io.mdu.models import (
    FMModel,
    InfiltrationMethod,
    Output,
    ParticlesThreeDType,
    ProcessFluxIntegration,
    VegetationModelNr,
)

from ..utils import test_input_dir


class TestModels:
    """Test class to test all classes and methods contained in the
    hydrolib.core.io.mdu.models.py module"""

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
        data = {"crsfile": [Path("test.crs")]}

        model = Output(**data)

        assert model.crsfile is not None
        assert len(model.crsfile) == 1
        assert isinstance(model.crsfile[0], DiskOnlyFileModel)
