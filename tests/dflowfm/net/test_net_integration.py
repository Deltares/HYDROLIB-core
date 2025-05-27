import numpy as np
from hydrolib.core.dflowfm.mdu.models import FMModel
from hydrolib.core.dflowfm.net.models import Branch
from meshkernel import GeometryList


def test_add_short_connecting_branch():
    fmmodel = FMModel()

    network = fmmodel.geometry.netfile.network

    lowerbranch = Branch(geometry=np.array([[-100, -25], [0, -25]]))
    upperbranch = Branch(geometry=np.array([[-100, 25], [0, 25]]))
    connectingbranch = Branch(geometry=np.array([[0, -25], [0, 25]]))

    branches = [lowerbranch, upperbranch, connectingbranch]
    for branch in branches:
        branch.generate_nodes(mesh1d_edge_length=50)
        network.mesh1d_add_branch(branch)

    assert np.array_equiv(
        network._mesh1d.mesh1d_node_x,
        np.array([-100.0, -50.0, 0.0, -100.0, -50.0, 0.0, 0.0]),
    )
    assert np.array_equiv(
        network._mesh1d.mesh1d_node_y,
        np.array([-25.0, -25.0, -25.0, 25.0, 25.0, 25.0, 0.0]),
    )

def test_create_triangular():

    fmmodel = FMModel()

    network = fmmodel.geometry.netfile.network

    polygon = GeometryList(
        x_coordinates=np.array([0.0, 6.0, 4.0, 2.0, 0.0]),
        y_coordinates=np.array([0.0, 2.0, 7.0, 6.0, 0.0]),
    )

    network.mesh2d_create_triangular_within_polygon(polygon)

    assert np.array_equiv(
        network._mesh2d.mesh2d_node_x,
        np.array([6.0, 4.0, 2.0, 0.0]),
    )
    assert np.array_equiv(
        network._mesh2d.mesh2d_node_y,
        np.array([2.0, 7.0, 6.0, 0.0]),
    )
    assert np.array_equiv(
        network._mesh2d.mesh2d_edge_nodes,
        np.array([[2, 3], [3, 0], [0, 2], [0, 1], [1, 2]]),
    )

