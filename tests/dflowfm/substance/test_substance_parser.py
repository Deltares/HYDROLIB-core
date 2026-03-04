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


class TestSubstanceParserExtractQuotedValues:
    """Tests for SubstanceParser._extract_quoted_values."""

    def test_single_quoted_value(self):
        """Test extracting a single quoted value."""
        result = SubstanceParser._extract_quoted_values("description 'hello world'")
        assert result == ["hello world"], f"Expected ['hello world'], got {result}"

    def test_multiple_quoted_values(self):
        """Test extracting multiple quoted values."""
        result = SubstanceParser._extract_quoted_values(
            "name  'proc1' 'description here'"
        )
        assert result == ["proc1", "description here"], f"Got {result}"

    def test_no_quotes(self):
        """Test text with no quoted values returns empty list."""
        result = SubstanceParser._extract_quoted_values("value 0.1500E+02")
        assert result == [], f"Expected [], got {result}"

    def test_empty_quoted_value(self):
        """Test extracting an empty quoted value ''."""
        result = SubstanceParser._extract_quoted_values("description ''")
        assert result == [""], f"Expected [''], got {result}"

    def test_empty_string(self):
        """Test extracting from empty string."""
        result = SubstanceParser._extract_quoted_values("")
        assert result == [], f"Expected [], got {result}"


class TestSubstanceParserParseFieldLine:
    """Tests for SubstanceParser._parse_field_line."""

    def test_quoted_value(self):
        """Test parsing a field line with a quoted value.

        Test scenario:
            ``description 'some text'`` returns ("description", "some text").
        """
        key, value = SubstanceParser._parse_field_line("   description 'some text'")
        assert key == "description", f"Expected 'description', got '{key}'"
        assert value == "some text", f"Expected 'some text', got '{value}'"

    def test_unquoted_value(self):
        """Test parsing a field line with an unquoted numeric value.

        Test scenario:
            ``value 0.1500E+02`` returns ("value", "0.1500E+02").
        """
        key, value = SubstanceParser._parse_field_line("   value  0.1500E+02")
        assert key == "value", f"Expected 'value', got '{key}'"
        assert value == "0.1500E+02", f"Expected '0.1500E+02', got '{value}'"

    def test_key_only_no_value(self):
        """Test parsing a field line with only a key.

        Test scenario:
            A line with just a keyword and no value.
        """
        key, value = SubstanceParser._parse_field_line("   keyword")
        assert key == "keyword", f"Expected 'keyword', got '{key}'"
        assert value == "", f"Expected '', got '{value}'"

    def test_case_insensitive_key(self):
        """Test that keys are lowercased.

        Test scenario:
            ``DESCRIPTION 'text'`` should return key as ``description``.
        """
        key, value = SubstanceParser._parse_field_line("DESCRIPTION 'text'")
        assert key == "description", f"Expected 'description', got '{key}'"

    def test_hyphenated_key(self):
        """Test parsing a field line with a hyphenated key.

        Test scenario:
            ``concentration-unit '(g/m3)'`` should return key as ``concentration-unit``.
        """
        key, value = SubstanceParser._parse_field_line("   concentration-unit '(g/m3)'")
        assert (
            key == "concentration-unit"
        ), f"Expected 'concentration-unit', got '{key}'"
        assert value == "(g/m3)", f"Expected '(g/m3)', got '{value}'"

    def test_extra_whitespace(self):
        """Test parsing with extra whitespace between key and value.

        Test scenario:
            Multiple spaces/tabs between key and value should be handled.
        """
        key, value = SubstanceParser._parse_field_line("   unit          '(oC)'")
        assert key == "unit", f"Expected 'unit', got '{key}'"
        assert value == "(oC)", f"Expected '(oC)', got '{value}'"
