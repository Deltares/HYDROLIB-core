from __future__ import annotations
from hydrolib.core.mesh import Links1D2D, Mesh2D

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
        """Return mesh2d from meshkernel"""
        return self.meshkernel.mesh2d_get()

    def read_file(self, file: Path) -> None:

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


class Branch:

    # geometry: np.full(0, dtype=np.double)
    # branchoffsets: np.full(0, dtype=np.double)

    def __init__(self, geometry: np.ndarray, branch_offsets: np.ndarray = None) -> None:

        # Check that the array has two collumns (x and y)
        assert geometry.shape[1] == 2
        # Split in x and y
        self.geometry = geometry
        self._x_coordinates = geometry[:, 0]
        self._y_coordinates = geometry[:, 1]

        if self.branch_offsets is None:
            self.branch_offsets = np.full(0, np.double)
        else:
            self.branch_offsets = branch_offsets

        # Calculate distance of coordinates along line
        segment_distances = np.hypot(np.diff(self._x_coordinates), np.diff(self._y_coordinates))
        self._distance = np.cumsum(np.concatenate([[0], segment_distances]))
        self.length = self._distance[-1]

    def set_branch_offsets(self, branch_offsets: np.ndarray) -> None:
        """Set offets for nodes on branch"""
        self.branch_offsets.resize(len(branch_offsets), refcheck=False)
        self.branch_offsets[:] = branch_offsets

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


class Mesh1d:
    """Inherits from mk.Mesh1d, but adds some additional attributes
    from the netcdf"""

    def __init__(self, meshkernel: mk.MeshKernel) -> None:
        self.meshkernel = meshkernel
        self.branches = {}

    def get_mesh1d(self) -> mk.Mesh1d:
        """Return mesh1d from meshkernel"""
        return self.meshkernel.mesh1d_get()

    def read_file(self, file: Path) -> Mesh1d:
        """
        Determine x, y locations of 1d network
        """
        # Check if path exists
        if not file.exists():
            raise OSError(f'Path "{file.resolve()}" does not exist.')

        ds = nc.Dataset(file)

        self.branches.clear()

        # Read network geometry nodes.
        branch_node_count = ds["network_part_node_count"][:].data
        branch_id = nc.chartostring(ds["network_branch_ids"][:].data)

        # Create a list of coordinates to create the branches from
        ngeom = list(zip(ds["network_geom_x"][:], ds["network_geom_y"][:]))

        # These determine the position of the nodes
        branchids = ds["mesh1d_nodes_branch_id"][:].data
        offsets = ds["mesh1d_nodes_branch_offset"][:].data

        # Collect branches
        total_crds = []

        for i, (name, nnodes) in enumerate(zip(branch_id, branch_node_count)):

            # Create network branch
            geometry = np.array([ngeom.pop(0) for _ in range(nnodes)])
            geo_branch = Branch(geometry)

            # Determine mesh node position on network branch
            branchoffsets = offsets[branchids == (i + 1)]
            meshcrds = geo_branch.interpolate(branchoffsets)
            geo_branch.set_branch_offsets(branchoffsets)
            self.branches[name.strip()] = geo_branch

            # Add the mesh coordinates to the total list of coordinates
            total_crds.append(meshcrds)

            # Determine if a start or end coordinate needs to be added for constructing a complete LineString
            if not np.isclose(branchoffsets[0], 0.0):
                meshcrds = np.insert(meshcrds, 0, geo_branch.coordinates[[0]], axis=0)
            if not np.isclose(branchoffsets[-1], geo_branch.length):
                meshcrds = np.append(meshcrds, geo_branch.coordinates[[-1]], axis=0)
            self.sch_branches[name.strip()] = Branch(meshcrds)

        # Convert list with all coordinates (except the appended ones for the schematized branches) to arrays
        node_x, node_y = np.vstack(total_crds).T
        # Create 1d mesh from nodes and edges (to be read)
        edge_nodes = ds["mesh1d_edge_nodes"][:].ravel() - 1
        ds.close()
        # Create 1d mesh from nodes and edges
        mesh1d = mk.Mesh1d(node_x=node_x.copy(), node_y=node_y.copy(), edge_nodes=edge_nodes.copy())

        # Add to meshkernel
        self.meshkernel.mesh1d_set(mesh1d)

        return mesh1d

    def get_node_mask(self, branchids=List[str]):
        """Get node mask, give a mask with True for each node that is in the given branchid list"""

        mesh1d = self.get_mesh1d()

        mask = np.full(mesh1d.node_x.size, False, dtype=bool)

        for branchid in branchids:

            branch = self.branches[branchid]
            # branch.

            # self.


class Links1D2D:
    def __init__(self, meshkernel: mk.MeshKernel) -> None:
        self.meshkernel = meshkernel

        """
        MeshKernelPy facilitaties 5 different functions to connect 1d and 2d.
        """

    def link_from_1d_to_2d(self, branchids: List[str] = None, polygon: mk.GeometryList = None):
        """Connect 1d nodes to 2d face circumcenters. A list of branchid's can be given
        to indicate where the connections should be made.

        Args:
            polygon (mk.GeometryList): [description]
            branchid (str, optional): [description]. Defaults to None.
        """

        # Computes Mesh1d-Mesh2d contacts, where each single Mesh1d node is connected to one Mesh2d face circumcenter.
        # The boundary nodes of Mesh1d (those sharing only one Mesh1d edge) are not connected to any Mesh2d face.

        # Get 1d node mask
        pass
        # if branchids is None:

        # self.meshkernel.contacts_compute_single(self, node_mask, polygons)

        # # Note that the function "contacts_compute_multiple" also computes the connections, but does not take into account
        # # a bounding polygon or the end points of the 1d mesh.
        # # self._mk.contacts_compute_multiple(self, node_mask)

        # # Computes Mesh1d-Mesh2d contacts, where a Mesh2d face per polygon is connected to the closest Mesh1d node.
        # self._mk.contacts_compute_with_polygons(self, node_mask, polygons)

        # # Computes Mesh1d-Mesh2d contacts, where Mesh1d nodes are connected to the Mesh2d face mass centers containing the input point.
        # self._mk.contacts_compute_with_points(self, node_mask, points)

        # # Computes Mesh1d-Mesh2d contacts, where Mesh1d nodes are connected to the closest Mesh2d faces at the boundary
        # self._mk.contacts_compute_boundary(self, node_mask, polygons, search_radius)

        # pass


class Network:
    """Could be based on the Network filemodel? Or separate?"""

    def __init__(self) -> None:
        self.meshkernel = mk.MeshKernel()

        self.mesh1d = Mesh1d(meshkernel=self.meshkernel)
        self.mesh2d = Mesh2d(meshkernel=self.meshkernel)
        self.links1d2d = Links1d2d(meshkernel=self.meshkernel)

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
