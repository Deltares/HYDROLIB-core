"""Equivalence tests for the SourceSink reference set from the kernel team.

For every (old_format, new_format) pair sharing a column-count prefix,
converting the old `sources.ext` via `extforce-convert` must yield a
SourceSink block with the same coordinates and z-fields as the
new-format direct read.
"""

from pathlib import Path
from typing import List, Tuple
from unittest.mock import patch

import pytest

from hydrolib.core.dflowfm.ext.models import ExtModel, SourceSink
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.tools.extforce_convert.main_converter import (
    ExternalForcingConverter,
)
from tests.utils import test_data_dir

DATA_ROOT = test_data_dir / "input" / "source-sink-format-variants"


EQUIVALENT_PAIRS = [
    ("2cols_old_format", "2cols_new_format"),
    ("3cols_old_format", "3cols_new_format"),
    ("4cols_old_format", "4cols_new_format_locationFile"),
    ("5cols_old_format", "5cols_new_format"),
]


COUPLED_EQUIVALENT_PAIRS = [
    (
        "_coupled_source_sink/3cols_old_format",
        "_coupled_source_sink/3cols_new_format",
    ),
    (
        "_coupled_source_sink/3cols_3rows_old_format",
        "_coupled_source_sink/3cols_3rows_new_format",
    ),
    (
        "_coupled_source_sink/5cols_old_format",
        "_coupled_source_sink/5cols_new_format",
    ),
]


def _as_list(value) -> List[float]:
    """Normalise a scalar, list, or None to a list for comparison."""
    result: List[float] = []
    if value is None:
        result = []
    elif isinstance(value, (list, tuple)):
        result = [float(v) for v in value]
    else:
        result = [float(value)]
    return result


def _convert_old_ext(mdu_path: Path) -> ExtModel:
    """Run extforce-convert on the given MDU and return the new ExtModel."""
    converter = ExternalForcingConverter.from_mdu(mdu_path)
    with patch(
        "hydrolib.tools.extforce_convert.main_converter"
        ".ExternalForcingConverter._update_mdu_file"
    ):
        ext_model, _, _ = converter.update()
    return ext_model


def _resolve_geometry(
    block: SourceSink, folder: Path
) -> Tuple[List[float], List[float], List[float], List[float]]:
    """Return (x, y, zsource, zsink) with `locationFile` resolved if used.

    When a block specifies `locationFile` instead of inline coordinates,
    read the polyline file to recover the equivalent (x, y, z) so that
    two blocks using different representation styles can be compared
    semantically.
    """
    xcoords = list(block.xcoordinates or [])
    ycoords = list(block.ycoordinates or [])
    zsource = _as_list(block.zsource)
    zsink = _as_list(block.zsink)

    locationfile_path = None
    if block.locationfile is not None and block.locationfile.filepath is not None:
        locationfile_path = folder / block.locationfile.filepath

    if locationfile_path is not None and locationfile_path.exists():
        polyline = PolyFile(locationfile_path)
        xcoords = list(polyline.x)
        ycoords = list(polyline.y)
        if str(locationfile_path).lower().endswith(".pliz"):
            file_zsource, file_zsink = polyline.get_z_sources_sinks()
            zsource = [z for z in file_zsource if z is not None]
            zsink = [z for z in file_zsink if z is not None]
            # Single-point polyline is a plain source; zsink is not used.
            if len(xcoords) == 1:
                zsink = []
    return xcoords, ycoords, zsource, zsink


def _assert_blocks_match(
    conv_block: SourceSink,
    ref_block: SourceSink,
    conv_folder: Path,
    ref_folder: Path,
) -> None:
    conv_xy_z = _resolve_geometry(conv_block, conv_folder)
    ref_xy_z = _resolve_geometry(ref_block, ref_folder)
    assert conv_xy_z == ref_xy_z


@pytest.mark.parametrize("old_folder,new_folder", EQUIVALENT_PAIRS)
def test_single_source_old_to_new_matches_reference(
    old_folder: str, new_folder: str
) -> None:
    old_mdu = DATA_ROOT / old_folder / "model.mdu"
    new_ext = DATA_ROOT / new_folder / "sources.ext"

    converted = _convert_old_ext(old_mdu)
    reference = ExtModel(new_ext)

    converted_blocks = {b.id: b for b in converted.sourcesink}
    reference_blocks = {b.id: b for b in reference.sourcesink}
    assert converted_blocks.keys() == reference_blocks.keys()

    conv_folder = DATA_ROOT / old_folder
    ref_folder = DATA_ROOT / new_folder
    for block_id, conv in converted_blocks.items():
        _assert_blocks_match(conv, reference_blocks[block_id], conv_folder, ref_folder)


@pytest.mark.parametrize("old_folder,new_folder", COUPLED_EQUIVALENT_PAIRS)
def test_coupled_old_to_new_matches_reference(old_folder: str, new_folder: str) -> None:
    old_mdu = DATA_ROOT / old_folder / "model.mdu"
    new_ext = DATA_ROOT / new_folder / "sources.ext"

    converted = _convert_old_ext(old_mdu)
    reference = ExtModel(new_ext)

    assert len(converted.sourcesink) == 1
    assert len(reference.sourcesink) == 1
    _assert_blocks_match(
        converted.sourcesink[0],
        reference.sourcesink[0],
        DATA_ROOT / old_folder,
        DATA_ROOT / new_folder,
    )
