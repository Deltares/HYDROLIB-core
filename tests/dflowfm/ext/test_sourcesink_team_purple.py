"""Round-trip tests for the SourceSink reference set from the kernel team.

Each new-format `sources.ext` under `tests/data/input/source-sink-format-variants/`
must parse cleanly, except folders ending in `_shouldError` which must raise.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from hydrolib.core.dflowfm.ext.models import ExtModel
from tests.utils import test_data_dir

DATA_ROOT = test_data_dir / "input" / "source-sink-format-variants"

SINGLE_SOURCE_NEW_FORMAT_OK = [
    "2cols_new_format",
    "3cols_new_format",
    "3cols_new_format_locationFile",
    "4cols_new_format_locationFile",
    "5cols_new_format",
    "5cols_new_format_locationFile",
]

SINGLE_SOURCE_NEW_FORMAT_SHOULD_ERROR = [
    "3cols_new_format_locationFile_zSource_shouldError",
    "5cols_new_format_locationFile_zSource_shouldError",
]

COUPLED_NEW_FORMAT_OK = [
    "_coupled_source_sink/3cols_new_format",
    "_coupled_source_sink/3cols_3rows_new_format",
    "_coupled_source_sink/3cols_new_format_locationFile_zSource_zSink",
    "_coupled_source_sink/3cols_3rows_format_locationFile_zSource_zSink",
    "_coupled_source_sink/5cols_new_format",
    "_coupled_source_sink/5cols_new_format_locationFile_zSource_zSink",
]

COUPLED_NEW_FORMAT_SHOULD_ERROR = [
    "_coupled_source_sink/3cols_new_format_locationFile_shouldError",
    "_coupled_source_sink/3cols_3rows_new_format_locationFile_shouldError",
    "_coupled_source_sink/5cols_new_format_locationFile_shouldError",
]


@pytest.mark.parametrize("folder", SINGLE_SOURCE_NEW_FORMAT_OK)
def test_single_source_new_format_parses(folder: str):
    ext_path = DATA_ROOT / folder / "sources.ext"
    model = ExtModel(ext_path)
    assert len(model.sourcesink) == 2
    assert {block.id for block in model.sourcesink} == {"left", "right"}


@pytest.mark.parametrize("folder", SINGLE_SOURCE_NEW_FORMAT_SHOULD_ERROR)
def test_single_source_new_format_should_error(folder: str):
    ext_path = DATA_ROOT / folder / "sources.ext"
    with pytest.raises((ValidationError, ValueError)):
        ExtModel(ext_path)


@pytest.mark.parametrize("folder", COUPLED_NEW_FORMAT_OK)
def test_coupled_source_sink_new_format_parses(folder: str):
    ext_path = DATA_ROOT / folder / "sources.ext"
    model = ExtModel(ext_path)
    assert len(model.sourcesink) == 1
    block = model.sourcesink[0]
    assert block.id == "left"
    assert block.zsource is not None
    assert block.zsink is not None


@pytest.mark.parametrize("folder", COUPLED_NEW_FORMAT_SHOULD_ERROR)
def test_coupled_source_sink_new_format_should_error(folder: str):
    ext_path = DATA_ROOT / folder / "sources.ext"
    with pytest.raises((ValidationError, ValueError)):
        ExtModel(ext_path)
