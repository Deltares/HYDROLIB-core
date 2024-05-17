from hydrolib.core.dflowfm.research.models import ResearchFMModel, ResearchGeneral, ResearchGeometry, ResearchNumerics, \
    ResearchPhysics, ResearchSediment, ResearchWaves, ResearchTime, ResearchWind, ResearchTrachytopes, ResearchOutput


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
