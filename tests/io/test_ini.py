from hydrolib.core.io.ini.models import (
    CommentBlock,
    Document,
    Property,
    Section,
)
from hydrolib.core.io.ini.parser import (
    Parser,
    _IntermediateCommentBlock,
    _IntermediateSection,
    ParserConfig,
)
from pydantic import ValidationError
from typing import List, Tuple, Union

import inspect
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


class TestParser:
    @pytest.mark.parametrize(
        "line,expected_result",
        [
            ("", True),
            ("     ", True),
            ("something", False),
            ("       also something", False),
        ],
    )
    def test_is_empty_line(self, line: str, expected_result: bool):
        parser = Parser(ParserConfig())
        assert parser._is_empty_line(line) == expected_result

    @pytest.mark.parametrize(
        "line,config,expected_result",
        [
            ("# some comment", ParserConfig(), True),
            ("       # with whitespace      ", ParserConfig(), True),
            ("#", ParserConfig(), True),
            ("     * yet another comment", ParserConfig(comment_delimeter="*"), True),
            ("# not a comment", ParserConfig(comment_delimeter="*"), False),
            ("", ParserConfig(), False),
            ("     ", ParserConfig(), False),
            ("something", ParserConfig(), False),
            ("       also something", ParserConfig(), False),
            (
                "123 a comment with a weird delimeter ",
                ParserConfig(comment_delimeter="123"),
                True,
            ),
        ],
    )
    def test_is_comment(self, line: str, config: ParserConfig, expected_result: bool):
        parser = Parser(config)
        assert parser._is_comment(line) == expected_result

    @pytest.mark.parametrize(
        "line,expected_result",
        [
            ("[a-header]", True),
            ("[ also header but with whitespace ]", True),
            ("[ # this works, but please don't do that # ]", True),
            ("                 [ prefixed whitespace is acceptable ]     ", True),
            ("[ not closed", False),
            ("  also not closed ]", False),
            ("(not-a-header)", False),
            ("{not-a-header}", False),
            ("", False),
            ("     ", False),
            ("something", False),
            ("       also something", False),
            ("# some comment", False),
        ],
    )
    def test_is_section_header(self, line: str, expected_result: bool):
        parser = Parser(ParserConfig())
        assert parser._is_section_header(line) == expected_result

    @pytest.mark.parametrize(
        "line,config,expected_result",
        [
            ("key=value", ParserConfig(allow_only_keywords=False), True),
            ("    key = value   ", ParserConfig(allow_only_keywords=False), True),
            ("key=value#Comment", ParserConfig(allow_only_keywords=False), True),
            (
                "    key = value # Comment",
                ParserConfig(allow_only_keywords=False),
                True,
            ),
            (
                "    key = value with multiple # Comment",
                ParserConfig(allow_only_keywords=False),
                True,
            ),
            (
                "    key with spaces = value # Comment",
                ParserConfig(allow_only_keywords=False),
                True,
            ),
            ("key =   ", ParserConfig(allow_only_keywords=False), True),
            ("key", ParserConfig(allow_only_keywords=True), True),
            ("key", ParserConfig(allow_only_keywords=False), False),
            ("key", ParserConfig(allow_only_keywords=False), False),
            ("key # comment", ParserConfig(allow_only_keywords=False), False),
        ],
    )
    def test_is_property(self, line: str, config: ParserConfig, expected_result: bool):
        parser = Parser(config)
        assert parser._is_property(line) == expected_result

    @pytest.mark.parametrize(
        "line,config,expected_result",
        [
            (
                "1.0 2.0 3.0 4.0",
                ParserConfig(allow_only_keywords=False, parse_datablocks=True),
                True,
            ),
            (
                "1.0 2.0 3.0 4.0",
                ParserConfig(allow_only_keywords=True, parse_datablocks=False),
                False,
            ),
            (
                "1.0",
                ParserConfig(allow_only_keywords=False, parse_datablocks=True),
                True,
            ),
            (
                "1.0",
                ParserConfig(allow_only_keywords=True, parse_datablocks=False),
                False,
            ),
            (
                "val1 val2",
                ParserConfig(allow_only_keywords=False, parse_datablocks=True),
                True,
            ),
            (
                "val1 val2",
                ParserConfig(allow_only_keywords=True, parse_datablocks=False),
                False,
            ),
            (
                "val",
                ParserConfig(allow_only_keywords=False, parse_datablocks=True),
                True,
            ),
            (
                "val",
                ParserConfig(allow_only_keywords=True, parse_datablocks=False),
                False,
            ),
        ],
    )
    def test_is_datarow(self, line: str, config: ParserConfig, expected_result: bool):
        parser = Parser(config)
        assert parser._is_datarow(line) == expected_result

    def test_feed_comment_at_the_beginning_of_the_document_gets_added_to_the_header(
        self,
    ):
        parser = Parser(config=ParserConfig())

        comment_content = " some comment"

        parser.feed_line(f"#{comment_content}")
        result = parser.finalize()

        expected_header_comment = [
            CommentBlock(start_line=0, end_line=0, lines=[comment_content])
        ]

        assert result.header_comment == expected_header_comment
        assert result.sections == []

    def test_feed_multiple_comment_blocks_at_the_beginning_of_the_document_gets_added_to_the_header(
        self,
    ):
        parser = Parser(config=ParserConfig())

        comment_blocks = list(
            [f"first comment in block {v}", f"second comment in block {v}"]
            for v in range(5)
        )

        for comment_block in comment_blocks:
            for line in comment_block:
                parser.feed_line(f"#{line}")

            parser.feed_line("")

        result = parser.finalize()

        expected_header_comment = list(
            CommentBlock(start_line=v * 3, end_line=v * 3 + 1, lines=comment_blocks[v])
            for v in range(5)
        )

        assert result.header_comment == expected_header_comment
        assert result.sections == []

    def test_feed_multiple_empty_lines_adds_header_correctly(
        self,
    ):
        parser = Parser(config=ParserConfig())

        comment_blocks = list(
            [f"line 1 in block {v}", f"line 2 in block {v}"] for v in range(3)
        )

        for comment_block in comment_blocks:
            for line in comment_block:
                parser.feed_line(f"#{line}")

            parser.feed_line("")
            parser.feed_line("")
            parser.feed_line("")

        result = parser.finalize()

        expected_header_comment = list(
            CommentBlock(start_line=v * 5, end_line=v * 5 + 1, lines=comment_blocks[v])
            for v in range(3)
        )

        assert result.header_comment == expected_header_comment
        assert result.sections == []

    def test_feed_comment_at_the_beginning_of_the_document_with_section_gets_added_to_the_header(
        self,
    ):
        parser = Parser(config=ParserConfig())

        comment_content = " some comment"

        parser.feed_line(f"#{comment_content}")
        parser.feed_line(f"[header]")
        result = parser.finalize()

        expected_header_comment = [
            CommentBlock(start_line=0, end_line=0, lines=[comment_content])
        ]

        assert result.header_comment == expected_header_comment
        assert len(result.sections) == 1

    def test_section_is_added_correctly(self):
        parser = Parser(config=ParserConfig())

        header = "header"
        properties = list(
            Property(
                key=f"key-{v}", value=f"value_{v}", comment=f"comment_{v}", line=v + 2
            )
            for v in range(5)
        )

        parser.feed_line("")
        parser.feed_line(f"    [{header}]")

        for p in properties:
            parser.feed_line(f"        {p.key} = {p.value} #{p.comment}")

        result = parser.finalize()

        expected_result = Document(
            sections=[
                Section(
                    header=header,
                    content=properties,
                    datablock=None,
                    start_line=1,
                    end_line=7,
                )
            ]
        )

        assert result == expected_result

    def test_section_with_comments_is_added_correctly(self):
        parser = Parser(config=ParserConfig())

        input_lines = inspect.cleandoc(
            """
            [header]
                # some comment
                # consisting of two lines
                key         = value                 # with a comment
                another-key = another-value
                # inbetween comment
                last-key    = last value            # inline comment
                # last comment
            """
        )

        for line in input_lines.splitlines():
            parser.feed_line(line)
        result = parser.finalize()

        expected_result = Document(
            sections=[
                Section(
                    header="header",
                    content=[
                        CommentBlock(
                            start_line=1,
                            end_line=2,
                            lines=[" some comment", " consisting of two lines"],
                        ),
                        Property(
                            key="key", value="value", comment=" with a comment", line=3
                        ),
                        Property(
                            key="another-key",
                            value="another-value",
                            comment=None,
                            line=4,
                        ),
                        CommentBlock(
                            start_line=5, end_line=5, lines=[" inbetween comment"]
                        ),
                        Property(
                            key="last-key",
                            value="last value",
                            comment=" inline comment",
                            line=6,
                        ),
                        CommentBlock(start_line=7, end_line=7, lines=[" last comment"]),
                    ],
                    datablock=None,
                    start_line=0,
                    end_line=8,
                )
            ]
        )

        assert result == expected_result

    def test_section_with_datablock_is_added_correctly(self):
        parser = Parser(config=ParserConfig(parse_datablocks=True))

        input_lines = inspect.cleandoc(
            """
            [header]
                # some comment
                # consisting of two lines
                key         = value
                some-key    = some-value
                # inbetween comment
                last-key    = last value
                # last comment
                     1.0  2.0  3.0
                     4.0  5.0  6.0
                     7.0  8.0  9.0
                    10.0 11.0 12.0
            """
        )

        for line in input_lines.splitlines():
            parser.feed_line(line)
        result = parser.finalize()

        expected_result = Document(
            sections=[
                Section(
                    header="header",
                    content=[
                        CommentBlock(
                            start_line=1,
                            end_line=2,
                            lines=[" some comment", " consisting of two lines"],
                        ),
                        Property(key="key", value="value", comment=None, line=3),
                        Property(
                            key="some-key",
                            value="some-value",
                            comment=None,
                            line=4,
                        ),
                        CommentBlock(
                            start_line=5, end_line=5, lines=[" inbetween comment"]
                        ),
                        Property(
                            key="last-key",
                            value="last value",
                            comment=None,
                            line=6,
                        ),
                        CommentBlock(start_line=7, end_line=7, lines=[" last comment"]),
                    ],
                    datablock=[
                        ["1.0", "2.0", "3.0"],
                        ["4.0", "5.0", "6.0"],
                        ["7.0", "8.0", "9.0"],
                        ["10.0", "11.0", "12.0"],
                    ],
                    start_line=0,
                    end_line=12,
                )
            ]
        )

        assert result == expected_result

    def test_multiple_sections_are_added_correctly(self):
        parser = Parser(config=ParserConfig())

        input_lines = inspect.cleandoc(
            """
            [header]
                # some comment
                # consisting of two lines
                key         = value                 # with a comment
                another-key = another-value
                # inbetween comment
                last-key    = last value            # inline comment
                # last comment


            [different-header]
                key1 = value1           # comment1
                key2 = value2           # comment2
                key3 = value3           # comment3
            """
        )

        for line in input_lines.splitlines():
            parser.feed_line(line)
        result = parser.finalize()

        expected_result = Document(
            sections=[
                Section(
                    header="header",
                    content=[
                        CommentBlock(
                            start_line=1,
                            end_line=2,
                            lines=[" some comment", " consisting of two lines"],
                        ),
                        Property(
                            key="key", value="value", comment=" with a comment", line=3
                        ),
                        Property(
                            key="another-key",
                            value="another-value",
                            comment=None,
                            line=4,
                        ),
                        CommentBlock(
                            start_line=5, end_line=5, lines=[" inbetween comment"]
                        ),
                        Property(
                            key="last-key",
                            value="last value",
                            comment=" inline comment",
                            line=6,
                        ),
                        CommentBlock(start_line=7, end_line=7, lines=[" last comment"]),
                    ],
                    datablock=None,
                    start_line=0,
                    end_line=10,
                ),
                Section(
                    header="different-header",
                    content=[
                        Property(
                            key="key1", value="value1", comment=" comment1", line=11
                        ),
                        Property(
                            key="key2", value="value2", comment=" comment2", line=12
                        ),
                        Property(
                            key="key3", value="value3", comment=" comment3", line=13
                        ),
                    ],
                    datablock=None,
                    start_line=10,
                    end_line=14,
                ),
            ]
        )

        assert result == expected_result

    def test_complex_document_is_added_correctly(self):
        input_lines = inspect.cleandoc(
            """
            # this is a very contrived example
            # with a header

            # consisting of multiple blocks
            # with datablocks


            [header]
                # some comment
                # consisting of two lines
                key         = value                 # with a comment
                another-key = another-value
                # inbetween comment
                last-key    = last value            # inline comment
                # last comment
                     1.0  2.0  3.0
                     4.0  5.0  6.0


            [different-header]
                key1 = value1           # comment1
                key2 = value2           # comment2
                key3 = value3           # comment3
                # some comment1
                # some comment2
                     7.0  8.0  9.0
                    10.0 11.0 12.0
            """
        )

        parser = Parser(config=ParserConfig(parse_datablocks=True))
        for line in input_lines.splitlines():
            parser.feed_line(line)
        result = parser.finalize()

        expected_result = Document(
            header_comment=[
                CommentBlock(
                    start_line=0,
                    end_line=1,
                    lines=[" this is a very contrived example", " with a header"],
                ),
                CommentBlock(
                    start_line=3,
                    end_line=4,
                    lines=[" consisting of multiple blocks", " with datablocks"],
                ),
            ],
            sections=[
                Section(
                    header="header",
                    content=[
                        CommentBlock(
                            start_line=8,
                            end_line=9,
                            lines=[" some comment", " consisting of two lines"],
                        ),
                        Property(
                            key="key", value="value", comment=" with a comment", line=10
                        ),
                        Property(
                            key="another-key",
                            value="another-value",
                            comment=None,
                            line=11,
                        ),
                        CommentBlock(
                            start_line=12, end_line=12, lines=[" inbetween comment"]
                        ),
                        Property(
                            key="last-key",
                            value="last value",
                            comment=" inline comment",
                            line=13,
                        ),
                        CommentBlock(
                            start_line=14, end_line=14, lines=[" last comment"]
                        ),
                    ],
                    datablock=[
                        ["1.0", "2.0", "3.0"],
                        ["4.0", "5.0", "6.0"],
                    ],
                    start_line=7,
                    end_line=19,
                ),
                Section(
                    header="different-header",
                    content=[
                        Property(
                            key="key1", value="value1", comment=" comment1", line=20
                        ),
                        Property(
                            key="key2", value="value2", comment=" comment2", line=21
                        ),
                        Property(
                            key="key3", value="value3", comment=" comment3", line=22
                        ),
                        CommentBlock(
                            start_line=23,
                            end_line=24,
                            lines=[" some comment1", " some comment2"],
                        ),
                    ],
                    datablock=[
                        ["7.0", "8.0", "9.0"],
                        ["10.0", "11.0", "12.0"],
                    ],
                    start_line=19,
                    end_line=27,
                ),
            ],
        )

        assert result == expected_result
