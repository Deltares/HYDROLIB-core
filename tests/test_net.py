from pathlib import Path

import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np
from numpy.lib.arraysetops import isin
import pytest
from meshkernel import GeometryList, MeshKernel

import os
import json

from hydrolib.core.io.net.models import Mesh2d, Mesh1d, Network


def test_create_1d_by_branch():
    pass


def test_create_1d_2d_1d2d():
    pass


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

    mesh2d_output.node_x.size == 114
    mesh2d_output.edge_nodes.size == 426

    # fig, ax = plt.subplots()
    # ax.set_aspect(1.0)
    # mesh2d_output.plot_edges(ax=ax)
    # ax.plot(polygon.x_coordinates, polygon.y_coordinates)
    # plt.show()


currentdir = Path(__file__).parent
cases = [
    currentdir.joinpath("data/input/e02/f101_1D-boundaries/c01_steady-state-flow/Boundary_net.nc"),
    currentdir.joinpath("data/input/e02/c11_korte-woerden-1d/dimr_model/dflowfm/FlowFM_net.nc"),
    Path(r"d:\Documents\4390.10 TKI Hydrolib\data\FlowFM_net.nc"),
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

    # fig, ax = plt.subplots()
    # ax.set_aspect(1.0)
    # network.plot(ax=ax)
    # ax.autoscale()
    # plt.show()


def test_load_ugrid_json():

    path = Path(__file__).parent.parent.joinpath("hydrolib/core/io/net/ugrid_conventions.json")
    assert path.exists()

    # Read the key conventions from json, based on nc version number
    with open(path, "r") as f:
        conventions = json.load(f)

    # Check if the format is as expected
    for _, dct in conventions.items():
        assert isinstance(dct, dict)
        for _, values in dct.items():
            assert isinstance(values, list)


@pytest.mark.parametrize(
    "filepath",
    cases,
)
def test_read_write_read_compare(filepath):

    # TODO: Running these test multiple times does not always work. Maybe write to memory?

    # Get nc file path
    assert filepath.exists()

    # Create network model
    network1 = Network.from_file(filepath)

    # Save to temporary location
    tmppath = Path("test.nc")
    tmppath.unlink()
    network1.to_file(tmppath)

    # Read a second network from thiWs location
    network2 = Network.from_file(tmppath)

    # Read keys from convention
    path = Path(__file__).parent.parent.joinpath("hydrolib/core/io/net/ugrid_conventions.json")
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


# def test_create_1d2d_net():

#     # Create 2D mesh


#     # Create 1D branch


#     # Discretize branch


#     pass
