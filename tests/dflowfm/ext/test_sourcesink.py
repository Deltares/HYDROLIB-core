"""
Class to test all methods contained in the
hydrolib.core.dflowfm.ext.models.SourceSink class
"""

from pathlib import Path

import numpy as np
import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.ext.models import ExtModel, SourceSink
from tests.utils import test_data_dir


class TestSourceSink:
    """
    Class to test the different types of source/sink forcings.
    """

    def test_sourcesink_fromfile(self):

        filepath = test_data_dir / "input/source-sink/source-sink-new.ext"
        m = ExtModel(filepath)
        assert len(m.sourcesink) == 2
        assert m.sourcesink[0].id == "L1"
        assert np.isclose(m.sourcesink[0].discharge, 10)
        assert np.isclose(m.sourcesink[1].discharge, 20)

    def test_sourcesink_fromdict(self):

        data = {
            "sourcesink": [
                {
                    "id": "L1",
                    "name": "L1",
                    "numCoordinates": 2,
                    "xCoordinates": [0.0, 1.0],
                    "yCoordinates": [0.0, 1.0],
                    "zSink": 0.0,
                    "zSource": 0.0,
                    "area": 1.0,
                    "discharge": 1.23,
                    "salinitydelta": 4.0,
                    "temperatureDelta": 5.0,
                }
            ]
        }
        m = ExtModel(**data)
        assert len(m.sourcesink) == 1
        assert np.isclose(m.sourcesink[0].discharge, 1.23)


class TestSourceSinkValidator:
    """
    class to test the validate_location_specification validator.
    """

    def test_source_sink_with_locationfile(self):
        """Test SourceSink creation with locationfile provided."""
        source_sink = SourceSink(
            id="test1",
            locationfile=DiskOnlyFileModel(filepath=Path("locationfile.pli")),
            discharge=5,
        )
        assert source_sink.locationfile is not None
        assert source_sink.numcoordinates is None
        assert source_sink.xcoordinates is None
        assert source_sink.ycoordinates is None

    def test_source_sink_with_coordinates(self):
        """Test SourceSink creation with coordinates provided."""
        source_sink = SourceSink(
            id="test2",
            numcoordinates=2,
            xcoordinates=[1.0, 2.0],
            ycoordinates=[3.0, 4.0],
            discharge=5,
        )
        assert source_sink.numcoordinates == 2
        assert source_sink.xcoordinates == [1.0, 2.0]
        assert source_sink.ycoordinates == [3.0, 4.0]
        assert source_sink.locationfile.filepath is None

    def test_source_sink_without_locationfile_or_coordinates(self):
        """Test that creating a SourceSink without locationfile or coordinates raises an error."""
        with pytest.raises(
            ValueError,
            match="Either `locationFile` or the combination of `numCoordinates`, `xCoordinates`, and `yCoordinates` must be provided.",
        ):
            SourceSink(id="test3", discharge=None)

    def test_source_sink_with_incomplete_coordinates(self):
        """Test that creating a SourceSink with incomplete coordinates raises an error."""
        with pytest.raises(
            ValueError,
            match="Either `locationFile` or the combination of `numCoordinates`, `xCoordinates`, and `yCoordinates` must be provided.",
        ):
            SourceSink(
                id="test4",
                numcoordinates=2,
                xcoordinates=[1.0, 2.0],  # ycoordinates missing
                discharge=None,
            )

    def test_source_sink_with_mismatched_coordinates(self):
        """Test that creating a SourceSink with mismatched coordinate lengths raises an error."""
        with pytest.raises(
            ValueError,
            match="Either `locationFile` or the combination of `numCoordinates`, `xCoordinates`, and `yCoordinates` must be provided.",
        ):
            SourceSink(
                id="test5",
                numcoordinates=2,
                xcoordinates=[1.0, 2.0, 3.0],  # Too many x-coordinates
                ycoordinates=[3.0, 4.0],
                discharge=None,
            )

    def test_locationfile_with_zsource_raises(self):
        with pytest.raises(
            ValueError,
            match=r"locationFile.*\.pliz.*cannot be combined with.*zSource",
        ):
            SourceSink(
                id="left",
                locationfile=DiskOnlyFileModel(filepath=Path("left.pliz")),
                zsource=-7.5,
                discharge=1.0,
            )

    def test_locationfile_with_zsink_raises(self):
        with pytest.raises(
            ValueError,
            match=r"locationFile.*\.pliz.*cannot be combined with.*zSink",
        ):
            SourceSink(
                id="left",
                locationfile=DiskOnlyFileModel(filepath=Path("left.pliz")),
                zsink=-2.5,
                discharge=1.0,
            )

    def test_pli_locationfile_with_zsource_allowed(self):
        """Plain `.pli` (no z column) + explicit zSource is valid.

        Used for coupled source-sink where the polyline only provides x,y and
        vertical placement comes from explicit zSource/zSink fields.
        """
        block = SourceSink(
            id="left",
            locationfile=DiskOnlyFileModel(filepath=Path("left.pli")),
            zsource=-2.5,
            zsink=-7.5,
            discharge=1.0,
        )
        assert block.zsource == -2.5
        assert block.zsink == -7.5

    def test_locationfile_with_zsource_list_raises(self):
        with pytest.raises(
            ValueError,
            match=r"locationFile.*\.pliz.*cannot be combined with.*zSource",
        ):
            SourceSink(
                id="left",
                locationfile=DiskOnlyFileModel(filepath=Path("left.pliz")),
                zsource=[-7.5, -3.01],
                discharge=1.0,
            )

    def test_inline_with_zsource_list(self):
        """Range source: zSource carries two values (zmin, zmax)."""
        block = SourceSink(
            id="left",
            numcoordinates=1,
            xcoordinates=[25.0],
            ycoordinates=[5.0],
            zsource=[-7.5, -3.01],
            discharge=1.0,
        )
        assert block.zsource == [-7.5, -3.01]
        assert block.zsink is None

    def test_inline_with_zsource_and_zsink_lists(self):
        """Coupled range source-sink: both zSource and zSink are 2-value lists."""
        block = SourceSink(
            id="left",
            numcoordinates=2,
            xcoordinates=[25.0, 175.0],
            ycoordinates=[5.0, 5.0],
            zsource=[-2.5, -1.1],
            zsink=[-7.5, -2.2],
            discharge=1.0,
        )
        assert block.zsource == [-2.5, -1.1]
        assert block.zsink == [-7.5, -2.2]

    def test_inline_with_scalar_zsource_zsink(self):
        """Coupled point source-sink: scalar zSource + scalar zSink."""
        block = SourceSink(
            id="left",
            numcoordinates=2,
            xcoordinates=[25.0, 175.0],
            ycoordinates=[5.0, 5.0],
            zsource=-2.5,
            zsink=-7.5,
            discharge=1.0,
        )
        assert block.zsource == -2.5
        assert block.zsink == -7.5
