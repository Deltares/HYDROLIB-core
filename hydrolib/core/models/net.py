from __future__ import annotations

from pathlib import Path
from typing import Union

import meshkernel as mk
import netCDF4 as nc
import numpy as np
from matplotlib.collections import LineCollection
import matplotlib.pyplot as plt
import matplotlib
from rtree import index

from hydrolib.core.basemodel import BaseModel


def split_by(gl: mk.GeometryList, by: float) -> list:
    """Function to split mk.GeometryList by seperator."""
    splitidx = np.full(len(gl.x_coordinates), False)
    x, y = gl.x_coordinates.copy(), gl.y_coordinates.copy()
    idx = np.where(x == by)[0]

    xparts = np.split(x, idx)
    yparts = np.split(y, idx)

    lists = [mk.GeometryList(xp[min(i, 1) :], yp[min(i, 1) :]) for i, (xp, yp) in enumerate(zip(xparts, yparts))]

    return lists


class Mesh2d:
    """Inherits from mk.Mesh2d, but adds some additional attributes
    from the netcdf"""

    def __init__(self, meshkernel: mk.MeshKernel) -> None:
        self.meshkernel = meshkernel

        self._node_z: np.ndarray = np.empty(0, dtype=np.double)
        self._face_z: np.ndarray = np.empty(0, dtype=np.double)
        self._edge_types: np.ndarray = np.empty(0, dtype=np.int32)

    def get_mesh2d(self) -> mk.Mesh2d:

        return self.meshkernel.mesh2d_get()

    def from_file(self, file: Path) -> None:

        ds = nc.Dataset(file)

        # Initiate 2d mesh with mandatory variables
        mesh2d = Mesh2d(
            node_x=ds["mesh2d_node_x"][:].data,
            node_y=ds["mesh2d_node_y"][:].data,
            edge_nodes=ds["mesh2d_edge_nodes"][:].data.ravel() - 1,
        )

        # Read other variables
        mesh2d.edge_x = ds["mesh2d_edge_x"][:].data
        mesh2d.edge_y = ds["mesh2d_edge_y"][:].data
        mesh2d.face_x = ds["mesh2d_face_x"][:].data
        mesh2d.face_y = ds["mesh2d_face_y"][:].data

        # Calculate number of nodes per face based on fillvalue
        # TODO: check how mixed meshes are stored by meshkernel (tri's and quads)
        face_nodes = ds.variables["mesh2d_face_nodes"]
        idx = face_nodes[:] != face_nodes._FillValue
        mesh2d.nodes_per_face = idx.sum(axis=1)
        mesh2d.face_nodes = face_nodes[:].data[idx] - 1

        ds.close()

        self.meshkernel.mesh2d_set(mesh2d)

    # def create_triangular(self, polygon: mk.GeometryList, mesh2d_triangular_options: IntEnum) -> None:
    #     """Creates a 2d mesh within a polygon."""
    #     pass

    def create_rectilinear(self, extent: tuple, dx: float, dy: float) -> None:
        """Create a rectilinear mesh within a polygon. A rectangular grid is generated within the polygon bounds

        Args:
            extent (tuple): Bounding box of mesh (left, bottom, right, top)
            dx (float): Horizontal distance
            dy (float): Vertical distance

        TODO: Perhaps the polygon processing part should be part of Hydrolib (not core)!

        Raises:
            NotImplementedError: MultiPolygons
        """

        xmin, ymin, xmax, ymax = extent

        # Generate mesh
        mesh2d_input = mk.Mesh2dFactory.create_rectilinear_mesh(
            rows=int((ymax - ymin) / dy),
            columns=int((xmax - xmin) / dx),
            origin_x=xmin,
            origin_y=ymin,
            spacing_x=dx,
            spacing_y=dy,
        )

        self.meshkernel.mesh2d_set(mesh2d_input)

    def clip(self, polygon: mk.GeometryList, deletemeshoption: int = 1):
        """Clip the 2D mesh by a polygon. Both outside the exterior and inside the interiors is clipped

        Args:
            polygon (GeometryList): Polygon stored as GeometryList
            deletemeshoption (int, optional): [description]. Defaults to 1.
        """

        # Delete outside polygon
        deletemeshoption = mk.DeleteMeshOption(deletemeshoption)
        parts = split_by(polygon, -998.0)

        # Check if parts are closed
        for part in parts:
            if not (part.x_coordinates[0], part.y_coordinates[0]) == (part.x_coordinates[-1], part.y_coordinates[-1]):
                raise ValueError("First and last coordinate of each GeometryList part should match.")

        self.meshkernel.mesh2d_delete(parts[0], deletemeshoption, True)

        # Delete all holes
        for interior in parts[1:]:
            self.meshkernel.mesh2d_delete(interior, deletemeshoption, False)

    def refine(self, polygon: mk.GeometryList, level: int):
        """Refine the mesh within a polygon, by a number of steps (level)

        Args:
            polygon (GeometryList): Polygon in which to refine
            level (int): Number of refinement steps
        """
        # Check if parts are closed
        if not (polygon.x_coordinates[0], polygon.y_coordinates[0]) == (
            polygon.x_coordinates[-1],
            polygon.y_coordinates[-1],
        ):
            raise ValueError("First and last coordinate of each GeometryList part should match.")

        parameters = mk.MeshRefinementParameters(
            refine_intersected=True,
            use_mass_center_when_refining=False,
            min_face_size=10.0,  # Does nothing?
            refinement_type=1,
            connect_hanging_nodes=True,
            account_for_samples_outside_face=False,
            max_refinement_iterations=level,
        )
        self.meshkernel.mesh2d_refine_based_on_polygon(polygon, parameters)


class Mesh1d:
    """Inherits from mk.Mesh1d, but adds some additional attributes
    from the netcdf"""

    def __init__(self, meshkernel: mk.MeshKernel) -> None:
        self.meshkernel = meshkernel

    def from_file(self, file: Path, network: Network) -> Mesh1d:
        """
        Determine x, y locations of 1d network
        """
        # Check if path exists
        if not file.exists():
            raise OSError(f'Path "{file.resolve()}" does not exist.')

        ds = nc.Dataset(file)
        # Read coordinates from branches
        node_x, node_y = network._coordinates.T
        # Create 1d mesh from nodes and edges (to be read)
        edge_nodes = ds["mesh1d_edge_nodes"][:].ravel() - 1
        ds.close()
        # Create 1d mesh from nodes and edges
        mesh1d = mk.Mesh1d(node_x=node_x.copy(), node_y=node_y.copy(), edge_nodes=edge_nodes.copy())
        # Add to meshkernel
        self.meshkernel.mesh1d_set(mesh1d)

        return mesh1d


class Network:
    def __init__(self, geo_branches, sch_branches, coordinates):
        self._geo_branches = {}
        self._geo_branches.update(geo_branches)
        # delft3dfmpy also keeps track of the schematised branches, so not the original ones
        # but the branch that remains after nodes have been interpolated on it.
        # This is used for example when the coordinates of a structure need to be determined:
        # It is defined on the geometry branch, but needs to be placed within the nodes based
        # on the schematised branches
        self._sch_branches = {}
        self._sch_branches.update(sch_branches)

        self._coordinates = coordinates

    @classmethod
    def from_file(cls, file: Path) -> Network:
        """
        Determine x, y locations of 1d network
        """

        if not file.exists():
            raise OSError(f'Path "{file.resolve()}" does not exist.')

        ds = nc.Dataset(file)

        # Read network geometry nodes.
        # TODO: Naming: call it a part or a branch?
        branch_node_count = ds["network_part_node_count"][:].data
        branch_id = nc.chartostring(ds["network_branch_ids"][:].data)

        # Create a list of coordinates to create the branches from
        ngeom = list(zip(ds["network_geom_x"][:], ds["network_geom_y"][:]))

        # These determine the position of the nodes
        branchids = ds["mesh1d_nodes_branch_id"][:].data
        offsets = ds["mesh1d_nodes_branch_offset"][:].data

        # Collect branches
        geo_branches = {}
        sch_branches = {}
        total_crds = []

        for i, (name, nnodes) in enumerate(zip(branch_id, branch_node_count)):

            # Create network branch
            geo_branch = Branch(np.array([ngeom.pop(0) for _ in range(nnodes)]))
            geo_branches[name.strip()] = geo_branch

            # Determine mesh node position on network branch
            branchoffsets = offsets[branchids == (i + 1)]
            meshcrds = geo_branch.interpolate(branchoffsets)
            # Add the mesh coordinates to the total list of coordinates
            total_crds.append(meshcrds)

            # Determine if a start or end coordinate needs to be added for constructing a complete LineString
            if not np.isclose(branchoffsets[0], 0.0):
                meshcrds = np.insert(meshcrds, 0, geo_branch.coordinates[[0]], axis=0)
            if not np.isclose(branchoffsets[-1], geo_branch.length):
                meshcrds = np.append(meshcrds, geo_branch.coordinates[[-1]], axis=0)
            sch_branches[name.strip()] = Branch(meshcrds)

        ds.close()

        return cls(geo_branches, sch_branches, np.vstack(total_crds))


class Branch:
    def __init__(self, coordinates: np.ndarray):

        # Check that the array has two collumns (x and y)
        assert coordinates.shape[1] == 2

        self.coordinates = coordinates

        # Split in x and y
        self._x_coordinates = coordinates[:, 0]
        self._y_coordinates = coordinates[:, 1]

        # Calculate distance of coordinates along line
        segment_distances = np.hypot(np.diff(self._x_coordinates), np.diff(self._y_coordinates))
        self._distance = np.cumsum(np.concatenate([[0], segment_distances]))
        self.length = self._distance[-1]

    def interpolate(self, distance: Union[float, np.ndarray]) -> np.ndarray:
        """Interpolate coordinates along branch by length
        #TODO: How to handle these kind of union datatypes? The array should also consist of floats
        Args:
            distance (Union[float, np.ndarray]): Length
        """
        intpcoords = np.stack(
            [
                np.interp(distance, self._distance, self._x_coordinates),
                np.interp(distance, self._distance, self._y_coordinates),
            ],
            axis=1,
        )

        return intpcoords


class Mesh:
    """Could be based on the Network filemodel? Or separate?"""

    def __init__(self, mesh1d: Mesh1d, mesh2d: Mesh2d, network: Network) -> None:
        self._mk = mk.MeshKernel()

        self.mesh1d = mesh1d
        self.mesh2d = mesh2d
        self.network = network

        self._mk.mesh1d_set(mesh1d)
        self._mk.mesh2d_set(mesh2d)

        # Spatial index (rtree)
        self.idx = index.Index()

    @classmethod
    def from_file(cls, file):

        network = Network.from_file(file)
        mesh1d = Mesh1d.from_file(file, network)
        mesh2d = Mesh2d.from_file(file)

        return cls(mesh1d, mesh2d, network)

    def plot(
        self,
        ax: matplotlib.axes._subplots.AxesSubplot,
        mesh1d_kwargs: dict = None,
        mesh2d_kwargs: dict = None,
        links1d2d_kwargs: dict = None,
    ) -> None:

        if mesh1d_kwargs is None:
            mesh1d_kwargs = {}
        if mesh2d_kwargs is None:
            mesh2d_kwargs = {}
        if links1d2d_kwargs is None:
            links1d2d_kwargs = {}

        # Mesh 1d
        mesh1d_output = self._mk.mesh1d_get()
        nodes1d = np.stack([mesh1d_output.node_x, mesh1d_output.node_y], axis=1)
        edge_nodes = self.mesh1d.edge_nodes.reshape((-1, 2))
        lc_mesh1d = LineCollection(nodes1d[edge_nodes], **mesh1d_kwargs)
        ax.add_collection(lc_mesh1d)

        # Mesh 2d
        mesh2d_output = self._mk.mesh2d_get()
        nodes2d = np.stack([mesh2d_output.node_x, mesh2d_output.node_y], axis=1)
        edge_nodes = self.mesh2d.edge_nodes.reshape((-1, 2))
        lc_mesh2d = LineCollection(nodes2d[edge_nodes], **mesh2d_kwargs)
        ax.add_collection(lc_mesh2d)

        # Links
        contacts = self._mk.contacts_get()
        faces2d = np.stack([mesh2d_output.face_x, mesh2d_output.face_y], axis=1)
        link_coords = np.stack([nodes1d[contacts.mesh1d_indices], faces2d[contacts.mesh2d_indices]], axis=1)
        lc_links1d2d = LineCollection(link_coords, **links1d2d_kwargs)
        ax.add_collection(lc_links1d2d)

    # def add_branch(self, id: str, name: str, x_coordinates: np.ndarray, y_coordinates: np.ndarray) -> None:

    #     # Create branch
    #     branch = Branch(*args)
    #     # Add to spatial index?
    #     self.idx.insert(id=id, bounds=branch._bbox, obj=branch)

    # def get_branch(self, id: str) -> Branch:
    #     # Get branch object from spatial index by id
    #     branch = ...
    #     return branch

    # def create_1d_mesh(self, mesh1d_options: IntEnum) -> None:
    #     pass
