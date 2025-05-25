import inspect
from itertools import chain
from typing import Iterable, List, Optional, Union

import pytest
from pydantic import ValidationError, Field

from hydrolib.core.base.models import FileModel, ModelSaveSettings
from hydrolib.core.dflowfm.ini.io_models import (
    CommentBlock,
    ContentElement,
    Datablock,
    Document,
    Property,
    Section,
)
from hydrolib.core.dflowfm.ini.models import INIBasedModel
from hydrolib.core.dflowfm.ini.parser import (
    Parser,
    ParserConfig,
    _IntermediateCommentBlock,
    _IntermediateSection,
)
from hydrolib.core.dflowfm.ini.serializer import (
    DataBlockINIBasedSerializerConfig,
    INISerializerConfig,
    MaxLengths,
    SectionSerializer,
    Serializer,
    _serialize_comment_block,
    write_ini,
)

from tests.utils import test_output_dir


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
            Property(key=f"key{i}", value=f"value{i}", comment=None) for i in range(5)
        )

        for prop in properties:
            intermediate_section.add_property(prop)

        result = intermediate_section.finalize()

        expected_section = Section(
            header=header,
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

        result = intermediate_section.finalize()

        expected_section = Section(
            header=header,
            content=[CommentBlock(lines=list(x[0] for x in comments))],
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

        result = intermediate_section.finalize()

        expected_section = Section(
            header=header,
            content=[],
            datablock=data_rows,
        )

        assert result == expected_section

    def test_add_multiple_components_and_finalize_has_expected_results(self):
        # Setup values
        header = "some-header"
        start_line = 50

        properties = list(
            Property(key=f"key{i}", value=f"value{i}", comment=None) for i in range(10)
        )

        comment_blocks = [
            CommentBlock(lines=["a", "b"]),
            CommentBlock(lines=["c", "d", "e"]),
            CommentBlock(lines=["1", "3", "4", "6"]),
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
            intermediate_section.add_comment(comment, line + 50)  # type: ignore

        for prop in properties[:5]:
            intermediate_section.add_property(prop)

        for comment, line in zip(
            comment_blocks[1].lines, range(len(comment_blocks[1].lines))
        ):
            intermediate_section.add_comment(comment, line + 57)  # type: ignore

        for prop in properties[5:]:
            intermediate_section.add_property(prop)

        for comment, line in zip(
            comment_blocks[2].lines, range(len(comment_blocks[2].lines))
        ):
            intermediate_section.add_comment(comment, line + 65)  # type: ignore

        for row in datarows:
            intermediate_section.add_datarow(row)

        result = intermediate_section.finalize()

        expected_content: List[Union[CommentBlock, Property]] = [comment_blocks[0]] + properties[:5] + [comment_blocks[1]] + properties[5:] + [comment_blocks[2]]  # type: ignore

        expected_section = Section(
            header=header,
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
            pytest.param("[a-header]", True),
            pytest.param("[ also header but with whitespace ]", True),
            pytest.param("[ # this works, but please don't do that # ]", True),
            pytest.param(
                "                 [ prefixed whitespace is acceptable ]     ", True
            ),
            pytest.param("[ not closed", False, id="Header not closed (end)"),
            pytest.param("  also not closed ]", False, id="Header not closed (begin)"),
            pytest.param("(not-a-header)", False),
            pytest.param("{not-a-header}", False),
            pytest.param("", False),
            pytest.param("     ", False),
            pytest.param("something", False),
            pytest.param("       also something", False),
            pytest.param("# some comment", False),
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
        "line,config,expected_value,expected_comment",
        [
            ("key=value", ParserConfig(allow_only_keywords=False), "value", None),
            ("key=#value#", ParserConfig(allow_only_keywords=False), "#value#", None),
            (
                "key= value # comment words",
                ParserConfig(allow_only_keywords=False),
                "value",
                "comment words",
            ),
            (
                "key= #value# # comment words   ",
                ParserConfig(allow_only_keywords=False),
                "#value#",
                "comment words",
            ),
            (
                "key=value # With a comment and also hash #2 halfway",
                ParserConfig(allow_only_keywords=False),
                "value",
                "With a comment and also hash #2 halfway",
            ),
        ],
    )
    def test_retrieve_property_comment(
        self,
        line: str,
        config: ParserConfig,
        expected_value: str,
        expected_comment: str,
    ):
        parser = Parser(config)
        key, valuestring = parser._retrieve_key_value(line)
        assert parser._retrieve_property_comment(valuestring) == (
            expected_comment,
            expected_value,
        )

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

    @pytest.mark.parametrize(
        "line,expected_key,expected_value",
        [
            ("someParam = 1.0 # comment text", "someparam", "1.0"),
            ("someParam = 1.0", "someparam", "1.0"),
        ],
    )
    def test_float_values(
        self, tmp_path, line: str, expected_key: str, expected_value: str
    ):
        p = tmp_path / "test.ini"
        p.write_text("[sectionA]\n" + line)
        result = Parser.parse(p).flatten()
        assert result["sectiona"][expected_key] == expected_value

    @pytest.mark.parametrize(
        "line,expected_key,expected_value",
        [
            ("someParam = foo # comment text", "someparam", "foo"),
            ("someParam = ", "someparam", None),
            ("someParam = # comment text", "someparam", None),
            ("someParam = #value A# ", "someparam", "#value A#"),
            ("someParam = #value A# # some comment", "someparam", "#value A#"),
            (
                "someParam = value A # some comment with hash #2 in it",
                "someparam",
                "value A",
            ),
        ],
    )
    def test_string_values(
        self, tmp_path, line: str, expected_key: str, expected_value: str
    ):
        p = tmp_path / "test.ini"
        p.write_text("[sectionA]\n" + line)
        result = Parser.parse(p).flatten()
        assert result["sectiona"][expected_key] == expected_value

    def test_feed_comment_at_the_beginning_of_the_document_gets_added_to_the_header(
        self,
    ):
        parser = Parser(config=ParserConfig())

        comment_content = "some comment"

        parser.feed_line(f"# {comment_content}")
        result = parser.finalize()

        expected_header_comment = [CommentBlock(lines=[comment_content])]

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
            CommentBlock(lines=comment_blocks[v]) for v in range(5)
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
            CommentBlock(lines=comment_blocks[v]) for v in range(3)
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

        expected_header_comment = [CommentBlock(lines=[comment_content])]

        assert result.header_comment == expected_header_comment
        assert len(result.sections) == 1

    def test_section_is_added_correctly(self):
        parser = Parser(config=ParserConfig())

        header = "header"
        properties = list(
            Property(
                key=f"key-{v}",
                value=f"value_{v}",
                comment=f"comment_{v}",
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
                            lines=["comment in a section", "starting with two lines"],
                        ),
                        Property(
                            key="key",
                            value="value",
                            comment="with a comment",
                        ),
                        Property(
                            key="another-key",
                            value="another-value",
                            comment=None,
                        ),
                        CommentBlock(lines=["inbetween comment"]),
                        Property(
                            key="last-key",
                            value="last value",
                            comment="inline comment",
                        ),
                        CommentBlock(lines=["last comment"]),
                    ],
                    datablock=None,
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
                            lines=["some comment", "consisting of two lines"],
                        ),
                        Property(key="key", value="value", comment=None),
                        Property(
                            key="some-key",
                            value="some-value",
                            comment=None,
                        ),
                        CommentBlock(lines=["inbetween comment"]),
                        Property(
                            key="last-key",
                            value="last value",
                            comment=None,
                        ),
                        CommentBlock(lines=["last comment"]),
                    ],
                    datablock=[
                        ["1.0", "2.0", "3.0"],
                        ["4.0", "5.0", "6.0"],
                        ["7.0", "8.0", "9.0"],
                        ["10.0", "11.0", "12.0"],
                    ],
                )
            ]
        )

        assert result == expected_result

    def test_multiple_sections_are_added_correctly(self):
        parser = Parser(config=ParserConfig())

        properties = list(
            Property(
                key=f"key-{v}",
                value=f"value_{v}",
                comment=f"comment_{v}",
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
        parser.feed_line("")

        result = parser.finalize()

        expected_result = Document(
            sections=[
                Section(
                    header="header1",
                    content=properties[:6],
                    datablock=None,
                ),
                Section(
                    header="header2",
                    content=properties[6:],
                    datablock=None,
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
                    lines=["this is a very contrived example", "with a header"],
                ),
                CommentBlock(
                    lines=["consisting of multiple blocks", "with datablocks"],
                ),
            ],
            sections=[
                Section(
                    header="header",
                    content=[
                        CommentBlock(
                            lines=["some comment", "consisting of two lines"],
                        ),
                        Property(
                            key="key",
                            value="value",
                            comment="with a comment",
                        ),
                        Property(
                            key="another-key",
                            value="another-value",
                            comment=None,
                        ),
                        CommentBlock(lines=["inbetween comment"]),
                        Property(
                            key="last-key",
                            value="last value",
                            comment="inline comment",
                        ),
                        CommentBlock(lines=["last comment"]),
                    ],
                    datablock=[
                        ["1.0", "2.0", "3.0"],
                        ["4.0", "5.0", "6.0"],
                    ],
                ),
                Section(
                    header="different-header",
                    content=[
                        Property(
                            key="key1",
                            value="value1",
                            comment="comment1",
                        ),
                        Property(
                            key="key2",
                            value="value2",
                            comment="comment2",
                        ),
                        Property(
                            key="key3",
                            value="value3",
                            comment="comment3",
                        ),
                        CommentBlock(
                            lines=["some comment1", "some comment2"],
                        ),
                    ],
                    datablock=[
                        ["7.0", "8.0", "9.0"],
                        ["10.0", "11.0", "12.0"],
                    ],
                ),
            ],
        )

        assert result == expected_result


class TestINISerializerConfig:
    def test_total_property_indent_expected_result(self):
        config = INISerializerConfig(section_indent=5, property_indent=3)
        assert config.total_property_indent == 8

    def test_total_datablock_indent_expected_result(self):
        config = INISerializerConfig(section_indent=3, datablock_indent=10)
        assert config.total_datablock_indent == 13

    def test_default_serializer_config(self):
        config = INISerializerConfig()
        assert config.section_indent == 0
        assert config.property_indent == 0
        assert config.datablock_indent == 8
        assert config.datablock_spacing == 2
        assert config.comment_delimiter == "#"
        assert config.skip_empty_properties == True
        assert config.float_format == ""


class TestDataBlockINIBasedSerializerConfig:
    def test_default_serializer_config(self):
        config = DataBlockINIBasedSerializerConfig()
        assert config.section_indent == 0
        assert config.property_indent == 0
        assert config.datablock_indent == 8
        assert config.datablock_spacing == 2
        assert config.comment_delimiter == "#"
        assert config.skip_empty_properties == True
        assert config.float_format == ""
        assert config.float_format_datablock == ""


class TestLengths:
    @pytest.mark.parametrize(
        "section,expected_result",
        [
            (
                Section(
                    header="header",
                    content=[],
                    datablock=None,
                ),
                MaxLengths(
                    key=0,
                    value=0,
                    datablock=None,
                ),
            ),
            (
                Section(
                    header="header",
                    content=[
                        CommentBlock(lines=[]),
                    ],
                    datablock=None,
                ),
                MaxLengths(
                    key=0,
                    value=0,
                    datablock=None,
                ),
            ),
            (
                Section(
                    header="header",
                    content=[
                        CommentBlock(
                            lines=["one", "two", "three", "four"],
                        ),
                    ],
                    datablock=None,
                ),
                MaxLengths(
                    key=0,
                    value=0,
                    datablock=None,
                ),
            ),
            (
                Section(
                    header="header",
                    content=[
                        Property(key="key", value="value", comment="comment"),
                    ],
                    datablock=None,
                ),
                MaxLengths(
                    key=3,
                    value=5,
                    datablock=None,
                ),
            ),
            (
                Section(
                    header="header",
                    content=[
                        Property(key="key", value="value", comment="comment"),
                        Property(key="123", value="12345", comment="comment"),
                    ],
                    datablock=None,
                ),
                MaxLengths(
                    key=3,
                    value=5,
                    datablock=None,
                ),
            ),
            (
                Section(
                    header="header",
                    content=[
                        Property(key="key", value="value", comment="comment"),
                        Property(key="long-key", value="value", comment="comment"),
                    ],
                    datablock=None,
                ),
                MaxLengths(
                    key=8,
                    value=5,
                    datablock=None,
                ),
            ),
            (
                Section(
                    header="header",
                    content=[
                        Property(key="key", value="long-value", comment="comment"),
                        Property(key="key", value="value", comment="comment"),
                    ],
                    datablock=None,
                ),
                MaxLengths(
                    key=3,
                    value=10,
                    datablock=None,
                ),
            ),
            (
                Section(
                    header="header",
                    content=[
                        CommentBlock(
                            lines=["one", "two", "three", "four"],
                        ),
                        Property(key="key", value="value", comment="comment"),
                        CommentBlock(
                            lines=["five", "six", "seven", "eight"],
                        ),
                    ],
                    datablock=None,
                ),
                MaxLengths(
                    key=3,
                    value=5,
                    datablock=None,
                ),
            ),
            (
                Section(
                    header="header",
                    content=[
                        Property(key="key", value="value", comment="comment"),
                        Property(key="long-key", value="value", comment=None),
                    ],
                    datablock=None,
                ),
                MaxLengths(
                    key=8,
                    value=5,
                    datablock=None,
                ),
            ),
            (
                Section(
                    header="header",
                    content=[
                        Property(key="long-key", value="value", comment=None),
                    ],
                    datablock=None,
                ),
                MaxLengths(
                    key=8,
                    value=5,
                    datablock=None,
                ),
            ),
            (
                Section(
                    header="header",
                    content=[
                        Property(key="long-key", value=None, comment=None),
                    ],
                    datablock=None,
                ),
                MaxLengths(
                    key=8,
                    value=0,
                    datablock=None,
                ),
            ),
            (
                Section(
                    header="header",
                    content=[],
                    datablock=[["1.23"]],
                ),
                MaxLengths(
                    key=0,
                    value=0,
                    datablock=(4,),
                ),
            ),
            (
                Section(
                    header="header",
                    content=[],
                    datablock=[["1.23", "1.2345", "1.234567"]],
                ),
                MaxLengths(
                    key=0,
                    value=0,
                    datablock=(4, 6, 8),
                ),
            ),
            (
                Section(
                    header="header",
                    content=[],
                    datablock=[
                        ["1.23", "1.0", "1.234567"],
                        ["0.0", "1.2345", "1.23456789"],
                        ["0.0", "0.0", "0.0"],
                    ],
                ),
                MaxLengths(
                    key=0,
                    value=0,
                    datablock=(4, 6, 10),
                ),
            ),
        ],
    )
    def test_from_section_expected_results(
        self, section: Section, expected_result: MaxLengths
    ):
        result = MaxLengths.from_section(section)
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
        "comment_block,delimiter,offset,expected_result",
        [
            (
                CommentBlock(lines=[]),
                "#",
                0,
                [],
            ),
            (
                CommentBlock(lines=["angry badger noises"]),
                "#",
                0,
                ["# angry badger noises"],
            ),
            (
                CommentBlock(lines=["comment"]),
                "#",
                4,
                ["    # comment"],
            ),
            (
                CommentBlock(lines=["one", "two", "three"]),
                "#",
                4,
                ["    # one", "    # two", "    # three"],
            ),
            (
                CommentBlock(lines=["comment"]),
                "*",
                6,
                ["      * comment"],
            ),
        ],
    )
    def test_serialize_comment_block(
        self,
        comment_block: CommentBlock,
        delimiter: str,
        offset: int,
        expected_result: List[str],
    ):
        result = list(_serialize_comment_block(comment_block, delimiter, offset))
        assert result == expected_result

    @pytest.mark.parametrize(
        "comment_header,config,expected_result",
        [
            (
                [],
                INISerializerConfig(),
                [],
            ),
            (
                [CommentBlock(lines=[])],
                INISerializerConfig(),
                [""],
            ),
            (
                [CommentBlock(lines=["angry badger noises"])],
                INISerializerConfig(),
                ["# angry badger noises", ""],
            ),
            (
                [CommentBlock(lines=["one", "two", "three"])],
                INISerializerConfig(),
                ["# one", "# two", "# three", ""],
            ),
            (
                [CommentBlock(lines=["comment"])],
                INISerializerConfig(comment_delimiter="*"),
                ["* comment", ""],
            ),
            (
                [
                    CommentBlock(lines=["one", "two", "three"]),
                    CommentBlock(lines=["four", "five", "six"]),
                ],
                INISerializerConfig(),
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
        config: INISerializerConfig,
        expected_result: List[str],
    ):
        serializer = Serializer(config=config)

        result = list(serializer._serialize_document_header(comment_header))
        assert result == expected_result

    @pytest.mark.parametrize(
        "header,config,expected_result",
        [
            ("header", INISerializerConfig(section_indent=0), "[header]"),
            ("header", INISerializerConfig(section_indent=4), "    [header]"),
            ("with spaces", INISerializerConfig(section_indent=0), "[with spaces]"),
        ],
    )
    def test_serialize_section_header(
        self,
        header: str,
        config: INISerializerConfig,
        expected_result: str,
    ):
        lengths = MaxLengths(key=0, value=0, datablock=None)
        serializer = SectionSerializer(config=config, max_length=lengths)

        result = list(serializer._serialize_section_header(header))
        assert result == [expected_result]

    @pytest.mark.parametrize(
        "property,lengths,config,expected_result",
        [
            (
                Property(key="key", value="value", comment="comment"),
                MaxLengths(key=3, value=5),
                INISerializerConfig(section_indent=0, property_indent=0),
                "key = value # comment",
            ),
            (
                Property(key="key", value="value", comment="comment"),
                MaxLengths(key=3, value=5),
                INISerializerConfig(section_indent=0, property_indent=4),
                "    key = value # comment",
            ),
            (
                Property(key="key", value="value", comment="comment"),
                MaxLengths(key=3, value=5),
                INISerializerConfig(section_indent=4, property_indent=0),
                "    key = value # comment",
            ),
            (
                Property(key="key", value="value", comment="comment"),
                MaxLengths(key=3, value=5),
                INISerializerConfig(section_indent=4, property_indent=4),
                "        key = value # comment",
            ),
            (
                Property(key="key", value="value", comment=None),
                MaxLengths(key=3, value=5),
                INISerializerConfig(section_indent=0, property_indent=0),
                "key = value",
            ),
            (
                Property(key="key", value=None, comment=None),
                MaxLengths(key=3, value=0),
                INISerializerConfig(
                    section_indent=0, property_indent=0, skip_empty_properties=False
                ),
                "key =",
            ),
            (
                Property(key="key", value=None, comment="comment"),
                MaxLengths(key=3, value=5),
                INISerializerConfig(
                    section_indent=0, property_indent=0, skip_empty_properties=False
                ),
                "key =       # comment",
            ),
            (
                Property(key="key", value="value", comment="comment"),
                MaxLengths(key=6, value=5),
                INISerializerConfig(section_indent=0, property_indent=0),
                "key    = value # comment",
            ),
            (
                Property(key="key", value="value", comment="comment"),
                MaxLengths(key=6, value=12),
                INISerializerConfig(section_indent=0, property_indent=0),
                "key    = value        # comment",
            ),
            (
                Property(key="key", value="value", comment="comment"),
                MaxLengths(key=6, value=12),
                INISerializerConfig(section_indent=2, property_indent=4),
                "      key    = value        # comment",
            ),
        ],
    )
    def test_serialize_property(
        self,
        property: Property,
        lengths: MaxLengths,
        config: INISerializerConfig,
        expected_result: str,
    ):
        serializer = SectionSerializer(config=config, max_length=lengths)

        result = list(serializer._serialize_property(property))
        assert result == [expected_result]

    @pytest.mark.parametrize(
        "content,lengths,config,expected_result",
        [
            (
                [],
                MaxLengths(key=0, value=0),
                INISerializerConfig(section_indent=0, property_indent=0),
                [],
            ),
            (
                [Property(key="key", value="value", comment="comment")],
                MaxLengths(key=3, value=5),
                INISerializerConfig(section_indent=0, property_indent=0),
                ["key = value # comment"],
            ),
            (
                [CommentBlock(lines=["angry badger noises"])],
                MaxLengths(key=3, value=5),
                INISerializerConfig(section_indent=0, property_indent=0),
                ["# angry badger noises"],
            ),
            (
                [CommentBlock(lines=["comment 1", "comment 2"])],
                MaxLengths(key=3, value=5),
                INISerializerConfig(section_indent=0, property_indent=4),
                ["    # comment 1", "    # comment 2"],
            ),
            (
                [
                    Property(key="key", value="value", comment="comment"),
                    CommentBlock(lines=["comment 1", "comment 2"]),
                    Property(
                        key="long-key",
                        value="long-value",
                        comment="long-comment",
                    ),
                    CommentBlock(lines=["comment 3", "comment 4"]),
                ],
                MaxLengths(key=12, value=15),
                INISerializerConfig(section_indent=4, property_indent=4),
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
        content: Iterable[ContentElement],
        lengths: MaxLengths,
        config: INISerializerConfig,
        expected_result: List[str],
    ):
        serializer = SectionSerializer(config=config, max_length=lengths)

        result = list(serializer._serialize_content(content))
        assert result == expected_result

    @pytest.mark.parametrize(
        "datablock,lengths,config,expected_result",
        [
            (
                None,
                MaxLengths(key=0, value=0),
                INISerializerConfig(),
                [],
            ),
            (
                [["1.0", "2.0", "3.0"]],
                MaxLengths(
                    key=0,
                    value=0,
                    datablock=[3, 4, 5],
                ),
                INISerializerConfig(datablock_indent=2, datablock_spacing=4),
                ["  1.0    2.0     3.0"],
            ),
            (
                [
                    ["1.0", "2.0", "3.0"],
                    ["4.0", "10.0", "200.0"],
                ],
                MaxLengths(
                    key=0,
                    value=0,
                    datablock=[3, 4, 5],
                ),
                INISerializerConfig(datablock_indent=2, datablock_spacing=4),
                [
                    "  1.0    2.0     3.0",
                    "  4.0    10.0    200.0",
                ],
            ),
            (
                [["1.0"]],
                MaxLengths(
                    key=0,
                    value=0,
                    datablock=[3],
                ),
                INISerializerConfig(datablock_indent=2, datablock_spacing=4),
                ["  1.0"],
            ),
            (
                [["1.0"]],
                MaxLengths(
                    key=0,
                    value=0,
                    datablock=None,
                ),
                INISerializerConfig(datablock_indent=2, datablock_spacing=4),
                [],
            ),
        ],
    )
    def test_serialize_datablock(
        self,
        datablock: Optional[Datablock],
        lengths: MaxLengths,
        config: INISerializerConfig,
        expected_result: List[str],
    ):
        serializer = SectionSerializer(config=config, max_length=lengths)

        result = list(serializer._serialize_datablock(datablock))
        assert result == expected_result

    @pytest.mark.parametrize(
        "section,config,expected_result",
        [
            (
                Section(
                    header="header",
                    content=[],
                    datablock=None,
                ),
                INISerializerConfig(section_indent=0, property_indent=0),
                ["[header]"],
            ),
            (
                Section(
                    header="header",
                    content=[CommentBlock(lines=["angry badger noises"])],
                    datablock=None,
                ),
                INISerializerConfig(section_indent=0, property_indent=0),
                ["[header]", "# angry badger noises"],
            ),
            (
                Section(
                    header="header",
                    content=[
                        Property(key="key", value="value", comment="comment"),
                    ],
                ),
                INISerializerConfig(section_indent=2, property_indent=4),
                [
                    "  [header]",
                    "      key = value # comment",
                ],
            ),
            (
                Section(
                    header="header",
                    content=[
                        Property(key="key", value="value", comment="comment"),
                        CommentBlock(lines=["comment 1", "comment 2"]),
                        Property(
                            key="long-key",
                            value="long-value",
                            comment="long-comment",
                        ),
                        CommentBlock(lines=["comment 3", "comment 4"]),
                    ],
                ),
                INISerializerConfig(section_indent=2, property_indent=4),
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
                INISerializerConfig(
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
                    content=[
                        Property(key="key", value="value", comment="comment"),
                        CommentBlock(lines=["comment 1", "comment 2"]),
                        Property(
                            key="long-key",
                            value="long-value",
                            comment="long-comment",
                        ),
                        CommentBlock(lines=["comment 3", "comment 4"]),
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
                INISerializerConfig(
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
            (
                Section(
                    header="header",
                    content=[
                        Property(key="key1", value="value", comment="comment1"),
                        Property(key="key2", value="", comment="comment2"),
                        Property(key="key3", value=None, comment="comment3"),
                    ],
                    datablock=[],
                ),
                INISerializerConfig(
                    section_indent=0,
                    property_indent=4,
                    datablock_indent=6,
                    datablock_spacing=4,
                    skip_empty_properties=False,
                ),
                [
                    "[header]",
                    "    key1 = value # comment1",
                    "    key2 =       # comment2",
                    "    key3 =       # comment3",
                ],
            ),
            (
                Section(
                    header="header",
                    content=[
                        Property(key="key1", value="value", comment="comment1"),
                        Property(key="key2", value="", comment="comment2"),
                        Property(key="key3", value=None, comment="comment3"),
                        Property(key="key4", value="   ", comment="comment4"),
                    ],
                    datablock=[],
                ),
                INISerializerConfig(
                    section_indent=0,
                    property_indent=4,
                    datablock_indent=6,
                    datablock_spacing=4,
                    skip_empty_properties=True,
                ),
                ["[header]", "    key1 = value # comment1"],
            ),
        ],
    )
    def test_serialize_section(
        self,
        section: Section,
        config: INISerializerConfig,
        expected_result: List[str],
    ):
        result = list(SectionSerializer.serialize(section, config))
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

        serializer = Serializer(config=INISerializerConfig(skip_empty_properties=False))
        result = "\n".join(serializer.serialize(document))

        assert result == input_str

    def test_non_filemodel_keyword_with_none_value_does_not_get_added_to_section(self):
        class TestINIBasedModel(INIBasedModel):
            random_property: str = Field(None)

        config = INISerializerConfig()
        settings = ModelSaveSettings()
        model = TestINIBasedModel()

        section = model._to_section(config, settings)

        assert len(section.content) == 0

    def test_filemodel_keyword_with_none_value_does_get_added_to_section(self):
        class TestINIBasedModel(INIBasedModel):
            random_property: FileModel = Field(None)
            random_property2: Union[FileModel, str] = Field(None)
            random_property3: List[FileModel] = Field(None)

        config = INISerializerConfig()
        settings = ModelSaveSettings()
        model = TestINIBasedModel()

        section = model._to_section(config, settings)

        assert len(section.content) == 3
        assert section.content[0].key == "random_property"
        assert section.content[0].value == ""
        assert section.content[1].key == "random_property2"
        assert section.content[1].value == ""
        assert section.content[2].key == "random_property3"
        assert section.content[2].value == ""


def test_serialize_deserialize_should_give_the_same_result():
    document = Document(
        header_comment=[
            CommentBlock(
                lines=["HYDROLIB-Core serialize | deserialize test", "extra crisp"],
            )
        ],
        sections=[
            Section(
                header="header1",
                content=[
                    Property(key="key1", value="value1", comment=None),
                    Property(key="key2", value=None, comment=None),
                    Property(key="key3", value=None, comment="comment"),
                    CommentBlock(lines=["comment 1", "comment 2"]),
                    Property(key="key4", value="1.34", comment="comment"),
                    CommentBlock(lines=["comment 3", "comment 4"]),
                ],
                datablock=[
                    ["a", "b", "c"],
                    ["1", "2", "3"],
                    ["hydro", "lib", "core"],
                ],
            ),
            Section(
                header="header2",
                content=[
                    Property(
                        key="key6",
                        value="value2",
                        comment=None,
                    ),
                    Property(
                        key="key7",
                        value=None,
                        comment=None,
                    ),
                    Property(
                        key="key8",
                        value=None,
                        comment="comment",
                    ),
                    CommentBlock(lines=["comment 5", "comment 6"]),
                    Property(key="key9", value="1.34", comment="comment"),
                    CommentBlock(lines=["comment 7", "comment 8"]),
                ],
                datablock=None,
            ),
            Section(
                header="header3",
                content=[
                    Property(
                        key="key10",
                        value="value10",
                        comment=None,
                    ),
                    Property(
                        key="key20",
                        value=None,
                        comment=None,
                    ),
                    Property(
                        key="key30",
                        value=None,
                        comment="comment",
                    ),
                    CommentBlock(
                        lines=["comment 10", "comment 20"],
                    ),
                    Property(
                        key="key40",
                        value="34.5",
                        comment="comment",
                    ),
                    CommentBlock(
                        lines=["comment 30", "comment 40"],
                    ),
                ],
                datablock=[
                    ["ab", "bc", "cd"],
                    ["111", "222", "333"],
                    ["hydro", "lib", "core"],
                ],
            ),
        ],
    )

    path = test_output_dir / "tmp" / "test.pliz"
    write_ini(path, document, config=INISerializerConfig(skip_empty_properties=False))

    parser = Parser(config=ParserConfig(parse_datablocks=True))
    with path.open("r") as f:
        for line in f:
            parser.feed_line(line)

    result = parser.finalize()

    assert result == document
