from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

import meshkernel as mk
import netCDF4 as nc
import numpy as np
from pydantic import Field

from hydrolib.core import __version__
from hydrolib.core.basemodel import BaseModel
from hydrolib.core.io.net.reader import UgridReader
from hydrolib.core.io.net.writer import UgridWriter


def split_by(gl: mk.GeometryList, by: float) -> list:
    """Function to split mk.GeometryList by seperator."""
    splitidx = np.full(len(gl.x_coordinates), False)
    x, y = gl.x_coordinates.copy(), gl.y_coordinates.copy()
    idx = np.where(x == by)[0]

    xparts = np.split(x, idx)
    yparts = np.split(y, idx)

    lists = [mk.GeometryList(xp[min(i, 1) :], yp[min(i, 1) :]) for i, (xp, yp) in enumerate(zip(xparts, yparts))]

    return lists


class Mesh2d(BaseModel):

    meshkernel: Optional[mk.MeshKernel] = Field(default_factory=mk.MeshKernel)

    mesh2d_node_x: np.ndarray = np.empty(0, dtype=np.double)
    mesh2d_node_y: np.ndarray = np.empty(0, dtype=np.double)
    mesh2d_node_z: np.ndarray = np.empty(0, dtype=np.double)

    mesh2d_edge_nodes: np.ndarray = np.empty(0, dtype=np.int32)

    mesh2d_face_x: np.ndarray = np.empty(0, dtype=np.double)
    mesh2d_face_y: np.ndarray = np.empty(0, dtype=np.double)
    mesh2d_face_z: np.ndarray = np.empty(0, dtype=np.double)
    mesh2d_face_nodes: np.ndarray = np.empty(0, dtype=np.int32)

    def empty(self):
        return self.mesh2d_node_x.size == 0

    def read_file(self, file: Path) -> None:

        # Create reader and read 2d
        reader = UgridReader(file=file)
        reader.read_2d(self)

    def _set_mesh2d(self):
        # Initiate 2d mesh with mandatory variables
        mesh2d = mk.Mesh2d(
            node_x=self.mesh2d_node_x,
            node_y=self.mesh2d_node_y,
            edge_nodes=self.mesh2d_edge_nodes,
        )

        self.meshkernel.mesh2d_set(mesh2d)
        # TODO: THis might also modify the other mesh properties. Make sure to update
        # these too.

    def get_mesh2d(self) -> mk.Mesh2d:
        """Return mesh2d from meshkernel"""
        return self.meshkernel.mesh2d_get()

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
    def __init__(self, geometry: np.ndarray, branch_offsets: np.ndarray, node_ids: np.ndarray) -> None:
        # Check that the array has two collumns (x and y)
        assert geometry.shape[1] == 2

        # Split in x and y
        self.geometry = geometry
        self._x_coordinates = geometry[:, 0]
        self._y_coordinates = geometry[:, 1]

        # Calculate distance of coordinates along line
        segment_distances = np.hypot(np.diff(self._x_coordinates), np.diff(self._y_coordinates))
        self._distance = np.cumsum(np.concatenate([[0], segment_distances]))
        self.length = self._distance[-1]

        # Set branch offsets
        self.branch_offsets = branch_offsets

        # Calculate node positions
        self.nodes = self.interpolate(branch_offsets)
        self.node_ids = np.empty(0, dtype=int)

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


class Link1d2d(BaseModel):

    meshkernel: Optional[mk.MeshKernel] = Field(default_factory=mk.MeshKernel)

    link1d2d_id: np.ndarray = np.empty(0, object)
    link1d2d_long_name: np.ndarray = np.empty(0, object)

    link1d2d_contact_type: np.ndarray = np.empty(0, np.int32)

    link1d2d: np.ndarray = np.empty(0, np.int32)

    def empty(self):
        return self.link1d2d.size == 0

    def read_file(self, file: Path) -> None:

        # Create reader and read 2d
        reader = UgridReader(file=file)
        reader.read_link1d2d(self)

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


class Mesh1d(BaseModel):
    """"""

    meshkernel: mk.MeshKernel = Field(default_factory=mk.MeshKernel)

    branches: dict = {}

    network1d_node_id: np.ndarray = np.empty(0, object)
    network1d_node_long_name: np.ndarray = np.empty(0, object)
    network1d_node_x: np.ndarray = np.empty(0, np.double)
    network1d_node_y: np.ndarray = np.empty(0, np.double)
    network1d_branch_id: np.ndarray = np.empty(0, object)
    network1d_branch_long_name: np.ndarray = np.empty(0, object)
    network1d_branch_length: np.ndarray = np.empty(0, np.double)
    network1d_branch_order: np.ndarray = np.empty(0, np.int32)
    network1d_edge_nodes: np.ndarray = np.empty(0, np.int32)
    network1d_geom_x: np.ndarray = np.empty(0, np.double)
    network1d_geom_y: np.ndarray = np.empty(0, np.double)
    network1d_part_node_count: np.ndarray = np.empty(0, np.int32)

    mesh1d_node_id: np.ndarray = np.empty(0, object)
    mesh1d_node_long_name: np.ndarray = np.empty(0, object)
    mesh1d_edge_nodes: np.ndarray = np.empty(0, np.int32)
    mesh1d_nodes_branch_id: np.ndarray = np.empty(0, np.int32)
    mesh1d_nodes_branch_offset: np.ndarray = np.empty(0, np.double)

    mesh1d_node_x: np.ndarray = np.empty(0, np.int32)
    mesh1d_node_y: np.ndarray = np.empty(0, np.double)

    def empty(self):
        return self.mesh1d_node_x.size == 0

    def _get_mesh1d(self) -> mk.Mesh1d:
        """Return mesh1d from meshkernel. Note that the meshkernel.Mesh1d instance
        does not contain all mesh attributes that are contained in this class"""
        return self.meshkernel.mesh1d_get()

    def process_network1d(self):
        """
        Determine x, y locations of mesh1d nodes based on the network1d
        """
        # Create a list of coordinates to create the branches from
        ngeom = list(zip(self.network1d_geom_x, self.network1d_geom_y))

        # Collect branches
        node_id = 0

        self.branches.clear()

        for i, (name, nnodes) in enumerate(zip(self.network1d_branch_id, self.network1d_part_node_count)):

            # Create network branch
            # Get geometry of branch from network geometry
            geometry = np.array([ngeom.pop(0) for _ in range(nnodes)])
            # Get branch offsets
            idx = self.mesh1d_nodes_branch_id == i
            branch_offsets = self.mesh1d_nodes_branch_offset[idx]
            # Get node_ids
            node_ids = np.arange(node_id, node_id + len(branch_offsets) + 1)
            node_ids += len(branch_offsets)
            # Create instance of branch object and add to dictionary
            geo_branch = Branch(geometry, branch_offsets=branch_offsets, node_ids=self.mesh1d_node_id[idx])
            self.branches[name.strip()] = geo_branch

            # # Determine if a start or end coordinate needs to be added for constructing a complete LineString
            # if not np.isclose(branchoffsets[0], 0.0):
            #     meshcrds = np.insert(meshcrds, 0, geo_branch.coordinates[[0]], axis=0)
            # if not np.isclose(branchoffsets[-1], geo_branch.length):
            #     meshcrds = np.append(meshcrds, geo_branch.coordinates[[-1]], axis=0)

        # Convert list with all coordinates (except the appended ones for the schematized branches) to arrays
        node_x, node_y = np.vstack([branch.nodes for branch in self.branches.values()]).T

        # Add to variables
        self.mesh1d_node_x = node_x
        self.mesh1d_node_y = node_y

    # def get_node_mask(self, branchids=List[str]):
    #     """Get node mask, give a mask with True for each node that is in the given branchid list"""

    #     mesh1d = self.get_mesh1d()

    #     mask = np.full(mesh1d.node_x.size, False, dtype=bool)

    #     for branchid in branchids:

    #         branch = self.branches[branchid]
    # branch.

    # self.


class Network:

    """"""

    def __init__(self) -> None:
        self.meshkernel = mk.MeshKernel()

        self._mesh1d = Mesh1d(meshkernel=self.meshkernel)
        self._mesh2d = Mesh2d(meshkernel=self.meshkernel)
        self._link1d2d = Link1d2d(meshkernel=self.meshkernel)

        # Spatial index (rtree)
        # self._idx = index.Index()

    @classmethod
    def from_file(cls, file: Path) -> Network:
        """Read network from file. This classmethod checks what mesh components (mesh1d & network1d, mesh2d, link1d2d) are
        present, and loads them one by one.

        Args:
            file (Path): path to netcdf file with network data

        Returns:
            Network: The instance of the class itself that is returned
        """

        network = cls()
        ds = nc.Dataset(file)

        reader = UgridReader(file)

        if reader._explorer.mesh1d_key is not None:
            reader.read_mesh1d_network1d(network._mesh1d)

        if reader._explorer.mesh2d_key is not None:
            reader.read_mesh2d(network._mesh2d)

        if reader._explorer.link1d2d_key is not None:
            reader.read_link1d2d(network._link1d2d)

        ds.close()

        return network

    def to_file(self, file: Path) -> None:
        writer = UgridWriter()
        writer.write(self, file)

    def mesh2d_create_rectilinear_within_bounds(self, extent: tuple, dx: float, dy: float) -> None:
        self._mesh2d.create_rectilinear(extent=extent, dx=dx, dy=dy)

    def mesh2d_create_triangular_within_polygon(self, polygon: mk.GeometryList) -> None:
        raise NotImplementedError()

    def mesh2d_clip_mesh(self, polygon: mk.GeometryList, deletemeshoption: int = 1) -> None:
        self._mesh2d.clip(polygon=polygon, deletemeshoption=deletemeshoption)

    def mesh2d_refine_mesh(self, polygon: mk.GeometryList, level: int = 1) -> None:
        self._mesh2d.refine(polygon=polygon, level=level)

    def plot(
        self,
        ax: matplotlib.axes._subplots.AxesSubplot,
        mesh1d_kwargs: dict = None,
        mesh2d_kwargs: dict = None,
        links1d2d_kwargs: dict = None,
    ) -> None:

        if mesh1d_kwargs is None:
            mesh1d_kwargs = {"color": "C3", "lw": 1.0}
        if mesh2d_kwargs is None:
            mesh2d_kwargs = {"color": "C0", "lw": 0.5}
        if links1d2d_kwargs is None:
            links1d2d_kwargs = {"color": "k", "lw": 1.0}

        # Mesh 1d
        if not self._mesh1d.empty():
            nodes1d = np.stack([self._mesh1d.mesh1d_node_x, self._mesh1d.mesh1d_node_y], axis=1)
            edge_nodes = self._mesh1d.mesh1d_edge_nodes.reshape((-1, 2))
            lc_mesh1d = LineCollection(nodes1d[edge_nodes], **mesh1d_kwargs)
            ax.add_collection(lc_mesh1d)

        # Mesh 2d
        if not self._mesh2d.empty():
            nodes2d = np.stack([self._mesh2d.mesh2d_node_x, self._mesh2d.mesh2d_node_y], axis=1)
            edge_nodes = self._mesh2d.mesh2d_edge_nodes.reshape((-1, 2))
            lc_mesh2d = LineCollection(nodes2d[edge_nodes], **mesh2d_kwargs)
            ax.add_collection(lc_mesh2d)

        # Links
        if not self._link1d2d.empty():
            faces2d = np.stack([self._mesh2d.mesh2d_face_x, self._mesh2d.mesh2d_face_y], axis=1)
            link_coords = np.stack(
                [nodes1d[self._link1d2d.link1d2d[:, 0]], faces2d[self._link1d2d.link1d2d[:, 1]]], axis=1
            )
            lc_link1d2d = LineCollection(link_coords, **links1d2d_kwargs)
            ax.add_collection(lc_link1d2d)
