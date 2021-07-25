from hydrolib.core.io.ini.models import (
    CommentBlock,
    Property,
    Section,
)
from hydrolib.core.io.ini.parser import (
    _IntermediateCommentBlock,
    _IntermediateSection,
    ParserConfig,
)
from pydantic import ValidationError
from typing import List, Union

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


class TestIntermediateSection:
    def test_add_property_and_finalize_has_expected_results(self):
        header = "some-header"
        start_line = 50
        intermediate_section = _IntermediateSection(
            header=header, start_line=start_line
        )

        properties = list(
            Property(line=50 + i, key=f"key{i}", value=f"value{i}", comment=None)
            for i in range(5)
        )

        for prop in properties:
            intermediate_section.add_property(prop)

        end_line = 54
        result = intermediate_section.finalize(end_line)

        expected_section = Section(
            header=header,
            start_line=start_line,
            end_line=end_line,
            content=properties,
            datablock=None,
        )

        assert result == expected_section

    def test_add_comment_and_finalize_has_expected_results(self):
        header = "some-header"
        start_line = 50
        intermediate_section = _IntermediateSection(
            header=header, start_line=start_line
        )

        comments = list((f"Comment {v}", 50 + v) for v in range(5))

        for comment, line in comments:
            intermediate_section.add_comment(comment, line)

        end_line = 54
        result = intermediate_section.finalize(end_line)

        expected_section = Section(
            header=header,
            start_line=start_line,
            end_line=end_line,
            content=[
                CommentBlock(
                    start_line=50, end_line=54, lines=list(x[0] for x in comments)
                )
            ],
            datablock=None,
        )

        assert result == expected_section

    def test_add_datarow_and_finalize_has_expected_results(self):
        header = "some-header"
        start_line = 50
        intermediate_section = _IntermediateSection(
            header=header, start_line=start_line
        )

        data_rows = list(
            [f"{1 + v * 5}", f"{2 + v * 5}", f"{3 + v * 5}", f"{4 + v * 5}"]
            for v in range(5)
        )

        for row in data_rows:
            intermediate_section.add_datarow(row)

        end_line = 54
        result = intermediate_section.finalize(end_line)

        expected_section = Section(
            header=header,
            start_line=start_line,
            end_line=end_line,
            content=[],
            datablock=data_rows,
        )

        assert result == expected_section

    def test_add_multiple_components_and_finalize_has_expected_results(self):
        # Setup values
        header = "some-header"
        start_line = 50
        end_line = 74

        properties = list(
            Property(line=50 + i, key=f"key{i}", value=f"value{i}", comment=None)
            for i in range(10)
        )

        comment_blocks = [
            CommentBlock(start_line=50, end_line=51, lines=["a", "b"]),
            CommentBlock(start_line=57, end_line=59, lines=["c", "d", "e"]),
            CommentBlock(start_line=65, end_line=68, lines=["1", "3", "4", "6"]),
        ]

        datarows = list(
            [f"{1 + v * 5}", f"{2 + v * 5}", f"{3 + v * 5}", f"{4 + v * 5}"]
            for v in range(5)
        )

        intermediate_section = _IntermediateSection(
            header=header, start_line=start_line
        )

        # Add Content and finalise
        for comment, line in zip(
            comment_blocks[0].lines, range(len(comment_blocks[0].lines))
        ):
            intermediate_section.add_comment(
                comment, line + comment_blocks[0].start_line
            )

        for prop in properties[:5]:
            intermediate_section.add_property(prop)

        for comment, line in zip(
            comment_blocks[1].lines, range(len(comment_blocks[1].lines))
        ):
            intermediate_section.add_comment(
                comment, line + comment_blocks[1].start_line
            )

        for prop in properties[5:]:
            intermediate_section.add_property(prop)

        for comment, line in zip(
            comment_blocks[2].lines, range(len(comment_blocks[2].lines))
        ):
            intermediate_section.add_comment(
                comment, line + comment_blocks[2].start_line
            )

        for row in datarows:
            intermediate_section.add_datarow(row)

        result = intermediate_section.finalize(end_line)

        expected_content: List[Union[CommentBlock, Property]] = [comment_blocks[0]] + properties[:5] + [comment_blocks[1]] + properties[5:] + [comment_blocks[2]]  # type: ignore

        expected_section = Section(
            header=header,
            start_line=start_line,
            end_line=end_line,
            content=expected_content,
            datablock=datarows,
        )

        assert result == expected_section
