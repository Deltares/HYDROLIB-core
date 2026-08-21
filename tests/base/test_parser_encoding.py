"""Tests for hydrolib.core.base.parser.open_file_with_fallback_encoding."""


from pathlib import Path

from hydrolib.core.base.parser import open_file_with_fallback_encoding


class TestOpenFileWithFallbackEncoding:
    """Tests for the open_file_with_fallback_encoding helper."""

    def test_reads_utf8_file(self, tmp_path: Path):
        """Test that a valid UTF-8 file is read correctly.

        Test scenario:
            A file written as UTF-8 with ASCII content should be read without
            falling back to Latin-1.
        """
        f = tmp_path / "test.txt"
        f.write_text("hello world\n", encoding="utf-8")
        result = open_file_with_fallback_encoding(f)
        assert result == "hello world\n", f"Expected 'hello world\\n', got {result!r}"

    def test_reads_utf8_file_with_unicode(self, tmp_path: Path):
        """Test that a valid UTF-8 file with multi-byte characters is read correctly.

        Test scenario:
            A file containing multi-byte UTF-8 characters (e.g. emoji, accents)
            should be read without fallback.
        """
        f = tmp_path / "test.txt"
        content = "température = 15°C\n"
        f.write_text(content, encoding="utf-8")
        result = open_file_with_fallback_encoding(f)
        assert result == content, f"Expected {content!r}, got {result!r}"

    def test_falls_back_to_latin1_for_non_utf8_bytes(self, tmp_path: Path):
        """Test that a file with non-UTF-8 bytes is read via Latin-1 fallback.

        Test scenario:
            A file containing the byte 0xB0 (degree symbol in Latin-1) that is
            NOT valid UTF-8 on its own should be decoded via the Latin-1 fallback
            path.
        """
        f = tmp_path / "test.txt"
        # Write raw bytes that are valid Latin-1 but invalid UTF-8:
        # 0xB0 is the degree symbol in Latin-1, but a bare 0xB0 is invalid in UTF-8
        content_bytes = b"temperature = 15\xb0C\n"
        f.write_bytes(content_bytes)

        result = open_file_with_fallback_encoding(f)
        assert result == "temperature = 15°C\n", f"Expected Latin-1 decoded content, got {result!r}"
        assert "°" in result, f"Expected degree symbol in result, got {result!r}"

    def test_falls_back_to_latin1_for_windows1252_content(self, tmp_path: Path):
        """Test that Windows-1252 encoded files are read via Latin-1 fallback.

        Test scenario:
            Model files from older Windows systems may use Windows-1252 encoding.
            Bytes like 0xE9 (é in Latin-1/Win-1252) that form invalid UTF-8
            sequences should be decoded via fallback.
        """
        f = tmp_path / "test.txt"
        # 0xE9 is 'é' in Latin-1, but bare 0xE9 is invalid UTF-8
        content_bytes = b"R\xe9sum\xe9 du mod\xe8le\n"
        f.write_bytes(content_bytes)

        result = open_file_with_fallback_encoding(f)
        assert result == "Résumé du modèle\n", f"Got {result!r}"

    def test_empty_file(self, tmp_path: Path):
        """Test that an empty file returns an empty string.

        Test scenario:
            An empty file should return '' without raising.
        """
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        result = open_file_with_fallback_encoding(f)
        assert result == "", f"Expected empty string, got {result!r}"

