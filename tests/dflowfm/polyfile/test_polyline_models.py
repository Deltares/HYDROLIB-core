from pathlib import Path

import pytest

from hydrolib.core.dflowfm.polyfile.models import Point, PolyFile


def test_with_label(polylines_dir: Path):
    """
    The test check a simple 2*2 polyline file with a label
    Now the polyfile.parser does not support having any labels in the file.
    parser will ignore the label and read the file as a normal polyline file.
    tfl_01
        2      2
        0.00000000000000000	0.00000000000000000 #zee
        0.00000000000000000	2.00000000000000000 #zee
    """
    path = polylines_dir.joinpath("boundary-polyline-no-z-with-label.pli")
    polyline = PolyFile(path)
    assert polyline.has_z_values is False
    assert polyline.filepath == path
    assert polyline.save_location == path.absolute()


def test_without_z(polylines_dir: Path):
    """
    The test check a simple 2*2 polyline file without z values.
    L1
     2     2
     -80    -50
     -80    550
    """
    path = polylines_dir.joinpath("boundary-polyline-no-z-no-label.pli")
    polyline = PolyFile(path)
    assert polyline.has_z_values is False
    assert polyline.filepath == path
    assert polyline.save_location == path.absolute()
    points = polyline.objects[0].points
    assert points[0] == Point(x=-80, y=-50, z=None, data=[])
    assert points[1] == Point(x=-80, y=550, z=None, data=[])


def test_with_z_and_pli_extension(polylines_dir: Path):
    """
    The test check a 2*2 polyline file with z values but the extension is pli not pliz.
    the parser will ignore the z values and read the file as a normal polyline file.
    tfl_01
        2      2
        0.00000000000000000	0.00000000000000000 5
        0.00000000000000000	2.00000000000000000 5
    """
    path = polylines_dir.joinpath("boundary-polyline-with-z-no-label.pli")
    polyline = PolyFile(path)
    assert polyline.has_z_values is False
    assert polyline.filepath == path
    assert polyline.save_location == path.absolute()
    points = polyline.objects[0].points
    assert points[0] == Point(x=0, y=0, z=None, data=[])
    assert points[1] == Point(x=0, y=2, z=None, data=[])


def test_with_z_and_pliz_extension(polylines_dir: Path):
    """
    The test check a 2*2 polyline file with z values, the extension is correct but the dimensions are 2*2.
    not 2*3
    the parser only reads the length of the dimensions in the second line and ignores the z values.
    tfl_01
        2      2
        0.00000000000000000	0.00000000000000000 5
        0.00000000000000000	2.00000000000000000 5
    """
    path = polylines_dir.joinpath("boundary-polyline-with-z-no-label.pliz")
    with pytest.raises(ValueError):
        PolyFile(path)
