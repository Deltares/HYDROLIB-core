from hydrolibcore.io.dflowfm.xyz import parser
from tests.utils import test_data_dir


def test_xyz_parser():
    fn = test_data_dir / "input" / "test.xyz"
    data = parser.XYZParser.parse(fn)
    assert "points" in data
    assert len(data.get("points", [])) == 7
