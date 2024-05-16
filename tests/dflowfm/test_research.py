from pathlib import Path

from hydrolib.core.dflowfm.research.models import ResearchFMModel, ResearchSedtrails


class TestResearchFMModel:
    def test_create_research_fmmodel(self):
        model = ResearchFMModel()
        model.sedtrails = ResearchSedtrails()
        model.sedtrails.sedtrailsoutputfile = Path(r"D:\temp\allow_extra.mdu")

        model.geometry.toplayminthick = 123.456

        model.filepath = Path(r"D:\temp\research.mdu")
        model.save()

    def test_load_research_model(self):
        model = ResearchFMModel(filepath=Path(r"D:\temp\research.mdu"))
        assert model.sedtrails is not None
        assert model.sedtrails.sedtrailsoutputfile is not None
        assert str(model.sedtrails.sedtrailsoutputfile.filepath) == r"D:\temp\allow_extra.mdu"

        assert model.geometry.toplayminthick == 123.456


