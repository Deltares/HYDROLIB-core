from typing import Union
from meshkernel.meshkernel import MeshKernel
from meshkernel.py_structures import GeometryList

import numpy as np
import meshkernel
from numpy.lib.arraysetops import isin

from rtree import index

from hydrolib.core.io.netcdf import IONetCDF


def split_by(gl: GeometryList, by: float) -> list:
    splitidx = np.full(len(gl.x_coordinates), False)
    x, y = gl.x_coordinates.copy(), gl.y_coordinates.copy()
    idx = np.where(x == by)[0]

    xparts = np.split(x, idx)
    yparts = np.split(y, idx)

    lists = [GeometryList(xp[min(i, 1) :], yp[min(i, 1) :]) for i, (xp, yp) in enumerate(zip(xparts, yparts))]

    return lists


class Network:
    """Could be based on the Network filemodel? Or separate?"""

    def __init__(self) -> None:
        self._mk = meshkernel.MeshKernel()
        # Seperate class to 
        self.mesh1d = Mesh1D(mk=self._mk)
        self.mesh2d = Mesh2D(mk=self._mk)
        self.links1d2d = Links1D2D(mk=self._mk)

        # Spatial index (rtree)
        self.idx = index.Index()

        # Object for reading and writing a network from NetCDF
        self.netcdfio = IONetCDF()
    
    def add_branch(self, id: str, name: str, x_coordinates: np.ndarray, y_coordinates: np.ndarray) -> None:

        # Create branch
        branch = Branch(*args)
        # Add to spatial index? 
        self.idx.insert(id=id, bounds=branch._bbox, obj=branch)
    
    def get_branch(self, id:str) -> Branch:
        # Get branch object from spatial index by id
        branch = ...
        return branch

    def create_1d_mesh(self, mesh1d_options: IntEnum) -> None:
        pass



class Spatial:
    """Parent class for all objects that will be part of the spatial index?
    """

    ...

    def create_spatial_index(self)


class Branch(Spatial):
    """Separate object for a branch. It is the only part of the mesh that needs a different object

    Args:
        Spatial ([type]): [description]
    """
    # Use other non conflicting name than 'id', similar to i.e. structures
    id: str
    name: str
    x_coordinates: np.ndarray
    y_coordinates: np.ndarray
    _bbox: tuple


class Mesh1D:
    def __init__(self, mk) -> None:
        self._mk = mk

        # Has a list of branches
        self._branches = []

    def generate_1d_network(self, node_distance: float) -> None:
        pass


class Mesh2D:
    """
    Mesh2D class. Based largely on the MeshKernel class.
    """
    def __init__(self) -> None:
        self._mk = mk

    def create_triangular(self, polygon: GeometryList, mesh2d_triangular_options: IntEnum) -> None:
        """Creates a 2d mesh within a polygon."""
        pass


    def create_rectilinear(self, polygon: GeometryList, dx: float, dy: float) -> None:
        """Create a rectilinear mesh within a polygon. A rectangular grid is generated within the polygon bounds

        Args:
            polygon (GeometryList): Polygon from which the bounds are used
            dx (float): Horizontal distance
            dy (float): Vertical distance

        TODO: Perhaps the polygon processing part should be part of Hydrolib (not core)!

        Raises:
            NotImplementedError: MultiPolygons
        """

        if -999.0 in polygon.x_coordinates:
            raise NotImplementedError("GeometryLists with multiple parts (MultiPolygons) are not supported.")

        # Determine origin, number of rows and number of columns
        idx = (polygon.x_coordinates != polygon.geometry_separator) & (
            polygon.x_coordinates != polygon.inner_outer_separator
        )
        xmin = polygon.x_coordinates[idx].min()
        xmax = polygon.x_coordinates[idx].max()
        ymin = polygon.y_coordinates[idx].min()
        ymax = polygon.y_coordinates[idx].max()

        # Generate mesh
        mesh2d_input = meshkernel.Mesh2dFactory.create_rectilinear_mesh(
            rows=int((ymax - ymin) / dy),
            columns=int((xmax - xmin) / dx),
            origin_x=xmin,
            origin_y=ymin,
            spacing_x=dx,
            spacing_y=dy,
        )
        self._mk.mesh2d_set(mesh2d_input)

    def clip(self, polygon: GeometryList, deletemeshoption: int=1):
        """Clip the 2D mesh by a polygon. Both outside the exterior and inside the interiors is clipped

        TODO: Or use option classes from MeshKernel in some way

        Args:
            polygon (GeometryList): Polygon stored as GeometryList
            deletemeshoption (int, optional): [description]. Defaults to 1.
        """

        # Delete outside polygon
        deletemeshoption = meshkernel.DeleteMeshOption(deletemeshoption)
        parts = split_by(polygon, -998.0)
        self._mk.mesh2d_delete(parts[0], deletemeshoption, True)

        # Delete all holes
        for interior in parts[1:]:
            self._mk.mesh2d_delete(interior, deletemeshoption, False)

    def refine(self, polygon: GeometryList, level: int):
        """Refine the mesh within a polygon, by a number of steps (level)

        Args:
            polygon (GeometryList): Polygon in which to refine
            level (int): Number of refinement steps
        """
        parameters = meshkernel.MeshRefinementParameters(
            refine_intersected=True,
            use_mass_center_when_refining=False,
            min_face_size=10.0,  # Does nothing?
            refinement_type=1,
            connect_hanging_nodes=True,
            account_for_samples_outside_face=False,
            max_refinement_iterations=level,
        )
        self._mk.mesh2d_refine_based_on_polygon(polygon, parameters)

    def get_mesh2d_output(self) -> meshkernel.Mesh2d:
        return self._mk.mesh2d_get()

    def remove_within_polygon(self, polygon: meshkernel.GeometryList, inverse: bool = False) -> None:
        pass


class Links1D2D:
    def __init__(self) -> None:
        self._mk = mk

        """
        5 different mesh kernel functions to facilitate the connecting, test them, see how to call them from here.
        Could be a seperate functions, or a single function with a Parameter class if more logical.
        """
        # Computes Mesh1d-Mesh2d contacts, where each single Mesh1d node is connected to one Mesh2d face circumcenter.
        # The boundary nodes of Mesh1d (those sharing only one Mesh1d edge) are not connected to any Mesh2d face.
        contacts_compute_single(self, node_mask, polygons)

        # Computes Mesh1d-Mesh2d contacts, where a single Mesh1d node is connected to multiple Mesh2d face circumcenters.
        contacts_compute_multiple(self, node_mask)

        # Computes Mesh1d-Mesh2d contacts, where a Mesh2d face per polygon is connected to the closest Mesh1d node.
        contacts_compute_with_polygons(self, node_mask, polygons)

        # Computes Mesh1d-Mesh2d contacts, where Mesh1d nodes are connected to the Mesh2d face mass centers containing the input point.
        contacts_compute_with_points(self, node_mask, points)

        # Computes Mesh1d-Mesh2d contacts, where Mesh1d nodes are connected to the closest Mesh2d faces at the boundary
        contacts_compute_boundary(self, node_mask, polygons, search_radius)

        pass
