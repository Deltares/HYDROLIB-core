"""Tests for the BubbleScreen INI block model."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.ext.models import BubbleScreen, ExtModel


class TestBubbleScreen:
    def test_inline_coordinates(self):
        block = BubbleScreen(
            id="bubbles1",
            numcoordinates=4,
            xcoordinates=[450.0, 450.0, 550.0, 550.0],
            ycoordinates=[550.0, 650.0, 650.0, 550.0],
            zlevel=-5.0,
            discharge=1.0,
        )
        assert block.id == "bubbles1"
        assert block.numcoordinates == 4
        assert block.zlevel == -5.0

    def test_locationfile(self):
        block = BubbleScreen(
            id="bubbles1",
            locationfile=DiskOnlyFileModel(filepath=Path("simple_bubbles.pli")),
            zlevel=-5.0,
            discharge=1.0,
        )
        assert block.id == "bubbles1"
        assert block.zlevel == -5.0

    def test_neither_location_raises(self):
        with pytest.raises(
            (ValidationError, ValueError),
            match=r"locationFile.*or.*numCoordinates",
        ):
            BubbleScreen(id="bubbles1", zlevel=-5.0, discharge=1.0)

    def test_mismatched_coordinates_raises(self):
        with pytest.raises((ValidationError, ValueError)):
            BubbleScreen(
                id="bubbles1",
                numcoordinates=4,
                xcoordinates=[450.0, 450.0],
                ycoordinates=[550.0, 650.0, 650.0, 550.0],
                zlevel=-5.0,
                discharge=1.0,
            )


class TestBubbleScreenRoundTrip:
    def test_inline_block_roundtrips(self, tmp_path: Path):
        block = BubbleScreen(
            id="bubbles1",
            numcoordinates=4,
            xcoordinates=[450.0, 450.0, 550.0, 550.0],
            ycoordinates=[550.0, 650.0, 650.0, 550.0],
            zlevel=-5.0,
            discharge=1.0,
        )
        model = ExtModel(bubblescreen=[block])
        out_path = tmp_path / "out.ext"
        model.filepath = out_path
        model.save()

        reread = ExtModel(out_path)
        assert len(reread.bubblescreen) == 1
        assert reread.bubblescreen[0].id == "bubbles1"
        assert reread.bubblescreen[0].zlevel == -5.0
        assert list(reread.bubblescreen[0].xcoordinates) == [
            450.0,
            450.0,
            550.0,
            550.0,
        ]

    def test_locationfile_block_roundtrips(self, tmp_path: Path):
        block = BubbleScreen(
            id="bubbles1",
            locationfile=DiskOnlyFileModel(filepath=Path("simple_bubbles.pli")),
            zlevel=-5.0,
            discharge=1.0,
        )
        model = ExtModel(bubblescreen=[block])
        out_path = tmp_path / "out.ext"
        model.filepath = out_path
        model.save()

        reread = ExtModel(out_path)
        assert len(reread.bubblescreen) == 1
        assert reread.bubblescreen[0].zlevel == -5.0


class TestBubbleScreenInExtModel:
    def test_extmodel_has_bubblescreen_field(self):
        model = ExtModel()
        assert model.bubblescreen == []

    def test_extmodel_parses_bubblescreen_block(self, tmp_path: Path):
        ext_content = (
            "[General]\n"
            "fileVersion = 2.01\n"
            "fileType = extForce\n"
            "\n"
            "[BubbleScreen]\n"
            "id = bubbles1\n"
            "numCoordinates = 4\n"
            "xCoordinates = 450 450 550 550\n"
            "yCoordinates = 550 650 650 550\n"
            "zLevel = -5.0\n"
            "discharge = 1.0\n"
        )
        ext_file = tmp_path / "bubbles.ext"
        ext_file.write_text(ext_content)

        model = ExtModel(ext_file)
        assert len(model.bubblescreen) == 1
        assert model.bubblescreen[0].id == "bubbles1"
        assert model.bubblescreen[0].zlevel == -5.0

    def test_bubblescreen_is_public_api(self):
        from hydrolib.core.dflowfm.ext import BubbleScreen as BS

        assert BS is BubbleScreen
