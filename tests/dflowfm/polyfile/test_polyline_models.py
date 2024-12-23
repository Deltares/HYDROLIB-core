"""
- To read the z values correctly, the dimensions should be 2*3 and the extension should be pliz.
- If the file is .pliz and the dimensions are 2*2, the parser will give an error.
- If the file is .pli and the dimensions are 2*3, the parser will ignore the z values.
"""

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
    path = polylines_dir / "boundary-polyline-no-z-with-label.pli"
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
    path = polylines_dir / "boundary-polyline-no-z-no-label.pli"
    polyline = PolyFile(path)
    assert polyline.has_z_values is False
    assert polyline.filepath == path
    assert polyline.save_location == path.absolute()
    points = polyline.objects[0].points
    assert points[0] == Point(x=-80, y=-50, z=None, data=[])
    assert points[1] == Point(x=-80, y=550, z=None, data=[])


def test_with_z_and_pli_extension_2by2(polylines_dir: Path):
    """
    The test check a 2*2 polyline file with z values, but the extension is pli not pliz.
    the parser will ignore the z values and read the file as a normal polyline file.
    tfl_01
        2 2
        0.00000000000000000	0.00000000000000000 5
        0.00000000000000000	2.00000000000000000 5
    """
    path = polylines_dir / "boundary-polyline-with-z-no-label.pli"
    polyline = PolyFile(path)
    assert polyline.has_z_values is False
    assert polyline.filepath == path
    assert polyline.save_location == path.absolute()
    points = polyline.objects[0].points
    assert points[0] == Point(x=0, y=0, z=None, data=[])
    assert points[1] == Point(x=0, y=2, z=None, data=[])


class TestPLIZExtension:

    def test_with_z_and_pliz_extension_2by2(self, polylines_dir: Path):
        """
        The test check a 2*2 polyline file with z values, the extension is correct, but the dimensions are 2*2.
        not 2*3
        the parser only reads the length of the dimensions in the second line and ignores the z values.
        ```
        tfl_01
            2 2
            0.00000000000000000	0.00000000000000000 5
            0.00000000000000000	2.00000000000000000 5
        ```

        - To read the z values correctly, the dimensions should be 2*3, and the extension should be pliz.
        """
        path = polylines_dir / "boundary-polyline-with-z-no-label.pliz"
        with pytest.raises(ValueError):
            PolyFile(path)

    def test_with_z_and_pliz_extension_2by3(self, polylines_dir: Path):
        """
        The test check a 2*3, polyline file with z values, the extension is correct, and the dimensions are correct.
        the parser only reads the length of the dimensions in the second line and ignores the z values.
        ```
        tfl_01
            2 3
            0.00000000000000000	0.00000000000000000 5
            0.00000000000000000	2.00000000000000000 5
        ```
        - To read the z values correctly, the dimensions should be 2*3 and the extension should be pliz.
        """
        path = polylines_dir / "boundary-polyline-with-z-no-label-2by3.pliz"
        polyfile = PolyFile(path)
        points = polyfile.objects[0].points
        assert len(polyfile.objects[0].points) == 2
        assert points[0] == Point(x=0, y=0, z=5, data=[])
        assert points[1] == Point(x=0, y=2, z=5, data=[])

    def test_with_z_and_pliz_extension_2by5(self, polylines_dir: Path):
        """
        The test check a 2*5 polyline file with z values in the third and fourth columns, the extension is correct,
        but the dimensions are 2*5.

        ```
        L1
             2     5
              63.35      12.95      -4.20   -5.35  0
              45.20       6.35      -3.00   -2.90  0
        ```

        - The first three columns are the x, y, and z values.
        The rest of the columns are the data values.
        """
        path = polylines_dir / "leftsor-5-columns.pliz"
        polyfile = PolyFile(path)
        points = polyfile.objects[0].points
        assert len(polyfile.objects[0].points) == 2
        assert points[0] == Point(x=63.35, y=12.95, z=-4.2, data=[-5.35, 0])
        assert points[1] == Point(x=45.2, y=6.35, z=-3, data=[-2.90, 0])
