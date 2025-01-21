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
    assert polyline.x == [0, 0]
    assert polyline.y == [0, 2]
    assert polyline.number_of_points == 2


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
    assert polyline.x == [-80, -80]
    assert polyline.y == [-50, 550]
    assert polyline.number_of_points == 2


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
    assert polyline.x == [0, 0]
    assert polyline.y == [0, 2]


class TestGetZSourcesSinks:
    def test_get_z_sources_sinks_single_value(self):
        """
        The test case is based on the following assumptions:
        - The polyline has only 3 columns, so the zsink and zsource will have only one value which is in the third column.
        ```
        zsink = -4.2
        zsource = -3
        ```

        - The polyline file has the following structure:
        ```
        L1
             2 3
              63.35 12.95 -4.20
              45.20 6.35 -3.00
        ```
        """
        polyfile = PolyFile("tests/data/input/source-sink/leftsor.pliz")

        z_source, z_sink = polyfile.get_z_sources_sinks()
        assert z_source == [-3]
        assert z_sink == [-4.2]

    def test_get_z_sources_sinks_multiple_values(self):
        """
        The test case is based on the following assumptions:
        - The polyline has only four or five columns, so the zsink and zsource will have two values which is in the
        third and forth columns' values, and if there is a fifth column it will be ignored.
        ```
        zsink = [-4.2, -5.35]
        zsource = [-3, -2.90]
        ```

        - The polyline file has the following structure:
        ```
        L1
             2 3
              63.35 12.95 -4.20 -5.35
              ...

              ...
              45.20 6.35 -3.00 -2.90
        ```
        when there is a fifth column:
        ```
        L1
             2 3
              63.35 12.95 -4.20 -5.35 0
              ...

              ...
              45.20 6.35 -3.00 -2.90 0
        ```
        """
        polyfile = PolyFile("tests/data/input/source-sink/leftsor-5-columns.pliz")

        z_source, z_sink = polyfile.get_z_sources_sinks()
        assert z_source == [-3, -2.90]
        assert z_sink == [-4.2, -5.35]

    def test_get_z_sources_sinks_no_z_values(self, polylines_dir: Path):
        """
        The test case is based on the following assumptions:
        - The polyline has only two columns, so the zsink and zsource will have no values.
        ```
        zsink = []
        zsource = []
        ```

        - The polyline file has the following structure:
        ```
        L1
             2 2
              63.35 12.95
              45.20 6.35
        ```
        """
        path = polylines_dir / "boundary-polyline-no-z-no-label.pli"
        polyfile = PolyFile(path)

        z_source, z_sink = polyfile.get_z_sources_sinks()
        assert z_source == [None]
        assert z_sink == [None]


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
        assert polyfile.x == [0, 0]
        assert polyfile.y == [0, 2]

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
        assert polyfile.x == [63.35, 45.2]
        assert polyfile.y == [12.95, 6.35]
