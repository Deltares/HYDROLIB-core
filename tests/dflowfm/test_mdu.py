import shutil
from pathlib import Path
from typing import Callable, Dict, Union

import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.ext.models import Boundary
from hydrolib.core.dflowfm.friction.models import FrictGeneral
from hydrolib.core.dflowfm.mdu.models import (
    Calibration,
    FMModel,
    Geometry,
    InfiltrationMethod,
    Output,
    Particles,
    ParticlesThreeDType,
    Processes,
    ProcessFluxIntegration,
    Restart,
    Sediment,
    VegetationModelNr,
)
from hydrolib.core.dflowfm.net.models import Network
from hydrolib.core.dflowfm.obs.models import ObservationPoint, ObservationPointModel
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
from hydrolib.core.dflowfm.xyn.models import XYNModel, XYNPoint
from tests.utils import (
    assert_files_equal,
    assert_objects_equal,
    test_data_dir,
    test_input_dir,
    test_output_dir,
    test_reference_dir,
)


def _create_boundary(data: Dict) -> Boundary:
    data["quantity"] = ""
    data["forcingfile"] = ForcingModel()

    if data["locationfile"] is None:
        data["nodeid"] = "id"

    return Boundary(**data)


class TestModels:
    """Test class to test all classes and methods contained in the
    hydrolib.core.dflowfm.mdu.models.py module"""

    def test_symbols_are_correctly_written_and_loaded_from_file(self):
        path = test_output_dir / "test_symbols.mdu"

        model_a = FMModel()
        assert (
            model_a.physics.comments.initialtemperature == "Initial temperature [◦C]."
        )
        model_a.filepath = path
        model_a.save()

        model_b = FMModel(filepath=path)
        assert (
            model_b.physics.comments.initialtemperature == "Initial temperature [◦C]."
        )

    def test_default_fmmodel_saved_and_loaded_correctly(self):
        outputfile = test_output_dir / "default_fmmodel.mdu"

        fmmodel = FMModel()
        fmmodel.filepath = outputfile
        fmmodel.save()

        importfm = FMModel(filepath=fmmodel.filepath)

        # Two different instances of the `Network` will fail the equality check
        network = Network()
        fmmodel.geometry.netfile.network = network
        importfm.geometry.netfile.network = network

        assert importfm.model_dump() == fmmodel.model_dump()

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
        assert fm_model.grw.hinterceptionlayer == pytest.approx(0.0)
        assert fm_model.grw.unifinfiltrationcapacity == pytest.approx(0.0)
        assert fm_model.grw.conductivity == pytest.approx(0.0)
        assert fm_model.grw.h_aquiferuni == pytest.approx(20.0)
        assert fm_model.grw.h_unsatini == pytest.approx(0.200000002980232)

        assert fm_model.processes is not None
        assert fm_model.processes.substancefile.filepath is None
        assert fm_model.processes.additionalhistoryoutputfile.filepath is None
        assert fm_model.processes.statisticsfile.filepath is None
        assert fm_model.processes.thetavertical == pytest.approx(0.0)
        assert fm_model.processes.dtprocesses == pytest.approx(0.0)
        assert fm_model.processes.processfluxintegration == ProcessFluxIntegration.WAQ
        assert fm_model.processes.wriwaqbot3doutput is False
        assert fm_model.processes.volumedrythreshold == pytest.approx(1e-3)
        assert fm_model.processes.depthdrythreshold == pytest.approx(1e-3)

        assert fm_model.particles is not None
        assert fm_model.particles.particlesfile is None
        assert fm_model.particles.particlesreleasefile.filepath is None
        assert fm_model.particles.addtracer is False
        assert fm_model.particles.starttime == pytest.approx(0.0)
        assert fm_model.particles.timestep == pytest.approx(0.0)
        assert fm_model.particles.threedtype == ParticlesThreeDType.DepthAveraged

        assert fm_model.veg is not None
        assert fm_model.veg.vegetationmodelnr == VegetationModelNr.No
        assert fm_model.veg.clveg == pytest.approx(0.8)
        assert fm_model.veg.cdveg == pytest.approx(0.7)
        assert fm_model.veg.cbveg == pytest.approx(0.0)
        assert fm_model.veg.rhoveg == pytest.approx(0.0)
        assert fm_model.veg.stemheightstd == pytest.approx(0.0)

    def test_mdu_with_3d_settings(self):
        input_mdu = (
            test_input_dir / "dflowfm_individual_files" / "special_3d_settings.mdu"
        )
        output_mdu = (
            test_output_dir / "test_mdu_with_3d_settings" / "special_3d_settings.mdu"
        )
        reference_mdu = test_reference_dir / "fm" / "special_3d_settings.mdu"

        fm_model = FMModel(filepath=input_mdu, recurse=False)
        assert fm_model.geometry.kmx == 53
        assert fm_model.geometry.layertype == 1
        assert fm_model.geometry.numtopsig == 20
        assert fm_model.geometry.numtopsiguniform == True
        assert fm_model.geometry.sigmagrowthfactor == pytest.approx(1.19)
        assert fm_model.geometry.dztop == pytest.approx(5.0)
        assert fm_model.geometry.floorlevtoplay == pytest.approx(-5.0)
        assert fm_model.geometry.dztopuniabovez == pytest.approx(-100.0)
        assert fm_model.geometry.keepzlayeringatbed == 2
        assert fm_model.geometry.dxwuimin2d == pytest.approx(0.1)

        fm_model.save(output_mdu, recurse=False)

        assert_files_equal(output_mdu, reference_mdu, [0])

    def test_disk_only_file_model_list_fields_are_initialized_correctly(self):
        data = {"landboundaryfile": [Path("test.ldb")]}

        model = Geometry(**data)

        assert model.landboundaryfile is not None
        assert len(model.landboundaryfile) == 1
        assert isinstance(model.landboundaryfile[0], DiskOnlyFileModel)

    def test_mdu_model(self):
        model = FMModel(
            filepath=Path(
                test_data_dir
                / "input"
                / "e02"
                / "c11_korte-woerden-1d"
                / "dimr_model"
                / "dflowfm"
                / "FlowFM.mdu"
            )
        )
        assert model.geometry.comments.uniformwidth1d == "test"

        output_dir = test_output_dir / self.test_mdu_model.__name__
        output_fn = output_dir / FMModel._generate_name()

        if output_dir.exists():
            try:
                shutil.rmtree(output_dir)
            except PermissionError:
                pass

        model.save(filepath=output_fn, recurse=True)

        assert model.save_location == output_fn
        assert model.save_location.is_file()

        assert model.geometry.frictfile is not None
        frictfile = model.geometry.frictfile[0]
        assert model.geometry.frictfile[0] is not None
        assert model.geometry.frictfile[0].filepath is not None

        assert frictfile.save_location == output_dir / frictfile.filepath
        assert frictfile.save_location.is_file()

        assert model.geometry.structurefile is not None
        structurefile = model.geometry.structurefile[0]
        assert structurefile is not None
        assert structurefile.filepath is not None

        assert structurefile.save_location == output_dir / structurefile.filepath
        assert structurefile.save_location.is_file()

    def test_load_model_recurse_false(self):
        model = FMModel(
            filepath=Path(
                test_data_dir
                / "input"
                / "e02"
                / "c11_korte-woerden-1d"
                / "dimr_model"
                / "dflowfm"
                / "FlowFM.mdu"
            ),
            recurse=False,
        )

        # Assert that references to child models are preserved, but child models are not loaded
        assert model.geometry.structurefile is not None
        assert len(model.geometry.structurefile) == 1
        assert model.geometry.structurefile[0].filepath == Path("structures.ini")
        assert not any(model.geometry.structurefile[0].structure)

    def test_mdu_from_scratch(self):
        output_fn = Path(test_output_dir / "scratch.mdu")
        model = FMModel()
        model.filepath = output_fn
        model.save()

    @pytest.mark.parametrize(
        "input",
        [
            pytest.param(None, id="None"),
            pytest.param(Path("some/path/extforce.file"), id="Path"),
            pytest.param(
                DiskOnlyFileModel(Path("some/other/path/extforce.file")), id="Model"
            ),
        ],
    )
    @pytest.mark.parametrize(
        "input_field, create_model, retrieve_field",
        [
            pytest.param(
                "restartfile",
                lambda d: Restart(**d),
                lambda m: m.restartfile,
                id="restartfile",
            ),
            pytest.param(
                "morfile", lambda d: Sediment(**d), lambda m: m.morfile, id="morfile"
            ),
            pytest.param(
                "sedfile", lambda d: Sediment(**d), lambda m: m.sedfile, id="sedfile"
            ),
            pytest.param(
                "flowgeomfile",
                lambda d: Output(**d),
                lambda m: m.flowgeomfile,
                id="flowgeomfile",
            ),
            pytest.param(
                "hisfile", lambda d: Output(**d), lambda m: m.hisfile, id="hisfile"
            ),
            pytest.param(
                "mapfile", lambda d: Output(**d), lambda m: m.mapfile, id="mapfile"
            ),
            pytest.param(
                "mapoutputtimevector",
                lambda d: Output(**d),
                lambda m: m.mapoutputtimevector,
                id="mapoutputtimevector",
            ),
            pytest.param(
                "classmapfile",
                lambda d: Output(**d),
                lambda m: m.classmapfile,
                id="classmapfile",
            ),
            pytest.param(
                "waterlevinifile",
                lambda d: Geometry(**d),
                lambda m: m.waterlevinifile,
                id="waterlevinifile",
            ),
            pytest.param(
                "oned2dlinkfile",
                lambda d: Geometry(**d),
                lambda m: m.oned2dlinkfile,
                id="oned2dlinkfile",
            ),
            pytest.param(
                "proflocfile",
                lambda d: Geometry(**d),
                lambda m: m.proflocfile,
                id="proflocfile",
            ),
            pytest.param(
                "profdeffile",
                lambda d: Geometry(**d),
                lambda m: m.profdeffile,
                id="profdeffile",
            ),
            pytest.param(
                "profdefxyzfile",
                lambda d: Geometry(**d),
                lambda m: m.profdefxyzfile,
                id="profdefxyzfile",
            ),
            pytest.param(
                "manholefile",
                lambda d: Geometry(**d),
                lambda m: m.manholefile,
                id="manholefile",
            ),
            pytest.param(
                "definitionfile",
                lambda d: Calibration(**d),
                lambda m: m.definitionfile,
                id="definitionfile",
            ),
            pytest.param(
                "areafile",
                lambda d: Calibration(**d),
                lambda m: m.areafile,
                id="definitionfile",
            ),
            pytest.param(
                "substancefile",
                lambda d: Processes(**d),
                lambda m: m.substancefile,
                id="substancefile",
            ),
            pytest.param(
                "additionalhistoryoutputfile",
                lambda d: Processes(**d),
                lambda m: m.additionalhistoryoutputfile,
                id="additionalhistoryoutputfile",
            ),
            pytest.param(
                "statisticsfile",
                lambda d: Processes(**d),
                lambda m: m.statisticsfile,
                id="statisticsfile",
            ),
            pytest.param(
                "particlesreleasefile",
                lambda d: Particles(**d),
                lambda m: m.particlesreleasefile,
                id="particlesreleasefile",
            ),
            pytest.param(
                "locationfile",
                _create_boundary,
                lambda m: m.locationfile,
                id="locationfile",
            ),
            pytest.param(
                "frictionvaluesfile",
                lambda d: FrictGeneral(**d),
                lambda m: m.frictionvaluesfile,
                id="frictionvaluesfile",
            ),
        ],
    )
    def test_model_diskonlyfilemodel_field_is_constructed_correctly(
        self,
        input: Union[None, Path, DiskOnlyFileModel],
        input_field: str,
        create_model: Callable[[Dict], object],
        retrieve_field: Callable[[object], DiskOnlyFileModel],
    ):
        data = {input_field: input}
        model = create_model(data)
        relevant_field = retrieve_field(model)

        assert isinstance(relevant_field, DiskOnlyFileModel)

        if isinstance(input, DiskOnlyFileModel):
            assert relevant_field == input
        else:
            assert relevant_field.filepath == input


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
            [ObservationCrossSection]: the objects contained in the fully loaded obs_crs.ini file.
        """

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

    def test_loading_fmmodel_model_with_xyn_obsfile(self):
        file_path = test_input_dir / "obsfile_cases" / "single_xyn" / "fm.mdu"
        model = FMModel(file_path)

        expected_points = [
            XYNPoint(x=1.1, y=2.2, n="ObservationPoint_2D_01"),
            XYNPoint(x=3.3, y=4.4, n="ObservationPoint_2D_02"),
        ]

        obsfile = model.output.obsfile[0]

        assert isinstance(obsfile, XYNModel)
        assert obsfile.points == expected_points

    def test_loading_fmmodel_model_with_ini_obsfile(self):
        file_path = test_input_dir / "obsfile_cases" / "single_ini" / "fm.mdu"
        model = FMModel(file_path)

        expected_points = [
            ObservationPoint(x=1.1, y=2.2, name="ObservationPoint_2D_01"),
            ObservationPoint(x=3.3, y=4.4, name="ObservationPoint_2D_02"),
        ]

        obsfile = model.output.obsfile[0]

        assert isinstance(obsfile, ObservationPointModel)

        assert len(obsfile.observationpoint) == len(expected_points)
        for actual_point, expected_point in zip(
            obsfile.observationpoint, expected_points
        ):
            assert actual_point.x == expected_point.x
            assert actual_point.y == expected_point.y
            assert actual_point.name == expected_point.name

    def test_loading_fmmodel_model_with_both_ini_and_xyn_obsfiles(self):
        file_path = test_input_dir / "obsfile_cases" / "both_ini_and_xyn" / "fm.mdu"
        model = FMModel(file_path)

        assert len(model.output.obsfile) == 2

        obsfile = model.output.obsfile
        xyn_file = obsfile[0]
        assert isinstance(xyn_file, XYNModel)

        expected_xyn_points = [
            XYNPoint(x=1.1, y=2.2, n="ObservationPoint_2D_01"),
            XYNPoint(x=3.3, y=4.4, n="ObservationPoint_2D_02"),
        ]
        assert xyn_file.points == expected_xyn_points

        ini_file = obsfile[1]
        assert isinstance(ini_file, ObservationPointModel)

        expected_ini_points = [
            ObservationPoint(x=1.1, y=2.2, name="ObservationPoint_2D_01"),
            ObservationPoint(x=3.3, y=4.4, name="ObservationPoint_2D_02"),
        ]
        assert len(ini_file.observationpoint) == len(expected_ini_points)

        for actual_point, expected_point in zip(
            ini_file.observationpoint, expected_ini_points
        ):
            assert actual_point.x == expected_point.x
            assert actual_point.y == expected_point.y
            assert actual_point.name == expected_point.name

    def test_mdu_unknown_keyword_loading_throws_valueerror_for_unknown_keyword(
        self, tmp_path
    ):
        tmp_mdu = """
        [General]
        fileVersion           = 1.09
        fileType              = modelDef
        program               = D-Flow FM
        version               = 1.2.100.66357
        autoStart             = 0
        pathsRelativeToParent = 0
        unknownkey            = something
        """

        tmp_mdu_path = tmp_path / "tmp.mdu"
        tmp_mdu_path.write_text(tmp_mdu)

        section_header = "default='General'"
        name = "unknownkey"

        expected_message = (
            f"Unknown keywords are detected in section: '{section_header}', '{[name]}'"
        )

        with pytest.raises(ValueError) as exc_err:
            FMModel(filepath=tmp_mdu_path)

        print(str(exc_err.value))
        assert expected_message in str(exc_err.value)

    def test_mdu_unknown_keywords_loading_throws_valueerror_for_unknown_keywords(
        self, tmp_path
    ):
        tmp_mdu = """
        [General]
        fileVersion           = 1.09
        fileType              = modelDef
        program               = D-Flow FM
        version               = 1.2.100.66357
        autoStart             = 0
        pathsRelativeToParent = 0
        unknownkey            = something
        unknownkey2           = something2
        """

        tmp_mdu_path = tmp_path / "tmp.mdu"
        tmp_mdu_path.write_text(tmp_mdu)

        section_header = "default='General'"
        name = "unknownkey"
        name2 = "unknownkey2"

        expected_message = (
            "Unknown keywords are detected in section: "
            f"'{section_header}', '{[name, name2]}'"
        )
        with pytest.raises(ValueError) as exc_err:
            FMModel(filepath=tmp_mdu_path)

        assert expected_message in str(exc_err.value)

    def test_mdu_unknown_keywords_loading_thrown_valueerror_for_unknown_keyword_does_not_include_excluded_fields(
        self, tmp_path
    ):
        tmp_mdu = """
        [General]
        fileVersion           = 1.09
        fileType              = modelDef
        program               = D-Flow FM
        version               = 1.2.100.66357
        autoStart             = 0
        pathsRelativeToParent = 0
        unknownkey            = something
        """

        tmp_mdu_path = tmp_path / "tmp.mdu"
        tmp_mdu_path.write_text(tmp_mdu)

        with pytest.raises(ValueError) as exc_err:
            model = FMModel(filepath=tmp_mdu_path)

            excluded_fields = model._exclude_fields()
            assert len(excluded_fields) > 0
            for excluded_field in excluded_fields:
                assert excluded_field not in str(exc_err.value)
