from hydrolib.core.io.ini.models import (
    CommentBlock,
)
from hydrolib.core.io.ini.parser import (
    _IntermediateCommentBlock,
    _IntermediateSection,
    ParserConfig,
)
from pydantic import ValidationError

import pytest


class TestParserConfig:
    def test_parser_config_does_not_allow_allow_only_keywords_and_parse_data_blocks_to_be_true(
        self,
    ):
        with pytest.raises(ValidationError):
            _ = ParserConfig(allow_only_keywords=True, parse_datablocks=True)


class TestIntermediateCommentBlock:
    def test_finalize_produces_correct_comment_block(self):
        start_line = 20
        intermediate_comment_block = _IntermediateCommentBlock(start_line=start_line)

        comment_lines = ["1", "2", "3"]

        for l in comment_lines:
            intermediate_comment_block.add_comment_line(l)

        result = intermediate_comment_block.finalize()
        expected_comment_block = CommentBlock(
            start_line=start_line,
            end_line=start_line + len(comment_lines) - 1,
            lines=comment_lines,
        )

        assert result == expected_comment_block
