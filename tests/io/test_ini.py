from itertools import chain
from hydrolib.core.io.ini.serializer import Serializer, SerializerConfig, _Lengths
import inspect
from typing import Iterable, List, Optional, Sequence, Tuple, Union

import pytest
from pydantic import ValidationError

from hydrolib.core.io.ini.models import (
    CommentBlock,
    Document,
    IniBasedModel,
    Property,
    Section,
)
from hydrolib.core.io.ini.parser import (
    Parser,
    ParserConfig,
    _IntermediateCommentBlock,
    _IntermediateSection,
)


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
            ("     * yet another comment", ParserConfig(comment_delimiter="*"), True),
            ("# not a comment", ParserConfig(comment_delimiter="*"), False),
            ("", ParserConfig(), False),
            ("     ", ParserConfig(), False),
            ("something", ParserConfig(), False),
            ("       also something", ParserConfig(), False),
            (
                "123 a comment with a weird delimiter ",
                ParserConfig(comment_delimiter="123"),
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

        comment_content = "some comment"

        parser.feed_line(f"# {comment_content}")
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

        comment_content = "header comment"

        parser.feed_line(f"# {comment_content}")
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
                # comment in a section
                # starting with two lines
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
                            lines=["comment in a section", "starting with two lines"],
                        ),
                        Property(
                            key="key", value="value", comment="with a comment", line=3
                        ),
                        Property(
                            key="another-key",
                            value="another-value",
                            comment=None,
                            line=4,
                        ),
                        CommentBlock(
                            start_line=5, end_line=5, lines=["inbetween comment"]
                        ),
                        Property(
                            key="last-key",
                            value="last value",
                            comment="inline comment",
                            line=6,
                        ),
                        CommentBlock(start_line=7, end_line=7, lines=["last comment"]),
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
                            lines=["some comment", "consisting of two lines"],
                        ),
                        Property(key="key", value="value", comment=None, line=3),
                        Property(
                            key="some-key",
                            value="some-value",
                            comment=None,
                            line=4,
                        ),
                        CommentBlock(
                            start_line=5, end_line=5, lines=["inbetween comment"]
                        ),
                        Property(
                            key="last-key",
                            value="last value",
                            comment=None,
                            line=6,
                        ),
                        CommentBlock(start_line=7, end_line=7, lines=["last comment"]),
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

        properties = list(
            Property(
                key=f"key-{v}", value=f"value_{v}", comment=f"comment_{v}", line=v + 1
            )
            for v in range(12)
        )

        parser.feed_line(f"    [header1]")
        for p in properties[:6]:
            parser.feed_line(f"        {p.key} = {p.value} #{p.comment}")
        parser.feed_line("")

        parser.feed_line(f"    [header2]")
        for p in properties[6:]:
            parser.feed_line(f"        {p.key} = {p.value} #{p.comment}")
            p.line += 2
        parser.feed_line("")

        result = parser.finalize()

        expected_result = Document(
            sections=[
                Section(
                    header="header1",
                    content=properties[:6],
                    datablock=None,
                    start_line=0,
                    end_line=8,
                ),
                Section(
                    header="header2",
                    content=properties[6:],
                    datablock=None,
                    start_line=8,
                    end_line=16,
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
                    lines=["this is a very contrived example", "with a header"],
                ),
                CommentBlock(
                    start_line=3,
                    end_line=4,
                    lines=["consisting of multiple blocks", "with datablocks"],
                ),
            ],
            sections=[
                Section(
                    header="header",
                    content=[
                        CommentBlock(
                            start_line=8,
                            end_line=9,
                            lines=["some comment", "consisting of two lines"],
                        ),
                        Property(
                            key="key", value="value", comment="with a comment", line=10
                        ),
                        Property(
                            key="another-key",
                            value="another-value",
                            comment=None,
                            line=11,
                        ),
                        CommentBlock(
                            start_line=12, end_line=12, lines=["inbetween comment"]
                        ),
                        Property(
                            key="last-key",
                            value="last value",
                            comment="inline comment",
                            line=13,
                        ),
                        CommentBlock(
                            start_line=14, end_line=14, lines=["last comment"]
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
                            key="key1", value="value1", comment="comment1", line=20
                        ),
                        Property(
                            key="key2", value="value2", comment="comment2", line=21
                        ),
                        Property(
                            key="key3", value="value3", comment="comment3", line=22
                        ),
                        CommentBlock(
                            start_line=23,
                            end_line=24,
                            lines=["some comment1", "some comment2"],
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


class TestIniBasedModel:
    class MissingCommentsModel(IniBasedModel):
        @classmethod
        def _supports_comments(cls):
            return True

        comments: Optional[IniBasedModel.Comments] = None

    def test_ini_based_model_which_supports_comments_should_have_comments(self):
        with pytest.raises(ValidationError):
            _ = TestIniBasedModel.MissingCommentsModel()

    class UnsupportedCommentsModel(IniBasedModel):
        @classmethod
        def _supports_comments(cls):
            return False

        comments = IniBasedModel.Comments()

    def test_ini_based_model_which_does_not_support_comments_should_not_have_comments(
        self,
    ):
        with pytest.raises(ValidationError):
            _ = TestIniBasedModel.UnsupportedCommentsModel()


class TestSerializerConfig:
    def test_total_property_indent_expected_result(self):
        config = SerializerConfig(section_indent=5, property_indent=3)
        assert config.total_property_indent == 8

    def test_total_datablock_indent_expected_result(self):
        config = SerializerConfig(section_indent=3, datablock_indent=10)
        assert config.total_datablock_indent == 13


class TestLengths:
    @pytest.mark.parametrize(
        "section,expected_result",
        [
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[],
                    datablock=None,
                ),
                _Lengths(
                    max_key_length=0,
                    max_value_length=0,
                    max_datablock_element_length=None,
                ),
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        CommentBlock(start_line=-1, end_line=-1, lines=[]),
                    ],
                    datablock=None,
                ),
                _Lengths(
                    max_key_length=0,
                    max_value_length=0,
                    max_datablock_element_length=None,
                ),
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        CommentBlock(
                            start_line=-1,
                            end_line=-1,
                            lines=["one", "two", "three", "four"],
                        ),
                    ],
                    datablock=None,
                ),
                _Lengths(
                    max_key_length=0,
                    max_value_length=0,
                    max_datablock_element_length=None,
                ),
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        Property(line=-1, key="key", value="value", comment="comment"),
                    ],
                    datablock=None,
                ),
                _Lengths(
                    max_key_length=3,
                    max_value_length=5,
                    max_datablock_element_length=None,
                ),
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        Property(line=-1, key="key", value="value", comment="comment"),
                        Property(line=-1, key="123", value="12345", comment="comment"),
                    ],
                    datablock=None,
                ),
                _Lengths(
                    max_key_length=3,
                    max_value_length=5,
                    max_datablock_element_length=None,
                ),
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        Property(line=-1, key="key", value="value", comment="comment"),
                        Property(
                            line=-1, key="long-key", value="value", comment="comment"
                        ),
                    ],
                    datablock=None,
                ),
                _Lengths(
                    max_key_length=8,
                    max_value_length=5,
                    max_datablock_element_length=None,
                ),
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        Property(
                            line=-1, key="key", value="long-value", comment="comment"
                        ),
                        Property(line=-1, key="key", value="value", comment="comment"),
                    ],
                    datablock=None,
                ),
                _Lengths(
                    max_key_length=3,
                    max_value_length=10,
                    max_datablock_element_length=None,
                ),
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        CommentBlock(
                            start_line=-1,
                            end_line=-1,
                            lines=["one", "two", "three", "four"],
                        ),
                        Property(line=-1, key="key", value="value", comment="comment"),
                        CommentBlock(
                            start_line=-1,
                            end_line=-1,
                            lines=["five", "six", "seven", "eight"],
                        ),
                    ],
                    datablock=None,
                ),
                _Lengths(
                    max_key_length=3,
                    max_value_length=5,
                    max_datablock_element_length=None,
                ),
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        Property(line=-1, key="key", value="value", comment="comment"),
                        Property(line=-1, key="long-key", value="value", comment=None),
                    ],
                    datablock=None,
                ),
                _Lengths(
                    max_key_length=8,
                    max_value_length=5,
                    max_datablock_element_length=None,
                ),
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        Property(line=-1, key="long-key", value="value", comment=None),
                    ],
                    datablock=None,
                ),
                _Lengths(
                    max_key_length=8,
                    max_value_length=5,
                    max_datablock_element_length=None,
                ),
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        Property(line=-1, key="long-key", value=None, comment=None),
                    ],
                    datablock=None,
                ),
                _Lengths(
                    max_key_length=8,
                    max_value_length=0,
                    max_datablock_element_length=None,
                ),
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[],
                    datablock=[["1.23"]],
                ),
                _Lengths(
                    max_key_length=0,
                    max_value_length=0,
                    max_datablock_element_length=(4,),
                ),
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[],
                    datablock=[["1.23", "1.2345", "1.234567"]],
                ),
                _Lengths(
                    max_key_length=0,
                    max_value_length=0,
                    max_datablock_element_length=(4, 6, 8),
                ),
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[],
                    datablock=[
                        ["1.23", "1.0", "1.234567"],
                        ["0.0", "1.2345", "1.23456789"],
                        ["0.0", "0.0", "0.0"],
                    ],
                ),
                _Lengths(
                    max_key_length=0,
                    max_value_length=0,
                    max_datablock_element_length=(4, 6, 10),
                ),
            ),
        ],
    )
    def test_from_section_expected_results(
        self, section: Section, expected_result: _Lengths
    ):
        result = _Lengths.from_section(section)
        assert result == expected_result


class TestSerializer:
    @pytest.mark.parametrize(
        "iterable,expected_result",
        [
            ([], []),
            (
                [
                    "one",
                ],
                ["one", ""],
            ),
            (
                [
                    "one",
                    "two",
                    "three",
                ],
                [
                    "one",
                    "",
                    "two",
                    "",
                    "three",
                    "",
                ],
            ),
        ],
    )
    def test_interweave_empty_lines_to_iterable_str_should_interweave_correctly(
        self, iterable: Iterable[str], expected_result: List[str]
    ):
        result = list(Serializer._interweave(iterable, ""))

        assert result == expected_result

    @pytest.mark.parametrize(
        "iterable,expected_result",
        [
            ([], []),
            (
                [
                    ["one"],
                ],
                ["one", ""],
            ),
            (
                [
                    [
                        "one",
                        "two",
                    ],
                    [
                        "three",
                        "four",
                    ],
                    [
                        "five",
                        "six",
                    ],
                ],
                [
                    "one",
                    "two",
                    "",
                    "three",
                    "four",
                    "",
                    "five",
                    "six",
                    "",
                ],
            ),
        ],
    )
    def test_interweave_empty_lines_to_iterable_iterable_str_should_interweave_correctly(
        self, iterable: Iterable[Iterable[str]], expected_result: List[str]
    ):
        result = list(chain.from_iterable(Serializer._interweave(iterable, [""])))
        assert result == expected_result

    @pytest.mark.parametrize(
        "comment_block,offset,config,expected_result",
        [
            (
                CommentBlock(start_line=-1, end_line=-1, lines=[]),
                0,
                SerializerConfig(),
                [],
            ),
            (
                CommentBlock(start_line=-1, end_line=-1, lines=["angry badger noises"]),
                0,
                SerializerConfig(),
                ["# angry badger noises"],
            ),
            (
                CommentBlock(start_line=-1, end_line=-1, lines=["comment"]),
                4,
                SerializerConfig(),
                ["    # comment"],
            ),
            (
                CommentBlock(start_line=-1, end_line=-1, lines=["one", "two", "three"]),
                4,
                SerializerConfig(),
                ["    # one", "    # two", "    # three"],
            ),
            (
                CommentBlock(start_line=-1, end_line=-1, lines=["comment"]),
                6,
                SerializerConfig(comment_delimiter="*"),
                ["      * comment"],
            ),
        ],
    )
    def test_serialize_comment_block(
        self,
        comment_block: CommentBlock,
        offset: int,
        config: SerializerConfig,
        expected_result: List[str],
    ):
        serializer = Serializer(config=config)

        result = list(serializer._serialize_comment_block(comment_block, offset))
        assert result == expected_result

    @pytest.mark.parametrize(
        "comment_header,config,expected_result",
        [
            (
                [],
                SerializerConfig(),
                [],
            ),
            (
                [CommentBlock(start_line=-1, end_line=-1, lines=[])],
                SerializerConfig(),
                [""],
            ),
            (
                [
                    CommentBlock(
                        start_line=-1, end_line=-1, lines=["angry badger noises"]
                    )
                ],
                SerializerConfig(),
                ["# angry badger noises", ""],
            ),
            (
                [
                    CommentBlock(
                        start_line=-1, end_line=-1, lines=["one", "two", "three"]
                    )
                ],
                SerializerConfig(),
                ["# one", "# two", "# three", ""],
            ),
            (
                [CommentBlock(start_line=-1, end_line=-1, lines=["comment"])],
                SerializerConfig(comment_delimiter="*"),
                ["* comment", ""],
            ),
            (
                [
                    CommentBlock(
                        start_line=-1, end_line=-1, lines=["one", "two", "three"]
                    ),
                    CommentBlock(
                        start_line=-1, end_line=-1, lines=["four", "five", "six"]
                    ),
                ],
                SerializerConfig(),
                [
                    "# one",
                    "# two",
                    "# three",
                    "",
                    "# four",
                    "# five",
                    "# six",
                    "",
                ],
            ),
        ],
    )
    def test_serialize_comment_header(
        self,
        comment_header: List[CommentBlock],
        config: SerializerConfig,
        expected_result: List[str],
    ):
        serializer = Serializer(config=config)

        result = list(serializer._serialize_comment_header(comment_header))
        assert result == expected_result

    @pytest.mark.parametrize(
        "header,config,expected_result",
        [
            ("header", SerializerConfig(section_indent=0), "[header]"),
            ("header", SerializerConfig(section_indent=4), "    [header]"),
            ("with spaces", SerializerConfig(section_indent=0), "[with spaces]"),
        ],
    )
    def test_serialize_section_header(
        self, header: str, config: SerializerConfig, expected_result: str
    ):
        serializer = Serializer(config=config)

        result = list(serializer._serialize_section_header(header))
        assert result == [expected_result]

    @pytest.mark.parametrize(
        "property,lengths,config,expected_result",
        [
            (
                Property(line=-1, key="key", value="value", comment="comment"),
                _Lengths(max_key_length=3, max_value_length=5),
                SerializerConfig(section_indent=0, property_indent=0),
                "key = value # comment",
            ),
            (
                Property(line=-1, key="key", value="value", comment="comment"),
                _Lengths(max_key_length=3, max_value_length=5),
                SerializerConfig(section_indent=0, property_indent=4),
                "    key = value # comment",
            ),
            (
                Property(line=-1, key="key", value="value", comment="comment"),
                _Lengths(max_key_length=3, max_value_length=5),
                SerializerConfig(section_indent=4, property_indent=0),
                "    key = value # comment",
            ),
            (
                Property(line=-1, key="key", value="value", comment="comment"),
                _Lengths(max_key_length=3, max_value_length=5),
                SerializerConfig(section_indent=4, property_indent=4),
                "        key = value # comment",
            ),
            (
                Property(line=-1, key="key", value="value", comment=None),
                _Lengths(max_key_length=3, max_value_length=5),
                SerializerConfig(section_indent=0, property_indent=0),
                "key = value",
            ),
            (
                Property(line=-1, key="key", value=None, comment=None),
                _Lengths(max_key_length=3, max_value_length=0),
                SerializerConfig(section_indent=0, property_indent=0),
                "key =",
            ),
            (
                Property(line=-1, key="key", value=None, comment="comment"),
                _Lengths(max_key_length=3, max_value_length=5),
                SerializerConfig(section_indent=0, property_indent=0),
                "key =       # comment",
            ),
            (
                Property(line=-1, key="key", value="value", comment="comment"),
                _Lengths(max_key_length=6, max_value_length=5),
                SerializerConfig(section_indent=0, property_indent=0),
                "key    = value # comment",
            ),
            (
                Property(line=-1, key="key", value="value", comment="comment"),
                _Lengths(max_key_length=6, max_value_length=12),
                SerializerConfig(section_indent=0, property_indent=0),
                "key    = value        # comment",
            ),
            (
                Property(line=-1, key="key", value="value", comment="comment"),
                _Lengths(max_key_length=6, max_value_length=12),
                SerializerConfig(section_indent=2, property_indent=4),
                "      key    = value        # comment",
            ),
        ],
    )
    def test_serialize_property(
        self,
        property: Property,
        lengths: _Lengths,
        config: SerializerConfig,
        expected_result: str,
    ):
        serializer = Serializer(config=config)

        result = list(serializer._serialize_property(property, lengths))
        assert result == [expected_result]

    @pytest.mark.parametrize(
        "content,lengths,config,expected_result",
        [
            (
                [],
                _Lengths(max_key_length=0, max_value_length=0),
                SerializerConfig(section_indent=0, property_indent=0),
                [],
            ),
            (
                [Property(line=-1, key="key", value="value", comment="comment")],
                _Lengths(max_key_length=3, max_value_length=5),
                SerializerConfig(section_indent=0, property_indent=0),
                ["key = value # comment"],
            ),
            (
                [
                    CommentBlock(
                        start_line=-1, end_line=-1, lines=["angry badger noises"]
                    )
                ],
                _Lengths(max_key_length=3, max_value_length=5),
                SerializerConfig(section_indent=0, property_indent=0),
                ["# angry badger noises"],
            ),
            (
                [
                    CommentBlock(
                        start_line=-1, end_line=-1, lines=["comment 1", "comment 2"]
                    )
                ],
                _Lengths(max_key_length=3, max_value_length=5),
                SerializerConfig(section_indent=0, property_indent=4),
                ["    # comment 1", "    # comment 2"],
            ),
            (
                [
                    Property(line=-1, key="key", value="value", comment="comment"),
                    CommentBlock(
                        start_line=-1, end_line=-1, lines=["comment 1", "comment 2"]
                    ),
                    Property(
                        line=-1,
                        key="long-key",
                        value="long-value",
                        comment="long-comment",
                    ),
                    CommentBlock(
                        start_line=-1, end_line=-1, lines=["comment 3", "comment 4"]
                    ),
                ],
                _Lengths(max_key_length=12, max_value_length=15),
                SerializerConfig(section_indent=4, property_indent=4),
                [
                    "        key          = value           # comment",
                    "        # comment 1",
                    "        # comment 2",
                    "        long-key     = long-value      # long-comment",
                    "        # comment 3",
                    "        # comment 4",
                ],
            ),
        ],
    )
    def test_serialize_content(
        self,
        content: Iterable[Union[Property, CommentBlock]],
        lengths: _Lengths,
        config: SerializerConfig,
        expected_result: List[str],
    ):
        serializer = Serializer(config=config)

        result = list(serializer._serialize_content(content, lengths))
        assert result == expected_result

    @pytest.mark.parametrize(
        "datablock,lengths,config,expected_result",
        [
            (
                None,
                _Lengths(max_key_length=0, max_value_length=0),
                SerializerConfig(),
                [],
            ),
            (
                [["1.0", "2.0", "3.0"]],
                _Lengths(
                    max_key_length=0,
                    max_value_length=0,
                    max_datablock_element_length=[3, 4, 5],
                ),
                SerializerConfig(datablock_indent=2, datablock_spacing=4),
                ["  1.0    2.0     3.0"],
            ),
            (
                [
                    ["1.0", "2.0", "3.0"],
                    ["4.0", "10.0", "200.0"],
                ],
                _Lengths(
                    max_key_length=0,
                    max_value_length=0,
                    max_datablock_element_length=[3, 4, 5],
                ),
                SerializerConfig(datablock_indent=2, datablock_spacing=4),
                [
                    "  1.0    2.0     3.0",
                    "  4.0    10.0    200.0",
                ],
            ),
            (
                [["1.0"]],
                _Lengths(
                    max_key_length=0,
                    max_value_length=0,
                    max_datablock_element_length=[
                        3,
                    ],
                ),
                SerializerConfig(datablock_indent=2, datablock_spacing=4),
                ["  1.0"],
            ),
            (
                [["1.0"]],
                _Lengths(
                    max_key_length=0,
                    max_value_length=0,
                    max_datablock_element_length=None,
                ),
                SerializerConfig(datablock_indent=2, datablock_spacing=4),
                [],
            ),
        ],
    )
    def test_serialize_datablock(
        self,
        datablock: Optional[Iterable[Sequence[str]]],
        lengths: _Lengths,
        config: SerializerConfig,
        expected_result: List[str],
    ):
        serializer = Serializer(config=config)

        result = list(serializer._serialize_datablock(datablock, lengths))
        assert result == expected_result

    @pytest.mark.parametrize(
        "section,config,expected_result",
        [
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[],
                    datablock=None,
                ),
                SerializerConfig(section_indent=0, property_indent=0),
                ["[header]"],
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        CommentBlock(
                            start_line=-1, end_line=-1, lines=["angry badger noises"]
                        )
                    ],
                    datablock=None,
                ),
                SerializerConfig(section_indent=0, property_indent=0),
                ["[header]", "# angry badger noises"],
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        Property(line=-1, key="key", value="value", comment="comment"),
                    ],
                ),
                SerializerConfig(section_indent=2, property_indent=4),
                [
                    "  [header]",
                    "      key = value # comment",
                ],
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        Property(line=-1, key="key", value="value", comment="comment"),
                        CommentBlock(
                            start_line=-1, end_line=-1, lines=["comment 1", "comment 2"]
                        ),
                        Property(
                            line=-1,
                            key="long-key",
                            value="long-value",
                            comment="long-comment",
                        ),
                        CommentBlock(
                            start_line=-1, end_line=-1, lines=["comment 3", "comment 4"]
                        ),
                    ],
                ),
                SerializerConfig(section_indent=2, property_indent=4),
                [
                    "  [header]",
                    "      key      = value      # comment",
                    "      # comment 1",
                    "      # comment 2",
                    "      long-key = long-value # long-comment",
                    "      # comment 3",
                    "      # comment 4",
                ],
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[],
                    datablock=[
                        [
                            "1.0",
                            "2.0",
                            "3.0",
                            "4.0",
                        ],
                        [
                            "-1.0",
                            "4.0",
                            "9.0",
                            "16.0",
                        ],
                        [
                            "1.0",
                            "16.0",
                            "81.0",
                            "256.0",
                        ],
                    ],
                ),
                SerializerConfig(
                    section_indent=0,
                    property_indent=4,
                    datablock_indent=6,
                    datablock_spacing=4,
                ),
                [
                    "[header]",
                    "      1.0     2.0     3.0     4.0",
                    "      -1.0    4.0     9.0     16.0",
                    "      1.0     16.0    81.0    256.0",
                ],
            ),
            (
                Section(
                    header="header",
                    start_line=-1,
                    end_line=-1,
                    content=[
                        Property(line=-1, key="key", value="value", comment="comment"),
                        CommentBlock(
                            start_line=-1, end_line=-1, lines=["comment 1", "comment 2"]
                        ),
                        Property(
                            line=-1,
                            key="long-key",
                            value="long-value",
                            comment="long-comment",
                        ),
                        CommentBlock(
                            start_line=-1, end_line=-1, lines=["comment 3", "comment 4"]
                        ),
                    ],
                    datablock=[
                        [
                            "1.0",
                            "2.0",
                            "3.0",
                            "4.0",
                        ],
                        [
                            "-1.0",
                            "4.0",
                            "9.0",
                            "16.0",
                        ],
                        [
                            "1.0",
                            "16.0",
                            "81.0",
                            "256.0",
                        ],
                    ],
                ),
                SerializerConfig(
                    section_indent=0,
                    property_indent=4,
                    datablock_indent=6,
                    datablock_spacing=4,
                ),
                [
                    "[header]",
                    "    key      = value      # comment",
                    "    # comment 1",
                    "    # comment 2",
                    "    long-key = long-value # long-comment",
                    "    # comment 3",
                    "    # comment 4",
                    "      1.0     2.0     3.0     4.0",
                    "      -1.0    4.0     9.0     16.0",
                    "      1.0     16.0    81.0    256.0",
                ],
            ),
        ],
    )
    def test_serialize_section(
        self, section: Section, config: SerializerConfig, expected_result: List[str]
    ):
        serializer = Serializer(config=config)

        result = list(serializer._serialize_section(section))
        assert result == expected_result

    def test_deserialize_serialize_should_give_the_same_result(self):
        input_str = (
            inspect.cleandoc(
                """
            # deserialize - serialize test

            # initial header
            # with two lines

            [header1]
                key1       = value1       # some comment
                longer_key = longer_value # longer comment
                k          =              # c
                key2       = value2       # some comment

            [header2]
                key3          = value3          # some comment
                very_long_key = very_long_value # longer comment
                k             =                 # c
                key4          = value4          # some comment
            """
            )
            + "\n"
        )

        parser = Parser(config=ParserConfig())

        for line in input_str.splitlines():
            parser.feed_line(line)

        document = parser.finalize()

        serializer = Serializer(config=SerializerConfig())
        result = "\n".join(serializer.serialize(document))

        assert result == input_str
