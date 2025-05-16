"""
Class to test all methods contained in the
hydrolib.core.dflowfm.ext.models.SourceSink class
"""

from pathlib import Path

import numpy as np
import pytest

from hydrolib.core.basemodel import DiskOnlyFileModel
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
                    "locationFile": "foobar.pli",
                    "zSink": 0.0,
                    "zSource": 0.0,
                    "area": 1.0,
                    "discharge": 1.23,
                    "salinityDelta": 4.0,
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
