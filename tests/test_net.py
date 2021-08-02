from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
from meshkernel import GeometryList, MeshKernel

import json

from hydrolib.core.io.net.models import Mesh2d, Mesh1d, Network, Branch
from .utils import test_output_dir, test_input_dir


def plot_network(network):
    _, ax = plt.subplots()
    ax.set_aspect(1.0)
    network.plot(ax=ax)
    ax.autoscale()
    plt.show()


@pytest.mark.manualtest
def test_create_1d_by_branch():

    # Define line
    x = np.linspace(0, 4 * np.pi, 1000)
    y = np.sin(x)

    # Create branch
    branch = Branch(geometry=np.stack([x, y], axis=1))
    # Generate nodes on branch
    branch.generate_nodes(mesh1d_edge_length=1)
    # Create Mesh1d
    network = Network()
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
    network.to_file(test_output_dir / "test_net.nc")


def get_circle_gl(r, detail=100):

    t = np.r_[np.linspace(0, 2 * np.pi, detail), 0]
    polygon = GeometryList(np.cos(t) * r, np.sin(t) * r)
    return polygon


@pytest.mark.manualtest
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
    network = Network()
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
    network.to_file(test_output_dir / "test_net.nc")

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
    network = Network.from_file(filepath)


def test_load_ugrid_json():

    path = Path(__file__).parent.parent.joinpath(
        "hydrolib/core/io/net/ugrid_conventions.json"
    )
    assert path.exists()

    # Read the key conventions from json, based on nc version number
    with open(path, "r") as f:
        conventions = json.load(f)

    # Check if the format is as expected
    for _, dct in conventions.items():
        assert isinstance(dct, dict)
        for _, values in dct.items():
            assert isinstance(values, list)


@pytest.mark.parametrize("filepath", cases)
def test_read_write_read_compare(filepath):

    # TODO: Running these test multiple times does not always work. Maybe write to memory?

    # Get nc file path
    assert filepath.exists()

    # Create network model
    network1 = Network.from_file(filepath)

    # Save to temporary location
    tmppath = test_output_dir / "test_net.nc"
    tmppath.unlink()
    network1.to_file(tmppath)

    # Read a second network from thiWs location
    network2 = Network.from_file(tmppath)

    # Read keys from convention
    path = Path(__file__).parent.parent.joinpath(
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
