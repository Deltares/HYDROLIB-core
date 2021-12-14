import json
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pytest
from meshkernel import GeometryList, MeshKernel

from hydrolib.core.io.net.models import Branch, Mesh2d, NetworkModel
from hydrolib.core.io.net.reader import NCExplorer

from ..utils import test_input_dir, test_output_dir


def plot_network(network):
    _, ax = plt.subplots()
    ax.set_aspect(1.0)
    network.plot(ax=ax)
    ax.autoscale()
    plt.show()


@pytest.mark.plots
def test_create_1d_by_branch():

    # Define line
    x = np.linspace(0, 4 * np.pi, 1000)
    y = np.sin(x)

    # Create branch
    branch = Branch(geometry=np.stack([x, y], axis=1))
    # Generate nodes on branch
    branch.generate_nodes(mesh1d_edge_length=1)
    # Create Mesh1d
    network = NetworkModel()
    network.mesh1d_add_branch(branch)

    # Add second
    branch = Branch(geometry=np.array([[-4.0, 3.0], [0.0, 0.0]]))
    branch.generate_nodes(mesh1d_edge_length=1.0)
    network.mesh1d_add_branch(branch, name="my_branch")

    # And third, reversed
    branch = Branch(geometry=np.array([[0.0, 0.0], [-5.0, 0.0]]))
    branch.generate_nodes(mesh1d_edge_length=1.0)
    network.mesh1d_add_branch(branch)

    # And fourth, but this one manually
    branch = Branch(
        geometry=np.array([[-4.0, -3.0], [0.0, 0.0]]),
        branch_offsets=np.arange(6, dtype=float),
        mask=np.array([False, False, False, False, False, True]),
    )
    network.mesh1d_add_branch(branch)

    plot_network(network)

    # Write to file
    network.save(test_output_dir / "test_net.nc")


def get_circle_gl(r, detail=100):

    t = np.r_[np.linspace(0, 2 * np.pi, detail), 0]
    polygon = GeometryList(np.cos(t) * r, np.sin(t) * r)
    return polygon


@pytest.mark.plots
def test_create_1d_2d_1d2d():

    # Define line (spiral)
    theta = np.arange(0.1, 20, 0.01)

    y = np.sin(theta) * theta
    x = np.cos(theta) * theta

    dists = np.r_[0.0, np.cumsum(np.hypot(np.diff(x), np.diff(y)))]
    dists = dists[np.arange(0, len(dists), 20)]

    # Create branch
    branch = Branch(geometry=np.stack([x, y], axis=1), branch_offsets=dists)

    # Create Mesh1d
    network = NetworkModel()
    network.mesh1d_add_branch(branch, name="branch1")

    branch = Branch(geometry=np.array([[-25.0, 0.0], [x[0], y[0]]]))
    branch.generate_nodes(mesh1d_edge_length=2.5)
    network.mesh1d_add_branch(branch, name="branch2")

    # Add Mesh2d
    network.mesh2d_create_rectilinear_within_bounds(
        extent=(-22, -22, 22, 22), dx=2, dy=2
    )
    network.mesh2d_clip_mesh(polygon=get_circle_gl(22))

    network.mesh2d_refine_mesh(polygon=get_circle_gl(11), level=1)
    network.mesh2d_refine_mesh(polygon=get_circle_gl(3), level=1)

    # Add links
    network.link1d2d_from_1d_to_2d(branchids=["branch1"], polygon=get_circle_gl(19))

    # Write to file
    network.save(test_output_dir / "test_net.nc")

    plot_network(network)


def test_create_2d():

    # Define polygon
    bbox = (1.0, -2.0, 3.0, 4.0)

    mesh2d = Mesh2d(meshkernel=MeshKernel())
    mesh2d.create_rectilinear(extent=bbox, dx=0.5, dy=0.75)

    mesh2d_output = mesh2d.get_mesh2d()
    assert mesh2d_output.node_x.size == 45
    assert mesh2d_output.edge_nodes.size == 152


def test_create_clip_2d():

    polygon = GeometryList(
        x_coordinates=np.array([0.0, 6.0, 4.0, 2.0, 0.0]),
        y_coordinates=np.array([0.0, 2.0, 7.0, 6.0, 0.0]),
    )

    # Define polygon
    bbox = (1.0, -2.0, 3.0, 4.0)
    mesh2d = Mesh2d(meshkernel=MeshKernel())
    mesh2d.create_rectilinear(extent=bbox, dx=0.5, dy=0.75)
    mesh2d.clip(polygon)

    mesh2d_output = mesh2d.get_mesh2d()

    assert mesh2d_output.node_x.size == 28
    assert mesh2d_output.edge_nodes.size == 90


def test_create_refine_2d():

    polygon = GeometryList(
        x_coordinates=np.array([0.0, 6.0, 4.0, 2.0, 0.0]),
        y_coordinates=np.array([0.0, 2.0, 7.0, 6.0, 0.0]),
    )

    # Define polygon
    bbox = (1.0, -2.0, 3.0, 4.0)
    # Create instance
    mesh2d = Mesh2d(meshkernel=MeshKernel())
    # Create within bounding box
    mesh2d.create_rectilinear(extent=bbox, dx=0.5, dy=0.75)
    # Refine
    mesh2d.refine(polygon, 1)

    mesh2d_output = mesh2d.get_mesh2d()

    assert mesh2d_output.node_x.size == 114
    assert mesh2d_output.edge_nodes.size == 426


cases = [
    test_input_dir / "e02/f101_1D-boundaries/c01_steady-state-flow/Boundary_net.nc",
    test_input_dir / "e02/c11_korte-woerden-1d/dimr_model/dflowfm/FlowFM_net.nc",
]


@pytest.mark.parametrize(
    "filepath",
    cases,
)
def test_read_net_nc(filepath):
    # Get nc file path
    if not filepath.exists():
        raise FileNotFoundError(f'File "{filepath.resolve()}" not found.')

    # Create network model
    network = NetworkModel(filepath=filepath)
    assert not network._mesh1d.is_empty()
    assert network._mesh2d.is_empty()


@pytest.mark.parametrize("filepath", cases)
def test_read_write_read_compare(filepath):
    # Get nc file path
    assert filepath.exists()

    # Create network model
    network1 = NetworkModel(filepath=filepath)

    # Save to temporary location
    save_path = (
        test_output_dir
        / test_read_write_read_compare.__name__
        / network1._generate_name()
    )
    network1.save(filepath=save_path)

    # Read a second network from this location
    network2 = NetworkModel(filepath=network1.filepath)

    # Read keys from convention
    path = Path(__file__).parent.parent.parent.joinpath(
        "hydrolib/core/io/net/ugrid_conventions.json"
    )

    with open(path, "r") as f:
        conventions = json.load(f)

    for cat, dct in conventions.items():
        if cat == "mesh2d":
            part1 = getattr(network1, "_mesh2d")
            part2 = getattr(network2, "_mesh2d")

        elif cat == "mesh1d" or cat == "network1d":
            part1 = getattr(network1, "_mesh1d")
            part2 = getattr(network2, "_mesh1d")

        elif cat == "link1d2d":
            part1 = getattr(network1, "_link1d2d")
            part2 = getattr(network2, "_link1d2d")

        for key in dct.keys():
            np.testing.assert_array_equal(getattr(part1, key), getattr(part2, key))


class TestMesh2d:
    test_file = test_input_dir / "ugrid_files" / "mesh2d_net.nc"

    def test_read_file_expected_results(self):
        mesh = Mesh2d()
        mesh.read_file(self.test_file)

        # fmt: off
        mesh2d_node_x=np.asarray([ 0.0, 0.0, 0.0, 0.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 300.0, 300.0, 300.0, 300.0, 300.0, 300.0, 400.0, 400.0, 400.0, 400.0, 400.0, 400.0, 500.0, 500.0, 500.0, 500.0, ]),
        mesh2d_node_y=np.asarray([ 200.0,300.0, 400.0, 500.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 200.0, 300.0, 400.0, 500.0,]),
        mesh2d_node_z=np.asarray([-999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0, ]),
        mesh2d_edge_x=np.ndarray([], dtype=np.float64),
        mesh2d_edge_y=np.ndarray([], dtype=np.float64),
        mesh2d_edge_z=np.ndarray([], dtype=np.float64),
        mesh2d_edge_nodes=np.array([
            [ 0,  5],
            [ 5,  6],
            [ 6,  1],
            [ 1,  0],
            [ 6,  7],
            [ 7,  2],
            [ 2,  1],
            [ 7,  8],
            [ 8,  3],
            [ 3,  2],
            [ 4, 10],
            [10, 11],
            [11,  5],
            [ 5,  4],
            [11, 12],
            [12,  6],
            [12, 13],
            [13,  7],
            [13, 14],
            [14,  8],
            [14, 15],
            [15,  9],
            [ 9,  8],
            [10, 16],
            [16, 17],
            [17, 11],
            [17, 18],
            [18, 12],
            [18, 19],
            [19, 13],
            [19, 20],
            [20, 14],
            [20, 21],
            [21, 15],
            [16, 22],
            [22, 23],
            [23, 17],
            [23, 24],
            [24, 18],
            [24, 25],
            [25, 19],
            [25, 26],
            [26, 20],
            [26, 27],
            [27, 21],
            [23, 28],
            [28, 29],
            [29, 24],
            [29, 30],
            [30, 25],
            [30, 31],
            [31, 26]], dtype=np.int32),
        mesh2d_face_x=np.asarray([ 50.0, 50.0, 50.0, 150.0, 150.0, 150.0, 150.0, 150.0, 250.0, 250.0, 250.0, 250.0, 250.0, 350.0, 350.0, 350.0, 350.0, 350.0, 450.0, 450.0, 450.0, ]),
        mesh2d_face_y=np.asarray([250.0, 350.0, 450.0, 150.0, 250.0, 350.0, 450.0, 550.0, 150.0, 250.0, 350.0, 450.0, 550.0, 150.0, 250.0, 350.0, 450.0, 550.0, 250.0, 350.0, 450.0, ]),
        mesh2d_face_z=np.asarray([], dtype=np.float64),
        mesh2d_face_nodes=np.asarray(
            [
                [0, 5, 6, 1],
                [1, 6, 7, 2],
                [2, 7, 8, 3],
                [4, 10, 11, 5],
                [5, 11, 12, 6],
                [6, 12, 13, 7],
                [7, 13, 14, 8],
                [8, 14, 15, 9],
                [10, 16, 17, 11],
                [11, 17, 18, 12],
                [12, 18, 19, 13],
                [13, 19, 20, 14],
                [14, 20, 21, 15],
                [16, 22, 23, 17],
                [17, 23, 24, 18],
                [18, 24, 25, 19],
                [19, 25, 26, 20],
                [20, 26, 27, 21],
                [23, 28, 29, 24],
                [24, 29, 30, 25],
                [25, 30, 31, 26],
            ],
            dtype=np.int32,
        ),
        # fmt: on

        assert np.array_equiv(mesh.mesh2d_node_x, mesh2d_node_x)
        assert np.array_equiv(mesh.mesh2d_node_y, mesh2d_node_y)
        assert np.array_equiv(mesh.mesh2d_node_z, mesh2d_node_z)

        assert np.array_equiv(mesh.mesh2d_edge_x, mesh2d_edge_x)
        assert np.array_equiv(mesh.mesh2d_edge_y, mesh2d_edge_y)
        assert np.array_equiv(mesh.mesh2d_edge_z, mesh2d_edge_z)
        assert np.array_equiv(mesh.mesh2d_edge_nodes, mesh2d_edge_nodes)

        assert np.array_equiv(mesh.mesh2d_face_x, mesh2d_face_x)
        assert np.array_equiv(mesh.mesh2d_face_y, mesh2d_face_y)
        assert np.array_equiv(mesh.mesh2d_face_z, mesh2d_face_z)
        assert np.array_equiv(mesh.mesh2d_face_nodes, mesh2d_face_nodes)


class TestNCExplorer:
    mesh2d_file = test_input_dir / "ugrid_files" / "mesh2d_net.nc"

    def test_load_ugrid_json(self):
        path = Path(__file__).parent.parent.parent.joinpath(
            "hydrolib/core/io/net/ugrid_conventions.json"
        )
        assert path.exists()

        with path.open() as f:
            conventions = json.load(f)

        # Check if the format is as expected
        for _, dct in conventions.items():
            assert isinstance(dct, dict)

            for _, values in dct.items():
                assert isinstance(values, dict)
                assert "suffices" in values
                assert isinstance(values["suffices"], List)

    @pytest.mark.parametrize(
        "file_path,network1d_dict,mesh1d_dict,mesh2d_dict,link1d2d_dict",
        [
            (
                test_input_dir / "ugrid_files" / "mesh2d_net.nc",
                None,
                None,
                {
                    "mesh2d_node_x": "mesh2d_node_x",
                    "mesh2d_node_y": "mesh2d_node_y",
                    "mesh2d_node_z": "mesh2d_node_z",
                    "mesh2d_edge_nodes": "mesh2d_edge_nodes",
                    "mesh2d_face_x": "mesh2d_face_x",
                    "mesh2d_face_y": "mesh2d_face_y",
                    "mesh2d_face_nodes": "mesh2d_face_nodes",
                },
                None,
            ),
            (
                test_input_dir
                / "e02/f101_1D-boundaries/c01_steady-state-flow/Boundary_net.nc",
                {
                    "network1d_node_id": "network1d_node_ids",
                    "network1d_node_long_name": "network1d_node_long_names",
                    "network1d_node_x": "network1d_node_x",
                    "network1d_node_y": "network1d_node_y",
                    "network1d_branch_id": "network1d_branch_ids",
                    "network1d_branch_long_name": "network1d_branch_long_names",
                    "network1d_branch_length": "network1d_edge_length",
                    "network1d_branch_order": "network1d_branch_order",
                    "network1d_edge_nodes": "network1d_edge_nodes",
                    "network1d_geom_x": "network1d_geom_x",
                    "network1d_geom_y": "network1d_geom_y",
                    "network1d_part_node_count": "network1d_geom_node_count",
                },
                {
                    "mesh1d_node_id": "mesh1d_node_ids",
                    "mesh1d_node_long_name": "mesh1d_node_long_names",
                    "mesh1d_edge_nodes": "mesh1d_edge_nodes",
                    "mesh1d_node_branch_id": "mesh1d_node_branch_id",
                    "mesh1d_node_branch_offset": "mesh1d_node_branch_offset",
                    "mesh1d_edge_branch_id": "mesh1d_edge_branch_id",
                    "mesh1d_edge_branch_offset": "mesh1d_edge_branch_offset",
                },
                None,
                None,
            ),
            (
                test_input_dir
                / "e02/c11_korte-woerden-1d/dimr_model/dflowfm/FlowFM_net.nc",
                {
                    "network1d_node_id": "network_node_id",
                    "network1d_node_long_name": "network_node_long_name",
                    "network1d_node_x": "network_node_x",
                    "network1d_node_y": "network_node_y",
                    "network1d_branch_id": "network_branch_id",
                    "network1d_branch_long_name": "network_branch_long_name",
                    "network1d_branch_length": "network_edge_length",
                    "network1d_branch_order": "network_branch_order",
                    "network1d_edge_nodes": "network_edge_nodes",
                    "network1d_geom_x": "network_geom_x",
                    "network1d_geom_y": "network_geom_y",
                    "network1d_part_node_count": "network_geom_node_count",
                },
                {
                    "mesh1d_node_id": "mesh1d_node_id",
                    "mesh1d_node_long_name": "mesh1d_node_long_name",
                    "mesh1d_edge_nodes": "mesh1d_edge_nodes",
                    "mesh1d_node_branch_id": "mesh1d_node_branch",
                    "mesh1d_node_branch_offset": "mesh1d_node_offset",
                    "mesh1d_edge_branch_id": "mesh1d_edge_branch",
                    "mesh1d_edge_branch_offset": "mesh1d_edge_offset",
                },
                None,
                None,
            ),
        ],
    )
    def test_from_file_expected_results(
        self,
        file_path: Path,
        network1d_dict: Optional[Dict[str, str]],
        mesh1d_dict: Optional[Dict[str, str]],
        mesh2d_dict: Optional[Dict[str, str]],
        link1d2d_dict: Optional[Dict[str, str]],
    ):
        explorer = NCExplorer.from_file_path(file_path)

        assert explorer.network1d_var_name_mapping == network1d_dict
        assert explorer.mesh1d_var_name_mapping == mesh1d_dict
        assert explorer.mesh2d_var_name_mapping == mesh2d_dict
        assert explorer.link1d2d_var_name_mapping == link1d2d_dict
