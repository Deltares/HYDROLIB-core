import pytest

from hydrolib.core.dflowfm.research.models import (
    ResearchFMModel,
    ResearchGeneral,
    ResearchGeometry,
    ResearchNumerics,
    ResearchOutput,
    ResearchPhysics,
    ResearchSediment,
    ResearchTime,
    ResearchTrachytopes,
    ResearchWaves,
    ResearchWind,
    ResearchSedtrails,
)
from tests.utils import test_input_dir


class TestResearchFMModel:
    def test_create_research_fmmodel(self):
        model = ResearchFMModel()

        assert isinstance(model.general, ResearchGeneral)
        assert isinstance(model.geometry, ResearchGeometry)
        assert isinstance(model.numerics, ResearchNumerics)
        assert isinstance(model.physics, ResearchPhysics)
        assert isinstance(model.sediment, ResearchSediment)
        assert isinstance(model.wind, ResearchWind)
        assert isinstance(model.waves, ResearchWaves)
        assert isinstance(model.time, ResearchTime)
        assert isinstance(model.trachytopes, ResearchTrachytopes)
        assert isinstance(model.output, ResearchOutput)

    def test_load_model_with_research_keywords_as_researchfmmodel(self):
        input_mdu = (
            test_input_dir
            / "research"
            / "mdu_with_research_keywords_from_dia_file_2024.03_release.mdu"
        )

        model = ResearchFMModel(filepath=input_mdu)

        # there are too many research keywords to test, so here we just assert a couple of them
        assert model.general.research_inputspecific == False
        assert model.geometry.research_helmert == False
        assert model.numerics.research_epseps == pytest.approx(1e-32)
        assert model.physics.research_uniffrictcoef1d2d == pytest.approx(2.3e-2)
        assert model.sediment.research_implicitfallvelocity == 1
        assert model.wind.research_wind_eachstep == 0
        assert model.waves.research_threedwaveboundarylayer == 1
        assert model.time.research_dtfacmax == pytest.approx(1.1)
        assert model.trachytopes.research_trtmnh == pytest.approx(0.1)
        assert model.output.research_mbainterval == pytest.approx(0.0)

    def test_sedtrails_fromscratch(self):
        model = ResearchFMModel()
        model.sedtrails = ResearchSedtrails()

        model.sedtrails.research_sedtrailsgrid = r"c:\random.txt"
        model.sedtrails.research_sedtrailsanalysis = "all"
        model.sedtrails.research_sedtrailsinterval = [1.0, 2.0, 3.0]
        model.sedtrails.research_sedtrailsoutputfile = r"c:\random2.txt"

    def test_sedtrails_can_be_loaded_from_mdu(self):
        input_mdu = (
            test_input_dir
            / "research"
            / "mdu_with_research_keywords_from_dia_file_2024.03_release.mdu"
        )

        model = ResearchFMModel(filepath=input_mdu)

        assert str(model.sedtrails.research_sedtrailsgrid) == r"c:\test.txt"
        assert model.sedtrails.research_sedtrailsanalysis == "all"
        assert model.sedtrails.research_sedtrailsinterval == [3600.0, 1.1, 2.2]
        assert str(model.sedtrails.research_sedtrailsoutputfile) == r"d:\test2.txt"
