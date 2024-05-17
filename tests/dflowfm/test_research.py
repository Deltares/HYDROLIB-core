from pathlib import Path

from hydrolib.core.dflowfm.research.models import ResearchFMModel


class TestResearchFMModel:
    def test_create_research_fmmodel(self):
        model = ResearchFMModel()

        model.geometry.toplayminthick = 123.456

        model.filepath = Path(r"D:\temp\research.mdu")
        model.save()

    def test_load_research_model(self):
        model = ResearchFMModel(filepath=Path(r"D:\temp\research.mdu"))


        assert model.geometry.toplayminthick == 123.456
