"""Tests for coordinate validation with raw string inputs from the INI parser.

These tests verify the fix for the validator ordering issue where
model_validator(mode="before") checked coordinate counts on raw strings
before field_validator(mode="before") had split them into List[float].

See: https://github.com/Deltares/HYDROLIB-core/issues/1034
"""

from pathlib import Path
from typing import Dict, List, Optional

import pytest
from pydantic import ValidationError

from hydrolib.core.dflowfm.ext.models import Lateral, SourceSink
from hydrolib.core.dflowfm.ini.util import (
    LocationValidationConfiguration,
    validate_location_specification,
)


class TestValidateLocationSpecificationRawStrings:
    """Tests for validate_location_specification with raw string inputs.

    The INI parser returns coordinates as space-separated strings and
    numcoordinates as a string digit. These tests verify that
    validate_location_specification handles this pre-split format
    correctly.
    """

    def test_raw_string_coordinates_with_string_numcoordinates(self):
        """Test validation passes when coordinates and numcoordinates are raw strings.

        Test scenario:
            Simulates the exact format returned by the INI parser:
            numcoordinates="3", xcoordinates="1.0 2.0 3.0", ycoordinates="4.0 5.0 6.0".
        """
        values = {
            "xcoordinates": "1.0 2.0 3.0",
            "ycoordinates": "4.0 5.0 6.0",
            "numcoordinates": "3",
        }

        result = validate_location_specification(values)

        assert result is values, "Should return the same dict on success"

    def test_raw_string_coordinates_with_int_numcoordinates(self):
        """Test validation passes when coordinates are strings but numcoordinates is int.

        Test scenario:
            Mixed format: numcoordinates already parsed to int,
            but coordinates still raw strings.
        """
        values = {
            "xcoordinates": "1.0 2.0 3.0",
            "ycoordinates": "4.0 5.0 6.0",
            "numcoordinates": 3,
        }

        result = validate_location_specification(values)

        assert result is values, "Should return the same dict on success"

    def test_raw_string_single_coordinate(self):
        """Test validation passes with a single coordinate as raw string.

        Test scenario:
            Single coordinate: numcoordinates="1", xcoordinates="5.0", ycoordinates="6.0".
        """
        values = {
            "xcoordinates": "5.0",
            "ycoordinates": "6.0",
            "numcoordinates": "1",
        }

        result = validate_location_specification(values)

        assert result is values, "Single coordinate as string should validate"

    def test_raw_string_coordinates_with_minimum_num_coordinates(self):
        """Test validation passes when minimum_num_coordinates is satisfied by raw strings.

        Test scenario:
            Config requires minimum 3 coordinates. Raw string has exactly 3.
        """
        values = {
            "xcoordinates": "1.0 2.0 3.0",
            "ycoordinates": "4.0 5.0 6.0",
            "numcoordinates": "3",
        }
        config = LocationValidationConfiguration(minimum_num_coordinates=3)

        result = validate_location_specification(values, config=config)

        assert result is values, "Should pass with exactly minimum coordinates"

    def test_raw_string_coordinates_below_minimum_raises_error(self):
        """Test validation rejects raw strings below minimum_num_coordinates.

        Test scenario:
            Config requires minimum 3 coordinates. Raw string has only 2.
        """
        values = {
            "xcoordinates": "1.0 2.0",
            "ycoordinates": "4.0 5.0",
            "numcoordinates": "2",
        }
        config = LocationValidationConfiguration(minimum_num_coordinates=3)

        with pytest.raises(ValueError, match="at least 3 coordinate"):
            validate_location_specification(values, config=config)

    def test_raw_string_mismatched_numcoordinates_raises_error(self):
        """Test validation rejects when numcoordinates doesn't match raw string count.

        Test scenario:
            numcoordinates="5" but only 3 space-separated values in coordinates.
        """
        values = {
            "xcoordinates": "1.0 2.0 3.0",
            "ycoordinates": "4.0 5.0 6.0",
            "numcoordinates": "5",
        }

        with pytest.raises(ValueError, match="numCoordinates should be equal"):
            validate_location_specification(values)

    def test_raw_string_mismatched_x_y_lengths_raises_error(self):
        """Test validation rejects when x and y raw strings have different counts.

        Test scenario:
            xcoordinates has 3 values, ycoordinates has 2 values.
        """
        values = {
            "xcoordinates": "1.0 2.0 3.0",
            "ycoordinates": "4.0 5.0",
            "numcoordinates": "3",
        }

        with pytest.raises(ValueError, match="numCoordinates should be equal"):
            validate_location_specification(values)

    def test_list_coordinates_still_work(self):
        """Test validation still works with pre-parsed list coordinates.

        Test scenario:
            Ensures backward compatibility — pre-split lists still validate.
        """
        values = {
            "xcoordinates": [1.0, 2.0, 3.0],
            "ycoordinates": [4.0, 5.0, 6.0],
            "numcoordinates": 3,
        }

        result = validate_location_specification(values)

        assert result is values, "Pre-parsed lists should still work"


class TestLateralRawStringCoordinates:
    """Tests for Lateral model with raw string coordinates from INI parser.

    The Lateral model has both a model_validator(mode="before") that calls
    validate_location_specification() and a field_validator(mode="before")
    that splits coordinate strings. These tests verify they work together.
    """

    def test_lateral_with_raw_string_polygon_coordinates(self):
        """Test Lateral accepts raw string polygon coordinates.

        Test scenario:
            Simulates how the INI parser delivers polygon lateral data:
            5 space-separated coordinate values as strings.
        """
        lateral = Lateral(
            id="polygon_lateral",
            name="polygon_lateral",
            numcoordinates="5",
            xcoordinates="1.0 2.0 3.0 4.0 5.0",
            ycoordinates="6.0 7.0 8.0 9.0 10.0",
            discharge=1.0,
        )

        assert (
            lateral.numcoordinates == 5
        ), f"Expected numcoordinates=5, got {lateral.numcoordinates}"
        assert lateral.xcoordinates == [
            1.0,
            2.0,
            3.0,
            4.0,
            5.0,
        ], f"Expected 5 x-coordinates, got {lateral.xcoordinates}"
        assert lateral.ycoordinates == [
            6.0,
            7.0,
            8.0,
            9.0,
            10.0,
        ], f"Expected 5 y-coordinates, got {lateral.ycoordinates}"

    def test_lateral_with_raw_string_single_coordinate(self):
        """Test Lateral accepts a single coordinate as raw string.

        Test scenario:
            Minimum valid polygon: numcoordinates="1" with one coordinate each.
        """
        lateral = Lateral(
            id="single_coord",
            name="single_coord",
            numcoordinates="1",
            xcoordinates="663197.49",
            ycoordinates="1525273.29",
            discharge=1.0,
        )

        assert (
            lateral.numcoordinates == 1
        ), f"Expected numcoordinates=1, got {lateral.numcoordinates}"
        assert lateral.xcoordinates == [
            663197.49
        ], f"Expected [663197.49], got {lateral.xcoordinates}"

    def test_lateral_with_list_coordinates_still_works(self):
        """Test Lateral still works with pre-parsed list coordinates.

        Test scenario:
            Backward compatibility — coordinates passed as lists with int numcoordinates.
        """
        lateral = Lateral(
            id="list_lateral",
            name="list_lateral",
            numcoordinates=2,
            xcoordinates=[1.1, 2.2],
            ycoordinates=[3.3, 4.4],
            discharge=1.0,
        )

        assert lateral.xcoordinates == [
            1.1,
            2.2,
        ], f"Expected [1.1, 2.2], got {lateral.xcoordinates}"

    def test_lateral_with_raw_string_mismatched_numcoordinates_raises(self):
        """Test Lateral rejects raw string coordinates with wrong numcoordinates.

        Test scenario:
            numcoordinates="5" but only 3 values in the coordinate strings.
        """
        with pytest.raises(ValidationError):
            Lateral(
                id="bad_lateral",
                name="bad_lateral",
                numcoordinates="5",
                xcoordinates="1.0 2.0 3.0",
                ycoordinates="4.0 5.0 6.0",
                discharge=1.0,
            )

    def test_lateral_branchid_chainage_unaffected(self):
        """Test that branchId+chainage laterals are not affected by the fix.

        Test scenario:
            Point-based lateral using branchId+chainage should still work.
        """
        lateral = Lateral(
            id="point_lateral",
            name="point_lateral",
            branchid="branch_7",
            chainage="370.839",
            discharge=1.0,
        )

        assert (
            lateral.branchid == "branch_7"
        ), f"Expected branchid='branch_7', got '{lateral.branchid}'"


class TestSourceSinkRawStringCoordinates:
    """Tests for SourceSink model with raw string coordinates.

    SourceSink has its own inline validate_location_specification model_validator
    that had the same raw-string issue.
    """

    def test_source_sink_with_raw_string_coordinates(self):
        """Test SourceSink accepts raw string coordinates.

        Test scenario:
            numcoordinates="2", coordinates as space-separated strings.
        """
        ss = SourceSink(
            id="test_ss",
            numcoordinates="2",
            xcoordinates="1.0 2.0",
            ycoordinates="3.0 4.0",
            discharge=5.0,
        )

        assert (
            ss.numcoordinates == 2
        ), f"Expected numcoordinates=2, got {ss.numcoordinates}"

    def test_source_sink_with_raw_string_many_coordinates(self):
        """Test SourceSink accepts many raw string coordinates.

        Test scenario:
            5 space-separated coordinates as strings — the exact scenario
            that triggered the original bug.
        """
        ss = SourceSink(
            id="polygon_ss",
            numcoordinates="5",
            xcoordinates="663197.49 663634.26 662898.64 662500.18 663197.49",
            ycoordinates="1525273.29 1524966.79 1524208.18 1524867.17 1525273.29",
            discharge=5.0,
        )

        assert (
            ss.numcoordinates == 5
        ), f"Expected numcoordinates=5, got {ss.numcoordinates}"

    def test_source_sink_with_list_coordinates_still_works(self):
        """Test SourceSink still works with pre-parsed list coordinates.

        Test scenario:
            Backward compatibility — lists and ints still validate.
        """
        ss = SourceSink(
            id="list_ss",
            numcoordinates=2,
            xcoordinates=[1.0, 2.0],
            ycoordinates=[3.0, 4.0],
            discharge=5.0,
        )

        assert ss.xcoordinates == [
            1.0,
            2.0,
        ], f"Expected [1.0, 2.0], got {ss.xcoordinates}"

    def test_source_sink_with_raw_string_mismatched_raises(self):
        """Test SourceSink rejects raw strings with mismatched counts.

        Test scenario:
            numcoordinates="3" but only 2 values in coordinate strings.
        """
        with pytest.raises(ValidationError):
            SourceSink(
                id="bad_ss",
                numcoordinates="3",
                xcoordinates="1.0 2.0",
                ycoordinates="3.0 4.0",
                discharge=5.0,
            )

    def test_source_sink_locationfile_unaffected(self):
        """Test that locationFile-based SourceSinks are not affected.

        Test scenario:
            SourceSink using locationFile should still work.
        """
        from hydrolib.core.base.models import DiskOnlyFileModel

        ss = SourceSink(
            id="file_ss",
            locationfile=DiskOnlyFileModel(filepath=Path("test.pli")),
            discharge=5.0,
        )

        assert ss.locationfile is not None, "locationfile should be set"
        assert ss.numcoordinates is None, "numcoordinates should be None"
