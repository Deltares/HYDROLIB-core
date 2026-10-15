"""Integration tests for the Latin-1 fallback wiring across all file parsers.

`hydrolib.core.base.parser.open_file_with_fallback_encoding` is wired into every
parser that reads a D-Flow FM / Rainfall-Runoff model file.  These tests feed each
parser a *genuinely non-UTF-8* document — one containing the raw byte `0xB0` (the
degree symbol `°` in Latin-1/Windows-1252, which is an invalid stand-alone UTF-8
byte) — and assert that:

1. the parser no longer raises `UnicodeDecodeError` (the regression the fallback
   fixes), and
2. the degree symbol survives into the parsed result wherever the format preserves
   the field it was placed in.

Every fixture writes raw Latin-1 bytes, and :func:`_assert_is_invalid_utf8` guards
that the crafted input really does exercise the fallback path (a document that
happened to be valid UTF-8 would make the test meaningless).
"""

from pathlib import Path

DEGREE = "\N{DEGREE SIGN}"


def _write_latin1(filepath: Path, text: str) -> Path:
    """Write `text` to `filepath` as raw Latin-1 bytes.

    Args:
        filepath: Destination path.
        text: Content to encode; any `°` becomes the single byte `0xB0`.

    Returns:
        Path: The same `filepath`, for convenient chaining.
    """
    filepath.write_bytes(text.encode("latin-1"))
    return filepath


def _assert_is_invalid_utf8(filepath: Path) -> None:
    """Assert the file cannot be decoded as UTF-8.

    This proves the document genuinely exercises the Latin-1 fallback branch; if it
    were valid UTF-8 the fallback would never be reached and the test would prove
    nothing.

    Args:
        filepath: Path to the file that should NOT be valid UTF-8.
    """
    raised = False
    try:
        filepath.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        raised = True
    assert raised, f"Test input {filepath} is valid UTF-8; it does not exercise the fallback"


class TestParserFallbackEncoding:
    """Feed a non-UTF-8 (0xB0) document through each wired parser."""

    def test_ini_parser(self, tmp_path: Path):
        """Test the generic INI `Parser.parse` reads a non-UTF-8 file.

        Test scenario:
            An INI document whose header comment holds `°` (as byte 0xB0) parses
            into a `Document` without a decode error, and the degree symbol
            survives into the parsed comment.
        """
        from hydrolib.core.dflowfm.ini.parser import Parser

        content = f"# temperature in {DEGREE}C\n[General]\n    fileVersion = 1.09\n    fileType = test\n"
        path = _write_latin1(tmp_path / "test.ini", content)
        _assert_is_invalid_utf8(path)

        result = Parser.parse(path)

        assert result is not None, "Parser.parse returned None for a valid INI document"
        assert DEGREE in str(result), f"Degree symbol lost in parsed INI document: {result!r}"

    def test_bc_forcing_model_parse(self, tmp_path: Path):
        """Test `ForcingModel.parse` reads a non-UTF-8 .bc file.

        Test scenario:
            A .bc forcing block whose `unit` value carries `°` (byte 0xB0) is
            parsed without a decode error and the degree symbol is preserved in the
            flattened result.
        """
        from hydrolib.core.dflowfm.bc.models import ForcingModel

        content = (
            "[Forcing]\n"
            "name = L1_0001\n"
            "function = timeseries\n"
            "timeInterpolation = linear\n"
            "quantity = time\n"
            f"unit = minutes since 2015-01-01 00:00:00 {DEGREE}\n"
            "quantity = waterlevelbnd\n"
            "unit = m\n"
            "0.0 0.01\n"
            "120.0 0.01\n"
        )
        path = _write_latin1(tmp_path / "forcing.bc", content)
        _assert_is_invalid_utf8(path)

        result = ForcingModel.parse(path)

        assert DEGREE in str(result), f"Degree symbol lost in parsed .bc content: {result!r}"

    def test_extold_parser(self, tmp_path: Path):
        """Test the old external-forcing `Parser.parse` reads a non-UTF-8 file.

        Test scenario:
            An old-style .ext file with `°` in its header comment parses into the
            comment/forcing dict without a decode error and keeps the degree symbol.
        """
        from hydrolib.core.dflowfm.extold.parser import Parser

        content = (
            f"* boundary conditions in {DEGREE}C\n"
            "QUANTITY =waterlevelbnd\n"
            "FILENAME =tfl_01.pli\n"
            "FILETYPE =9\n"
            "METHOD   =3\n"
            "OPERAND  =O\n"
        )
        path = _write_latin1(tmp_path / "old.ext", content)
        _assert_is_invalid_utf8(path)

        result = Parser.parse(path)

        assert result["forcing"], "No forcing block parsed from old-style .ext file"
        assert DEGREE in str(result["comment"]), f"Degree symbol lost in .ext comments: {result['comment']!r}"

    def test_cmp_parser(self, tmp_path: Path):
        """Test `CMPParser.parse` reads a non-UTF-8 .cmp file.

        Test scenario:
            A .cmp file whose header comment holds `°` (byte 0xB0) parses into the
            components dict without a decode error and preserves the degree symbol.
        """
        from hydrolib.core.dflowfm.cmp.parser import CMPParser

        content = (
            f"* COLUMN3=Phase (deg {DEGREE})\n"
            "745.0000000     0.1053834     0.0000000\n"
            "745.0000000     1.0000000     45.1200000\n"
        )
        path = _write_latin1(tmp_path / "test.cmp", content)
        _assert_is_invalid_utf8(path)

        result = CMPParser.parse(path)

        assert result["component"], "No components parsed from .cmp file"
        assert DEGREE in str(result["comments"]), f"Degree symbol lost in .cmp comments: {result['comments']!r}"

    def test_xyz_parser(self, tmp_path: Path):
        """Test `XYZParser.parse` reads a non-UTF-8 .xyz file.

        Test scenario:
            An .xyz point whose inline comment holds `°` (byte 0xB0) parses into
            the points list without a decode error and keeps the degree symbol in
            the comment field.
        """
        from hydrolib.core.dflowfm.xyz.parser import XYZParser

        content = f"1.0 2.0 3.0 # station at 15{DEGREE}C\n4.0 5.0 6.0\n"
        path = _write_latin1(tmp_path / "test.xyz", content)
        _assert_is_invalid_utf8(path)

        result = XYZParser.parse(path)

        assert len(result["points"]) == 2, f"Expected 2 points, got {len(result['points'])}"
        assert result["points"][0]["comment"] == f"station at 15{DEGREE}C", (
            f"Degree symbol lost in .xyz comment: {result['points'][0]['comment']!r}"
        )

    def test_xyn_parser(self, tmp_path: Path):
        """Test `XYNParser.parse` reads a non-UTF-8 .xyn file.

        Test scenario:
            An .xyn observation point whose quoted name holds `°` (byte 0xB0)
            parses without a decode error and preserves the degree symbol in the
            name field.
        """
        from hydrolib.core.dflowfm.xyn.parser import XYNParser

        content = f"50000 50000 'loc {DEGREE}'\n900000 50000 loc02\n"
        path = _write_latin1(tmp_path / "test.xyn", content)
        _assert_is_invalid_utf8(path)

        result = XYNParser.parse(path)

        assert len(result["points"]) == 2, f"Expected 2 points, got {len(result['points'])}"
        assert result["points"][0]["n"] == f"loc {DEGREE}", (
            f"Degree symbol lost in .xyn name: {result['points'][0]['n']!r}"
        )

    def test_t3d_parser(self, tmp_path: Path):
        """Test `T3DParser.parse` reads a non-UTF-8 .t3d file.

        Test scenario:
            A .t3d file whose header comment holds `°` (byte 0xB0) parses into the
            records/layers dict without a decode error and keeps the degree symbol.
        """
        from hydrolib.core.dflowfm.t3d.parser import T3DParser

        content = (
            f"# temperature profile in {DEGREE}C\n"
            "LAYER_TYPE=SIGMA\n"
            "LAYERS=0.0 0.5 1.0\n"
            "TIME = 0 seconds since 2006-01-01 00:00:00 +00:00\n"
            "40 35 30\n"
        )
        path = _write_latin1(tmp_path / "test.t3d", content)
        _assert_is_invalid_utf8(path)

        result = T3DParser.parse(path)

        assert result["records"], "No records parsed from .t3d file"
        assert DEGREE in str(result["comments"]), f"Degree symbol lost in .t3d comments: {result['comments']!r}"

    def test_polyfile_parser(self, tmp_path: Path):
        """Test `read_polyfile` reads a non-UTF-8 .pli file.

        Test scenario:
            A poly file whose description line holds `°` (byte 0xB0) parses into a
            `PolyObject` without a decode error and preserves the degree symbol in
            the object description.
        """
        from hydrolib.core.dflowfm.polyfile.parser import read_polyfile

        content = (
            f"* boundary in {DEGREE}C\n"
            "L1\n"
            "    2    2\n"
            "    0.0    0.0\n"
            "    0.0    2.0\n"
        )
        path = _write_latin1(tmp_path / "test.pli", content)
        _assert_is_invalid_utf8(path)

        result = read_polyfile(path)

        assert result["objects"], "No poly objects parsed from .pli file"
        assert DEGREE in str(result["objects"][0].description), (
            f"Degree symbol lost in .pli description: {result['objects'][0].description!r}"
        )

    def test_rr_topology_parser(self, tmp_path: Path):
        """Test `NetworkTopologyFileParser.parse` reads a non-UTF-8 topology file.

        Test scenario:
            An RR node topology record whose quoted `nm` value holds `°` (byte
            0xB0) parses without a decode error and preserves the degree symbol in
            the record.
        """
        from hydrolib.core.rr.topology.parser import NetworkTopologyFileParser

        content = f"NODE id 'n1' nm 'node{DEGREE}' node\n"
        path = _write_latin1(tmp_path / "3B_NOD.TP", content)
        _assert_is_invalid_utf8(path)

        result = NetworkTopologyFileParser("node").parse(path)

        assert len(result["node"]) == 1, f"Expected 1 node record, got {len(result['node'])}"
        assert result["node"][0]["nm"] == f"node{DEGREE}", (
            f"Degree symbol lost in topology record: {result['node'][0]!r}"
        )

    def test_rr_fnm_read(self, tmp_path: Path):
        """Test the RR `read` parser reads a non-UTF-8 .fnm file.

        Test scenario:
            An .fnm file whose first value holds `°` (byte 0xB0) is read without a
            decode error and the degree symbol survives into the resulting mapping.
        """
        from hydrolib.core.rr.parser import read

        keys = ["control_file", "node_data", "link_data"]
        content = f"'control {DEGREE}.file'\n'nodes.dat'\n'links.dat'\n"
        path = _write_latin1(tmp_path / "test.fnm", content)
        _assert_is_invalid_utf8(path)

        result = read(keys, path)

        assert result["control_file"] == f"control {DEGREE}.file", (
            f"Degree symbol lost in .fnm value: {result['control_file']!r}"
        )

    def test_rr_meteo_bui_parser(self, tmp_path: Path):
        """Test `BuiParser.parse` reads a non-UTF-8 .bui file.

        Test scenario:
            A .bui precipitation file whose station name holds `°` (byte 0xB0)
            parses without a decode error and preserves the degree symbol in the
            station names.
        """
        from hydrolib.core.rr.meteo.parser import BuiParser

        content = (
            "*Name of this file: DEFAULT.BUI\n"
            "1\n"
            "*Aantal stations\n"
            "1\n"
            "*Namen van stations\n"
            f"'De Bilt {DEGREE}'\n"
            "*Aantal gebeurtenissen en timestep\n"
            "1 3600\n"
            "2021 4 20 7 0 0 7 0 0 0\n"
            "0.100\n"
        )
        path = _write_latin1(tmp_path / "DEFAULT.BUI", content)
        _assert_is_invalid_utf8(path)

        result = BuiParser.parse(path)

        assert DEGREE in str(result["name_of_stations"]), (
            f"Degree symbol lost in .bui station names: {result['name_of_stations']!r}"
        )

    def test_mdu_parser_read_file(self, tmp_path: Path):
        """Test `MDUParser._read_file` reads a non-UTF-8 .mdu file.

        Test scenario:
            The low-level MDU line reader returns the file's lines (including a
            comment holding `°` as byte 0xB0) without a decode error. The reader is
            exercised in isolation via `__new__` to avoid the heavy full-model load
            that the constructor performs.
        """
        from hydrolib.tools.extforce_convert.mdu_parser import MDUParser

        content = f"# Deltares MDU in {DEGREE}C\n[model]\n    Program = D-Flow FM\n"
        path = _write_latin1(tmp_path / "test.mdu", content)
        _assert_is_invalid_utf8(path)

        parser = MDUParser.__new__(MDUParser)
        parser.mdu_path = path
        lines = parser._read_file()

        assert any(DEGREE in line for line in lines), f"Degree symbol lost in MDU lines: {lines!r}"

    def test_helper_used_by_ini_parser(self, tmp_path: Path):
        """Test the INI parser routes its read through the fallback helper.

        Test scenario:
            `Parser.parse` must call `open_file_with_fallback_encoding` (not a
            bare `open`/`read_text`), so that every INI-format model file inherits
            the fallback. Wrapping the helper and asserting it is called confirms the
            wiring rather than an incidental UTF-8 read.
        """
        from unittest import mock

        from hydrolib.core.base.parser import open_file_with_fallback_encoding
        from hydrolib.core.dflowfm.ini import parser as ini_parser

        content = "[General]\n    fileVersion = 1.09\n    fileType = test\n"
        path = _write_latin1(tmp_path / "spy.ini", content)

        with mock.patch.object(
            ini_parser,
            "open_file_with_fallback_encoding",
            wraps=open_file_with_fallback_encoding,
        ) as spy:
            ini_parser.Parser.parse(path)

        assert spy.call_count == 1, f"Expected the fallback helper to be called once, got {spy.call_count}"
