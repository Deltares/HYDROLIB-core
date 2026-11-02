import warnings
from pathlib import Path

import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.ext.models import Spatial
from hydrolib.core.dflowfm.inifield.models import InitialField, ParameterField
from hydrolib.tools.extforce_convert.converters import InifieldToSpatialConverter


def _parameter(**kwargs) -> ParameterField:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return ParameterField(**kwargs)


def _initial(**kwargs) -> InitialField:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return InitialField(**kwargs)


class TestKeywordMapping:
    def test_gridded_block_copies_set_keywords(self):
        block = _parameter(
            quantity="frictionCoefficient",
            dataFile="friction.xyz",
            dataFileType="sample",
            interpolationMethod="triangulation",
            operand="+",
            locationType="2d",
        )

        result = InifieldToSpatialConverter().convert(block, Path("friction.xyz"))

        assert isinstance(result, Spatial)
        assert result.quantity == "frictionCoefficient"
        assert result.datafile.filepath == Path("friction.xyz")
        assert result.datafiletype == "sample"
        assert result.interpolationmethod == "triangulation"
        assert result.operand == "add"
        assert result.locationtype == "2d"

    def test_initial_and_parameter_blocks_convert_alike(self):
        kwargs = dict(
            quantity="waterlevelbnd", dataFile="a.xyz", dataFileType="sample"
        )

        from_initial = InifieldToSpatialConverter().convert(
            _initial(**kwargs), Path("a.xyz")
        )
        from_parameter = InifieldToSpatialConverter().convert(
            _parameter(**kwargs), Path("a.xyz")
        )

        assert from_initial == from_parameter

    @pytest.mark.parametrize("old, new", [("O", "override"), ("A", "overrideIfMissing"),
                                          ("+", "add"), ("*", "multiply"),
                                          ("X", "maximum"), ("N", "minimum")])
    def test_operand_letters_become_words(self, old, new):
        block = _parameter(
            quantity="q", dataFile="a.xyz", dataFileType="sample", operand=old
        )

        result = InifieldToSpatialConverter().convert(block, Path("a.xyz"))

        assert result.operand == new

    @pytest.mark.parametrize("old, new", [(True, True), (False, False)])
    def test_extrapolation_method_becomes_extrapolation_allowed(self, old, new):
        block = _parameter(
            quantity="q",
            dataFile="a.xyz",
            dataFileType="sample",
            extrapolationMethod=old,
        )

        result = InifieldToSpatialConverter().convert(block, Path("a.xyz"))

        assert result.extrapolationallowed is new

    def test_averaging_keywords_are_copied(self):
        block = _parameter(
            quantity="q",
            dataFile="a.xyz",
            dataFileType="sample",
            interpolationMethod="averaging",
            averagingType="mean",
            averagingRelSize=1.5,
            averagingNumMin=2,
            averagingPercentile=10.0,
        )

        result = InifieldToSpatialConverter().convert(block, Path("a.xyz"))

        assert result.averagingtype == "mean"
        assert result.averagingrelsize == 1.5
        assert result.averagingnummin == 2
        assert result.averagingpercentile == 10.0

    def test_tracer_keywords_are_copied(self):
        block = _initial(
            quantity="initialtracerfoo",
            dataFile="a.xyz",
            dataFileType="sample",
            tracerFallVelocity=0.5,
            tracerDecayTime=3.0,
        )

        result = InifieldToSpatialConverter().convert(block, Path("a.xyz"))

        assert result.tracerfallvelocity == 0.5
        assert result.tracerdecaytime == 3.0

    def test_keywords_not_set_in_source_stay_unset(self):
        block = _parameter(quantity="q", dataFile="a.xyz", dataFileType="sample")

        result = InifieldToSpatialConverter().convert(block, Path("a.xyz"))

        assert result.model_fields_set == {"quantity", "datafile", "datafiletype"}


class TestPolygonWithValue:
    def test_polygon_value_becomes_target_mask_and_data_value(self):
        block = _parameter(
            quantity="frictionCoefficient",
            dataFile="region.pol",
            dataFileType="polygon",
            interpolationMethod="constant",
            value=0.023,
        )

        result = InifieldToSpatialConverter().convert(block, Path("region.pol"))

        assert result.datavalue == 0.023
        assert result.interpolationmethod == "constant"
        assert result.targetmaskfile.filepath == Path("region.pol")
        assert result.datafile is None
        assert result.datafiletype is None

    def test_polygon_value_without_interpolation_method_gets_constant(self):
        block = _parameter(
            quantity="q", dataFile="region.pol", dataFileType="polygon", value=1.0
        )

        result = InifieldToSpatialConverter().convert(block, Path("region.pol"))

        assert result.interpolationmethod == "constant"

    def test_polygon_value_keeps_operand(self):
        block = _parameter(
            quantity="q",
            dataFile="region.pol",
            dataFileType="polygon",
            interpolationMethod="constant",
            operand="*",
            value=2.0,
        )

        result = InifieldToSpatialConverter().convert(block, Path("region.pol"))

        assert result.operand == "multiply"

    def test_polygon_value_does_not_warn(self):
        block = _parameter(
            quantity="q", dataFile="region.pol", dataFileType="polygon", value=1.0
        )

        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            InifieldToSpatialConverter().convert(block, Path("region.pol"))

    def test_initialvertical_polygon_keeps_data_file(self):
        block = _initial(
            quantity="initialverticalsalinityprofile",
            dataFile="profile.pol",
            dataFileType="polygon",
            interpolationMethod="constant",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            result = InifieldToSpatialConverter().convert(block, Path("profile.pol"))

        assert result.datafiletype == "polygon"
        assert isinstance(result.datafile, DiskOnlyFileModel)
        assert result.datafile.filepath == Path("profile.pol")
        assert result.targetmaskfile is None
        assert result.datavalue is None


class TestVerticalProfileValue:
    def test_value_on_a_vertical_profile_polygon_is_dropped_with_a_warning(self):
        block = _initial(
            quantity="initialverticalsalinityprofile",
            dataFile="profile.pol",
            dataFileType="polygon",
            interpolationMethod="constant",
            value=3.0,
        )

        with pytest.warns(UserWarning, match="value.*initialverticalsalinityprofile"):
            result = InifieldToSpatialConverter().convert(block, Path("profile.pol"))

        assert result.datavalue is None

    def test_vertical_profile_without_value_does_not_warn(self):
        block = _initial(
            quantity="initialverticalsalinityprofile",
            dataFile="profile.pol",
            dataFileType="polygon",
            interpolationMethod="constant",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            InifieldToSpatialConverter().convert(block, Path("profile.pol"))


class TestDataFilePath:
    def test_converted_path_replaces_the_source_path(self):
        block = _parameter(quantity="q", dataFile="a.xyz", dataFileType="sample")

        result = InifieldToSpatialConverter().convert(block, Path("sub/a.xyz"))

        assert result.datafile.filepath == Path("sub/a.xyz")
