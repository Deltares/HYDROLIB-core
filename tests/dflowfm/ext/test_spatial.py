"""Unit tests for the TargetLayer enum and Spatial.validate_targetlayer validator."""

import pytest

from hydrolib.core.dflowfm.ext.models import TargetLayer, Spatial


def _make_spatial(targetlayer) -> Spatial:
    """Instantiate a minimal valid Spatial block with the given targetLayer."""
    return Spatial(
        quantity="initialwaqbottest",
        dataFile="some_file.nc",
        dataFileType="netcdf",
        targetLayer=targetlayer,
    )


class TestTargetLayerEnum:
    def test_bottom_value(self):
        assert TargetLayer.bottom == "bottom"

    def test_all_value(self):
        assert TargetLayer.all == "all"

    def test_members(self):
        members = list(TargetLayer)
        assert TargetLayer.bottom in members
        assert TargetLayer.all in members


class TestValidateTargetLayer:
    """Tests for targetlayer coercion via Spatial instantiation."""

    @pytest.mark.parametrize("raw", ["bottom", "Bottom", "BOTTOM"])
    def test_bottom_string_variants(self, raw):
        spatial = _make_spatial(raw)
        assert spatial.targetlayer == TargetLayer.bottom

    @pytest.mark.parametrize("raw", ["all", "All", "ALL"])
    def test_all_string_variants(self, raw):
        spatial = _make_spatial(raw)
        assert spatial.targetlayer == TargetLayer.all

    @pytest.mark.parametrize("raw", ["1", "2", "10", "100"])
    def test_positive_integer_string(self, raw):
        spatial = _make_spatial(raw)
        assert spatial.targetlayer == int(raw)

    def test_positive_integer_int_value(self):
        spatial = _make_spatial(3)
        assert spatial.targetlayer == 3

    def test_none_targetlayer(self):
        spatial = _make_spatial(None)
        assert spatial.targetlayer is None

    @pytest.mark.parametrize("raw", ["0", "-1", "foo", "layer1", ""])
    def test_invalid_value_raises(self, raw):
        with pytest.raises(Exception, match="TargetLayer must be"):
            _make_spatial(raw)
