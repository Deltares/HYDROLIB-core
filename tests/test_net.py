import meshkernel

import sys

sys.path.append("d:/Documents/GitHub/HYDROLIB-core")

from hydrolib.core.models import net
from meshkernel import GeometryList, MeshKernel
import numpy as np
import matplotlib.pyplot as plt


def test_create_2d():

    # Define polygon
    bbox = (1.0, -2.0, 3.0, 4.0)

    mesh2d = net.Mesh2d(meshkernel=MeshKernel())
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
    mesh2d = net.Mesh2d(meshkernel=MeshKernel())
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
    mesh2d = net.Mesh2d(meshkernel=MeshKernel())
    # Create within bounding box
    mesh2d.create_rectilinear(extent=bbox, dx=0.5, dy=0.75)
    # Refine
    mesh2d.refine(polygon, 1)

    mesh2d_output = mesh2d.get_mesh2d()

    mesh2d_output.node_x.size == 114
    mesh2d_output.edge_nodes.size == 426

    # fig, ax = plt.subplots()
    # mesh2d_output.plot_edges(ax=ax)
    # ax.plot(polygon.x_coordinates, polygon.y_coordinates)
    # plt.show()


# def test_create_1d2d_net():

#     # Create 2D mesh


#     # Create 1D branch


#     # Discretize branch


#     pass


if __name__ == "__main__":
    test_create_2d()
    test_create_clip_2d()
    test_create_refine_2d()
