from pathlib import Path

import pytest

from hydrolib.core.dflowfm.substance.parser import SubstanceParser


class TestSubstanceParserParse:
    """Tests for SubstanceParser.parse — the top-level parse entry point."""

    def test_parse_counts(self, input_files_dir: Path):
        """Test that parse returns correct counts for all block types.

        Test scenario:
            Parse the standard substance-file.sub that has 2 of each block type.
        """
        path = input_files_dir / "substances" / "substance-file.sub"
        data = SubstanceParser.parse(path)
        assert (
            len(data["substances"]) == 2
        ), f"Expected 2 substances, got {len(data['substances'])}"
        assert (
            len(data["parameters"]) == 2
        ), f"Expected 2 parameters, got {len(data['parameters'])}"
        assert (
            len(data["outputs"]) == 2
        ), f"Expected 2 outputs, got {len(data['outputs'])}"
        assert (
            len(data["active_processes"]["processes"]) == 2
        ), f"Expected 2 processes, got {len(data['active_processes']['processes'])}"

    def test_parse_empty_file(self, input_files_dir: Path):
        """Test that parse returns empty collections for an empty file.

        Test scenario:
            An empty .sub file should produce empty lists for all block types.
        """
        path = input_files_dir / "substances" / "empty-file.sub"
        data = SubstanceParser.parse(path)
        assert (
            data["substances"] == []
        ), f"Expected empty substances, got {data['substances']}"
        assert (
            data["parameters"] == []
        ), f"Expected empty parameters, got {data['parameters']}"
        assert data["outputs"] == [], f"Expected empty outputs, got {data['outputs']}"
        assert (
            data["active_processes"]["processes"] == []
        ), f"Expected empty processes, got {data['active_processes']['processes']}"

    def test_parse_only_parameters(self, input_files_dir: Path):
        """Test parsing a file with only parameter blocks.

        Test scenario:
            File has 3 parameters but no substances, outputs, or processes.
        """
        path = input_files_dir / "substances" / "only-parameters.sub"
        data = SubstanceParser.parse(path)
        assert (
            len(data["substances"]) == 0
        ), f"Expected 0 substances, got {len(data['substances'])}"
        assert (
            len(data["parameters"]) == 3
        ), f"Expected 3 parameters, got {len(data['parameters'])}"
        assert (
            len(data["outputs"]) == 0
        ), f"Expected 0 outputs, got {len(data['outputs'])}"

    def test_parse_inactive_substances(self, input_files_dir: Path):
        """Test parsing a file with both active and inactive substances.

        Test scenario:
            First substance is active, second is inactive.
        """
        path = input_files_dir / "substances" / "inactive-substances.sub"
        data = SubstanceParser.parse(path)
        assert (
            len(data["substances"]) == 2
        ), f"Expected 2 substances, got {len(data['substances'])}"
        assert (
            data["substances"][0]["type"] == "active"
        ), f"Expected first substance active, got {data['substances'][0]['type']}"
        assert (
            data["substances"][1]["type"] == "inactive"
        ), f"Expected second substance inactive, got {data['substances'][1]['type']}"

    def test_parse_returns_all_keys(self, input_files_dir: Path):
        """Test that parse always returns all four required keys.

        Test scenario:
            Even for an empty file, the dict must have substances, parameters, outputs,
            active_processes keys.
        """
        path = input_files_dir / "substances" / "empty-file.sub"
        data = SubstanceParser.parse(path)
        expected_keys = {"substances", "parameters", "outputs", "active_processes"}
        assert (
            set(data.keys()) == expected_keys
        ), f"Expected keys {expected_keys}, got {set(data.keys())}"


class TestSubstanceParserSubstanceBlock:
    """Tests for SubstanceParser._parse_substance_block."""

    def test_parse_substance_fields(self, input_files_dir: Path):
        """Test that substance block fields are parsed correctly.

        Test scenario:
            Verify name, type, description, concentration_unit, waste_load_unit
            from the standard test file.
        """
        path = input_files_dir / "substances" / "substance-file.sub"
        data = SubstanceParser.parse(path)
        sub = data["substances"][0]
        assert sub["name"] == "Any-substance-name-1", f"Got name: {sub['name']}"
        assert sub["type"] == "active", f"Got type: {sub['type']}"
        assert (
            sub["description"] == "Any description here"
        ), f"Got description: {sub['description']}"
        assert (
            sub["concentration_unit"] == "Any Unit"
        ), f"Got concentration_unit: {sub['concentration_unit']}"
        assert (
            sub["waste_load_unit"] == "-"
        ), f"Got waste_load_unit: {sub['waste_load_unit']}"

    def test_parse_inactive_substance_type(self, input_files_dir: Path):
        """Test that 'inactive' type is correctly parsed.

        Test scenario:
            The second substance in inactive-substances.sub has type 'inactive'.
        """
        path = input_files_dir / "substances" / "inactive-substances.sub"
        data = SubstanceParser.parse(path)
        sub = data["substances"][1]
        assert sub["name"] == "InactiveSub", f"Got name: {sub['name']}"
        assert sub["type"] == "inactive", f"Got type: {sub['type']}"

    def test_substance_block_without_terminator(self, tmp_path: Path):
        """Test parsing a substance block that lacks end-substance.

        Test scenario:
            Parser should still return the parsed fields, consuming to EOF.
        """
        content = "substance 'Orphan' active\n   description 'no end'\n"
        filepath = tmp_path / "no_end.sub"
        filepath.write_text(content, encoding="utf-8")

        data = SubstanceParser.parse(filepath)
        assert (
            len(data["substances"]) == 1
        ), f"Expected 1 substance, got {len(data['substances'])}"
        assert (
            data["substances"][0]["name"] == "Orphan"
        ), f"Got name: {data['substances'][0]['name']}"
        assert (
            data["substances"][0]["description"] == "no end"
        ), f"Got description: {data['substances'][0]['description']}"


class TestSubstanceParserParameterBlock:
    """Tests for SubstanceParser._parse_parameter_block."""

    def test_parse_parameter_value_as_string(self, input_files_dir: Path):
        """Test that parameter values are returned as raw strings.

        Test scenario:
            Fortran notation like '-0.9990E+03' should be preserved as-is.
        """
        path = input_files_dir / "substances" / "substance-file.sub"
        data = SubstanceParser.parse(path)
        param = data["parameters"][0]
        assert param["name"] == "Any-Parameter-name-1", f"Got name: {param['name']}"
        assert param["value"] == "-0.9990E+03", f"Got value: {param['value']}"

    def test_parse_multiple_parameter_values(self, input_files_dir: Path):
        """Test parsing multiple parameters with different scientific notation values.

        Test scenario:
            File with 3 parameters: positive, positive, negative values.
        """
        path = input_files_dir / "substances" / "only-parameters.sub"
        data = SubstanceParser.parse(path)
        assert (
            data["parameters"][0]["value"] == "0.1500E+02"
        ), f"Got value: {data['parameters'][0]['value']}"
        assert (
            data["parameters"][1]["value"] == "0.3500E+02"
        ), f"Got value: {data['parameters'][1]['value']}"
        assert (
            data["parameters"][2]["value"] == "-0.9990E+03"
        ), f"Got value: {data['parameters'][2]['value']}"

    def test_parse_parameter_all_fields(self, input_files_dir: Path):
        """Test that all parameter fields are parsed.

        Test scenario:
            Verify name, description, unit, value from only-parameters.sub.
        """
        path = input_files_dir / "substances" / "only-parameters.sub"
        data = SubstanceParser.parse(path)
        param = data["parameters"][0]
        assert param["name"] == "Temp", f"Got name: {param['name']}"
        assert (
            param["description"] == "ambient water temperature"
        ), f"Got description: {param['description']}"
        assert param["unit"] == "(oC)", f"Got unit: {param['unit']}"

    def test_parameter_block_without_value_omits_key(self, tmp_path: Path):
        """Test that a parameter block lacking a value line omits the 'value' key.

        Test scenario:
            The parser must not seed an arbitrary default (e.g. 0) for a missing
            value; the key is simply absent so downstream model construction can
            reject the malformed block instead of silently coercing a value.
        """
        content = "parameter 'NoValue'\n   description 'missing value'\n   unit '(-)'\nend-parameter\n"
        filepath = tmp_path / "no_value.sub"
        filepath.write_text(content, encoding="utf-8")

        data = SubstanceParser.parse(filepath)
        param = data["parameters"][0]
        assert (
            "value" not in param
        ), f"Expected no 'value' key for a valueless block, got {param}"


class TestSubstanceParserOutputBlock:
    """Tests for SubstanceParser._parse_output_block."""

    def test_parse_output_fields(self, input_files_dir: Path):
        """Test that output fields are correctly parsed.

        Test scenario:
            Verify name and description from the standard test file.
        """
        path = input_files_dir / "substances" / "substance-file.sub"
        data = SubstanceParser.parse(path)
        out = data["outputs"][0]
        assert out["name"] == "Any-output-name-1", f"Got name: {out['name']}"
        assert (
            out["description"] == "Any description"
        ), f"Got description: {out['description']}"

    def test_parse_output_block_without_terminator(self, tmp_path: Path):
        """Test parsing an output block that lacks end-output.

        Test scenario:
            Parser should still return the parsed fields.
        """
        content = "output 'OrphanOut'\n   description 'no end'\n"
        filepath = tmp_path / "no_end_out.sub"
        filepath.write_text(content, encoding="utf-8")

        data = SubstanceParser.parse(filepath)
        assert (
            len(data["outputs"]) == 1
        ), f"Expected 1 output, got {len(data['outputs'])}"
        assert data["outputs"][0]["description"] == "no end"


class TestSubstanceParserActiveProcessesBlock:
    """Tests for SubstanceParser._parse_active_processes_block."""

    def test_parse_active_processes(self, input_files_dir: Path):
        """Test parsing active-processes block with name/description pairs.

        Test scenario:
            Standard test file has 2 process entries.
        """
        path = input_files_dir / "substances" / "substance-file.sub"
        data = SubstanceParser.parse(path)
        procs = data["active_processes"]["processes"]
        assert procs[0]["name"] == "Any-name-1", f"Got name: {procs[0]['name']}"
        assert (
            procs[0]["description"] == "any description 1"
        ), f"Got description: {procs[0]['description']}"
        assert procs[1]["name"] == "Any-name-2", f"Got name: {procs[1]['name']}"

    def test_parse_active_processes_empty_block(self, tmp_path: Path):
        """Test parsing an active-processes block with no name entries.

        Test scenario:
            Block has opening/closing keywords but no name lines.
        """
        content = "active-processes\nend-active-processes\n"
        filepath = tmp_path / "empty_procs.sub"
        filepath.write_text(content, encoding="utf-8")

        data = SubstanceParser.parse(filepath)
        assert (
            data["active_processes"]["processes"] == []
        ), f"Expected empty processes, got {data['active_processes']['processes']}"

    def test_parse_name_line_with_single_quote(self, tmp_path: Path):
        """Test that a name line with fewer than 2 quoted values is skipped.

        Test scenario:
            A malformed name line with only 1 quoted value should be ignored.
        """
        content = "active-processes\n   name  'OnlyName'\nend-active-processes\n"
        filepath = tmp_path / "single_quote.sub"
        filepath.write_text(content, encoding="utf-8")

        data = SubstanceParser.parse(filepath)
        assert (
            data["active_processes"]["processes"] == []
        ), "Name line with < 2 quoted values should be skipped"


class TestSubstanceParserOneLineBlocks:
    """Tests for files whose blocks are written entirely on a single line."""

    def test_parse_counts(self, input_files_dir: Path):
        """Test that every one-line block is found.

        Test scenario:
            Each block (and its terminator) sits on one line; none may swallow the
            blocks that follow it.
        """
        data = SubstanceParser.parse(
            input_files_dir / "substances" / "one-line-blocks.sub"
        )
        assert len(data["substances"]) == 2, f"Got {data['substances']}"
        assert len(data["parameters"]) == 2, f"Got {data['parameters']}"
        assert len(data["outputs"]) == 2, f"Got {data['outputs']}"
        assert (
            len(data["active_processes"]["processes"]) == 2
        ), f"Got {data['active_processes']}"

    def test_parse_field_values(self, input_files_dir: Path):
        """Test that field values on the header line are read, incl. quoted spaces and `|`/`<`."""
        data = SubstanceParser.parse(
            input_files_dir / "substances" / "one-line-blocks.sub"
        )
        assert data["substances"][0] == {
            "name": "OXY",
            "type": "active",
            "description": "Oxygen",
            "concentration_unit": "gO2/m3",
            "waste_load_unit": "-",
        }
        assert data["substances"][1]["type"] == "inactive"
        assert data["parameters"][1] == {
            "name": "SWAdsP",
            "description": "switch <0=Kd|1=Langmuir>",
            "unit": "-",
            "value": "0.000e+00",
        }
        assert data["outputs"][1] == {"name": "TotN", "description": "total nitrogen"}
        assert data["active_processes"]["processes"][1] == {
            "name": "RearOXY",
            "description": "Reaeration of oxygen",
        }

    def test_one_line_and_multi_line_blocks_are_equivalent(self, tmp_path: Path):
        """Test that line breaks carry no meaning.

        Test scenario:
            The same parameter written on one line and over several lines
            parses to the same dictionary.
        """
        one = tmp_path / "one.sub"
        one.write_text(
            "parameter 'P' description 'd' unit '-' value 1.0 end-parameter\n"
        )
        many = tmp_path / "many.sub"
        many.write_text(
            "parameter 'P'\n  description 'd'\n  unit '-'\n  value 1.0\nend-parameter\n"
        )
        assert SubstanceParser.parse(one) == SubstanceParser.parse(many)


class TestSubstanceParserUnquote:
    """Tests for SubstanceParser._unquote."""

    @pytest.mark.parametrize(
        "token, expected",
        [
            ("'hello world'", "hello world"),
            ("0.1500E+02", "0.1500E+02"),
            ("''", ""),
            ("'", "'"),
        ],
    )
    def test_unquote(self, token: str, expected: str):
        assert SubstanceParser._unquote(token) == expected
