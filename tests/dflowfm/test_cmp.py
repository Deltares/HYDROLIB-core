from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from hydrolib.core.basemodel import ModelSaveSettings
from hydrolib.core.dflowfm.cmp.models import CmpModel, CmpRecord
from hydrolib.core.dflowfm.cmp.parser import CmpParser
from hydrolib.core.dflowfm.cmp.serializer import CmpSerializer


class TestCmpModel:
    def test_cmp_model_initialization(self):
        model = CmpModel()
        assert model is not None
        assert len(model.comments) == 0
        assert len(model.components) == 0

    def test_cmp_record_initialization(self):
        record = CmpRecord(period=0.0, amplitude=1.0, phase=2.0)
        assert record is not None
        assert record.period == 0.0


class TestCmpParser:
    def test_cmp_parser_initialization(self):
        parser = CmpParser()
        assert parser is not None
        assert isinstance(parser, CmpParser)

    def test_cmp_parser_parse(self, fs: FakeFilesystem):
        cmp_file = Path("input.cmp")
        fs.create_file(cmp_file, contents="#test content\n0.0   1.0  2.0")

        parser = CmpParser()
        model = parser.parse(cmp_file)
        assert model is not None
        assert model == {
            "comments": ["test content"],
            "components": [{"period": "0.0", "amplitude": "1.0", "phase": "2.0"}],
        }

    def test_cmp_parser_parse_empty_file(self, fs: FakeFilesystem):
        cmp_file = Path("empty.cmp")
        fs.create_file(cmp_file, contents="")

        parser = CmpParser()
        model = parser.parse(cmp_file)
        assert model is not None
        assert model == {"comments": [], "components": []}


class TestCmpSerializer:
    def test_cmp_serializer_initialization(self):
        serializer = CmpSerializer()
        assert serializer is not None
        assert isinstance(serializer, CmpSerializer)

    def test_cmp_serializer_serialize(self, fs: FakeFilesystem):
        data = {
            "comments": ["test comment"],
            "components": [{"period": "0.0", "amplitude": "1.0", "phase": "2.0"}],
        }

        serializer = CmpSerializer()
        cmp_file = Path("/fake/output.cmp")
        save_settings = ModelSaveSettings()

        serializer.serialize(cmp_file, data, save_settings)

        assert fs.exists(cmp_file)
        with open(cmp_file, "r", encoding="utf8") as file:
            content = file.read()
            assert content == "#test comment\n0.0 1.0 2.0"
