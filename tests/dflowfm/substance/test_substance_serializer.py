from pathlib import Path

import pytest

from hydrolib.core.base.models import ModelSaveSettings
from hydrolib.core.dflowfm.substance.serializer import (
    SubstanceSerializer,
    SubstanceSerializerConfig,
)


@pytest.fixture
def default_config():
    """Provide default serializer config."""
    return SubstanceSerializerConfig()


@pytest.fixture
def default_save_settings():
    """Provide default save settings."""
    return ModelSaveSettings()


class TestSubstanceSerializerConfig:
    """Tests for SubstanceSerializerConfig."""

    def test_default_float_format(self):
        """Test that the default float format is .4E.

        Test scenario:
            Default config should produce scientific notation with 4 decimal places.
        """
        config = SubstanceSerializerConfig()
        assert (
            config.float_format == ".4E"
        ), f"Expected '.4E', got '{config.float_format}'"

    def test_custom_float_format(self):
        """Test that float format can be customized."""
        config = SubstanceSerializerConfig(float_format=".2f")
        assert (
            config.float_format == ".2f"
        ), f"Expected '.2f', got '{config.float_format}'"


class TestSubstanceSerializerSerializeSubstance:
    """Tests for SubstanceSerializer._serialize_substance."""

    def test_active_substance(self):
        """Test serializing an active substance block.

        Test scenario:
            Active substance should produce 5 lines with 'active' type.
        """
        substance = {
            "name": "OXY",
            "type": "active",
            "description": "Dissolved Oxygen",
            "concentration_unit": "(g/m3)",
            "waste_load_unit": "-",
        }
        lines = SubstanceSerializer._serialize_substance(substance)
        assert len(lines) == 5, f"Expected 5 lines, got {len(lines)}"
        assert lines[0] == "substance 'OXY' active", f"Got header: {lines[0]}"
        assert (
            lines[1] == "   description        'Dissolved Oxygen'"
        ), f"Got desc: {lines[1]}"
        assert lines[2] == "   concentration-unit '(g/m3)'", f"Got conc: {lines[2]}"
        assert lines[3] == "   waste-load-unit    '-'", f"Got wl: {lines[3]}"
        assert lines[4] == "end-substance", f"Got end: {lines[4]}"

    def test_inactive_substance(self):
        """Test serializing an inactive substance block.

        Test scenario:
            Inactive substance should have 'inactive' in the header line.
        """
        substance = {
            "name": "DetCS1",
            "type": "inactive",
            "description": "DetC in layer S1",
            "concentration_unit": "(gC/m2)",
            "waste_load_unit": "-",
        }
        lines = SubstanceSerializer._serialize_substance(substance)
        assert "inactive" in lines[0], f"Expected 'inactive' in header: {lines[0]}"

    def test_missing_keys_use_defaults(self):
        """Test that missing dict keys use default values.

        Test scenario:
            An empty dict should produce a substance with empty strings and 'active' type.
        """
        lines = SubstanceSerializer._serialize_substance({})
        assert lines[0] == "substance '' active", f"Got header: {lines[0]}"
        assert lines[3] == "   waste-load-unit    '-'", f"Got wl default: {lines[3]}"


class TestSubstanceSerializerSerializeParameter:
    """Tests for SubstanceSerializer._serialize_parameter."""

    def test_parameter_with_scientific_notation(self, default_config):
        """Test serializing a parameter with default .4E float format.

        Test scenario:
            Value 15.0 should be formatted as '1.5000E+01' with .4E format.
        """
        parameter = {
            "name": "Temp",
            "description": "ambient water temperature",
            "unit": "(oC)",
            "value": 15.0,
        }
        lines = SubstanceSerializer._serialize_parameter(parameter, default_config)
        assert len(lines) == 5, f"Expected 5 lines, got {len(lines)}"
        assert lines[0] == "parameter 'Temp'", f"Got header: {lines[0]}"
        assert "1.5000E+01" in lines[3], f"Got value line: {lines[3]}"
        assert lines[4] == "end-parameter", f"Got end: {lines[4]}"

    def test_parameter_negative_value(self, default_config):
        """Test serializing a parameter with a negative value.

        Test scenario:
            Value -999.0 should be formatted as '-9.9900E+02'.
        """
        parameter = {
            "name": "Special",
            "description": "special value",
            "unit": "(-)",
            "value": -999.0,
        }
        lines = SubstanceSerializer._serialize_parameter(parameter, default_config)
        assert "-9.9900E+02" in lines[3], f"Got value line: {lines[3]}"

    def test_parameter_zero_value(self, default_config):
        """Test serializing a parameter with value zero.

        Test scenario:
            Value 0 should be formatted as '0.0000E+00'.
        """
        parameter = {"name": "Zero", "description": "zero", "unit": "(-)", "value": 0}
        lines = SubstanceSerializer._serialize_parameter(parameter, default_config)
        assert "0.0000E+00" in lines[3], f"Got value line: {lines[3]}"

    def test_parameter_empty_float_format(self):
        """Test serializing with empty float_format uses str().

        Test scenario:
            When float_format is empty string, value should use str() conversion.
        """
        config = SubstanceSerializerConfig(float_format="")
        parameter = {"name": "P", "description": "d", "unit": "u", "value": 15.0}
        lines = SubstanceSerializer._serialize_parameter(parameter, config)
        assert "15.0" in lines[3], f"Got value line: {lines[3]}"


class TestSubstanceSerializerSerializeOutput:
    """Tests for SubstanceSerializer._serialize_output."""

    def test_output_block(self):
        """Test serializing an output block.

        Test scenario:
            Output should produce 3 lines: header, description, end.
        """
        output = {"name": "Chlfa", "description": "Chlorophyll-a concentration"}
        lines = SubstanceSerializer._serialize_output(output)
        assert len(lines) == 3, f"Expected 3 lines, got {len(lines)}"
        assert lines[0] == "output 'Chlfa'", f"Got header: {lines[0]}"
        assert (
            lines[1] == "   description   'Chlorophyll-a concentration'"
        ), f"Got desc: {lines[1]}"
        assert lines[2] == "end-output", f"Got end: {lines[2]}"

    def test_output_empty_description(self):
        """Test serializing an output with empty description."""
        output = {"name": "X", "description": ""}
        lines = SubstanceSerializer._serialize_output(output)
        assert lines[1] == "   description   ''", f"Got desc: {lines[1]}"


class TestSubstanceSerializerSerializeActiveProcesses:
    """Tests for SubstanceSerializer._serialize_active_processes."""

    def test_multiple_processes(self):
        """Test serializing multiple active processes.

        Test scenario:
            Two processes should produce opening, 2 name lines, closing.
        """
        processes = [
            {"name": "RearOXY", "description": "Reaeration of oxygen"},
            {"name": "BLOOM_P", "description": "BLOOM II algae module"},
        ]
        lines = SubstanceSerializer._serialize_active_processes(processes)
        assert len(lines) == 4, f"Expected 4 lines, got {len(lines)}"
        assert lines[0] == "active-processes", f"Got opening: {lines[0]}"
        assert (
            lines[1] == "   name  'RearOXY' 'Reaeration of oxygen'"
        ), f"Got line 1: {lines[1]}"
        assert lines[3] == "end-active-processes", f"Got closing: {lines[3]}"

    def test_empty_processes_list(self):
        """Test serializing an empty processes list.

        Test scenario:
            Empty list should still produce opening and closing lines.
        """
        lines = SubstanceSerializer._serialize_active_processes([])
        assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"
        assert lines[0] == "active-processes"
        assert lines[1] == "end-active-processes"


class TestSubstanceSerializerSerialize:
    """Tests for SubstanceSerializer.serialize — the top-level serialize entry point."""

    def test_serialize_creates_file(
        self, tmp_path: Path, default_config, default_save_settings
    ):
        """Test that serialize creates the output file.

        Test scenario:
            Serializing minimal data should create the file at the given path.
        """
        data = {
            "substances": [
                {
                    "name": "OXY",
                    "type": "active",
                    "description": "Dissolved Oxygen",
                    "concentration_unit": "(g/m3)",
                    "waste_load_unit": "-",
                }
            ],
            "parameters": [],
            "outputs": [],
            "active_processes": {"processes": []},
        }
        output_path = tmp_path / "test.sub"
        SubstanceSerializer.serialize(
            output_path, data, default_config, default_save_settings
        )
        assert output_path.exists(), "Output file should exist"

    def test_serialize_empty_data(
        self, tmp_path: Path, default_config, default_save_settings
    ):
        """Test serializing completely empty data.

        Test scenario:
            Empty data should create a file with no content (or just a newline).
        """
        data = {
            "substances": [],
            "parameters": [],
            "outputs": [],
            "active_processes": {"processes": []},
        }
        output_path = tmp_path / "empty.sub"
        SubstanceSerializer.serialize(
            output_path, data, default_config, default_save_settings
        )
        assert output_path.exists(), "Output file should exist even for empty data"
        content = output_path.read_text(encoding="utf-8")
        assert content.strip() == "", f"Expected empty content, got: {content!r}"

    def test_serialize_creates_parent_dirs(
        self, tmp_path: Path, default_config, default_save_settings
    ):
        """Test that serialize creates parent directories if they don't exist.

        Test scenario:
            Path with non-existent parent directories should be created automatically.
        """
        data = {
            "substances": [],
            "parameters": [],
            "outputs": [],
            "active_processes": {"processes": []},
        }
        output_path = tmp_path / "deep" / "nested" / "dir" / "test.sub"
        SubstanceSerializer.serialize(
            output_path, data, default_config, default_save_settings
        )
        assert output_path.exists(), "File should be created with parent dirs"

    def test_serialize_skips_empty_active_processes(
        self, tmp_path: Path, default_config, default_save_settings
    ):
        """Test that empty active_processes does not write active-processes block.

        Test scenario:
            When processes list is empty, no active-processes block should appear in output.
        """
        data = {
            "substances": [
                {
                    "name": "X",
                    "type": "active",
                    "description": "d",
                    "concentration_unit": "u",
                    "waste_load_unit": "-",
                }
            ],
            "parameters": [],
            "outputs": [],
            "active_processes": {"processes": []},
        }
        output_path = tmp_path / "no_procs.sub"
        SubstanceSerializer.serialize(
            output_path, data, default_config, default_save_settings
        )
        content = output_path.read_text(encoding="utf-8")
        assert (
            "active-processes" not in content
        ), f"active-processes block should not appear: {content}"

    def test_serialize_includes_active_processes_when_present(
        self, tmp_path: Path, default_config, default_save_settings
    ):
        """Test that active-processes block is written when processes exist.

        Test scenario:
            Non-empty processes list should produce the active-processes block.
        """
        data = {
            "substances": [],
            "parameters": [],
            "outputs": [],
            "active_processes": {
                "processes": [{"name": "Proc1", "description": "desc1"}]
            },
        }
        output_path = tmp_path / "with_procs.sub"
        SubstanceSerializer.serialize(
            output_path, data, default_config, default_save_settings
        )
        content = output_path.read_text(encoding="utf-8")
        assert (
            "active-processes" in content
        ), f"Expected active-processes block: {content}"
        assert (
            "end-active-processes" in content
        ), f"Expected end-active-processes: {content}"
