from pathlib import Path

import pytest

from hydrolib.core.dflowfm.polyfile.models import PolyFile


def test_with_label(polylines_dir: Path):
    """
    The test check a simple 2*2 polyline file with a label
    Now the polyfile.parser does not support having any labels in the file.
    So the test should raise a ValueError.
    tfl_01
        2      2
        0.00000000000000000	0.00000000000000000e #zee
        0.00000000000000000	2.00000000000000000e #zee
    """
    path = polylines_dir.joinpath("polyline-no-z-with-label.pli")
    with pytest.raises(ValueError):
        PolyFile(path)


def test_without_z(polylines_dir: Path):
    """
    The test check a simple 2*2 polyline file without z values.
    L1
     2     2
     -80    -50
     -80    550
    """
    path = polylines_dir.joinpath("polyline-no-z-no-label.pli")
    polyline = PolyFile(path)
    assert polyline.has_z_values is False
    assert polyline.filepath == path
    assert polyline.save_location == path.absolute()
