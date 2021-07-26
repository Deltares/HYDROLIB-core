from typing import Union
from meshkernel.meshkernel import MeshKernel
from meshkernel.py_structures import GeometryList

import numpy as np
import meshkernel
from numpy.lib.arraysetops import isin

from rtree import index

from hydrolib.core.io.net import read_1d_network, read_2d


class Mesh2D:
    """
    Mesh2D class. Based largely on the MeshKernel class.
    """

    def __init__(self, mk: meshkernel.MeshKernel) -> None:
        self._mk = mk


class Links1D2D:
    def __init__(self, mk: meshkernel.MeshKernel) -> None:
        self._mk = mk

        """
        5 different mesh kernel functions to facilitate the connecting, test them, see how to call them from here.
        Could be a seperate functions, or a single function with a Parameter class if more logical.
        """
        # Computes Mesh1d-Mesh2d contacts, where each single Mesh1d node is connected to one Mesh2d face circumcenter.
        # The boundary nodes of Mesh1d (those sharing only one Mesh1d edge) are not connected to any Mesh2d face.
        self._mk.contacts_compute_single(self, node_mask, polygons)

        # Computes Mesh1d-Mesh2d contacts, where a single Mesh1d node is connected to multiple Mesh2d face circumcenters.
        self._mk.contacts_compute_multiple(self, node_mask)

        # Computes Mesh1d-Mesh2d contacts, where a Mesh2d face per polygon is connected to the closest Mesh1d node.
        self._mk.contacts_compute_with_polygons(self, node_mask, polygons)

        # Computes Mesh1d-Mesh2d contacts, where Mesh1d nodes are connected to the Mesh2d face mass centers containing the input point.
        self._mk.contacts_compute_with_points(self, node_mask, points)

        # Computes Mesh1d-Mesh2d contacts, where Mesh1d nodes are connected to the closest Mesh2d faces at the boundary
        self._mk.contacts_compute_boundary(self, node_mask, polygons, search_radius)

        pass
