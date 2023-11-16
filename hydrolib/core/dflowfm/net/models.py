from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import meshkernel as mk
import netCDF4 as nc
import numpy as np
import numpy.typing as npt
from meshkernel.py_structures import GeometryList
from pydantic import Field

from hydrolib.core import __version__
from hydrolib.core.basemodel import (
    BaseModel,
    ModelSaveSettings,
    ParsableFileModel,
    file_load_context,
)
from hydrolib.core.dflowfm.net.reader import UgridReader
from hydrolib.core.dflowfm.net.writer import UgridWriter

logger = logging.getLogger(__name__)


def split_by(gl: mk.GeometryList, by: float) -> list:
    """Function to split mk.GeometryList by seperator.

    Args:
        gl (mk.GeometryList): The geometry list to split.
        by (float): The value by which to split the gl.

    Returns:
        list: The split lists.
    """
    x, y = gl.x_coordinates.copy(), gl.y_coordinates.copy()
    idx = np.where(x == by)[0]

    xparts = np.split(x, idx)
    yparts = np.split(y, idx)

    lists = [
        mk.GeometryList(xp[min(i, 1) :], yp[min(i, 1) :])
        for i, (xp, yp) in enumerate(zip(xparts, yparts))
    ]

    return lists


class Mesh2d(BaseModel):
    """Mesh2d defines a single two dimensional grid.

    Attributes:
        meshkernel (mk.MeshKernel):
            The meshkernel used to manimpulate this Mesh2d.
        mesh2d_node_z (np.ndarray):
            The node positions on the z-axis. Defaults to np.empty(0, dtype=np.double).
        mesh2d_face_z (np.ndarray):
            The face positions on the z-axis. Defaults to np.empty(0, dtype=np.double).
    """

    meshkernel: mk.MeshKernel = Field(default_factory=mk.MeshKernel)

    # placeholders for bathymetry
    mesh2d_node_z: np.ndarray = Field(
        default_factory=lambda: np.empty(0, dtype=np.double)
    )
    mesh2d_face_z: np.ndarray = Field(
        default_factory=lambda: np.empty(0, dtype=np.double)
    )

    @property
    def mesh2d_node_x(self) -> np.ndarray[float]:
        """The x-coordinates of the nodes in the mesh.

        Returns:
            ndarray[float]: A 1D double array describing the x-coordinates of the nodes.
        """
        return self.meshkernel.mesh2d_get().node_x

    @property
    def mesh2d_node_y(self) -> np.ndarray[float]:
        """The y-coordinates of the nodes in the mesh.

        Returns:
            ndarray[float]: A 1D double array describing the y-coordinates of the nodes.
        """
        return self.meshkernel.mesh2d_get().node_y

    @property
    def mesh2d_edge_x(self) -> np.ndarray[float]:
        """The x-coordinates of the mesh edges' middle points.

        Returns:
            ndarray[float]: A 1D double array describing x-coordinates of the mesh edges' middle points.
        """
        return self.meshkernel.mesh2d_get().edge_x

    @property
    def mesh2d_edge_y(self) -> np.ndarray[float]:
        """The y-coordinates of the mesh edges' middle points.

        Returns:
            ndarray[float]: A 1D double array describing y-coordinates of the mesh edges' middle points.
        """
        return self.meshkernel.mesh2d_get().edge_y

    @property
    def mesh2d_edge_nodes(self) -> np.ndarray[int, int]:
        """The node indices of the mesh edges.

        Returns:
            np.ndarray[int, int]: A 2D integer array (nEdges, 2) containg the two node indices for each edge.
        """
        mesh2d_output = self.meshkernel.mesh2d_get()
        edge_nodes = mesh2d_output.edge_nodes.reshape((-1, 2))
        return edge_nodes

    @property
    def mesh2d_face_x(self) -> np.ndarray[float]:
        """The x-coordinates of the mesh faces' mass centers.

        Returns:
            ndarray[float]: A 1D double array describing x-coordinates of the mesh faces' mass centers.
        """
        return self.meshkernel.mesh2d_get().face_x

    @property
    def mesh2d_face_y(self) -> np.ndarray[float]:
        """The y-coordinates of the mesh faces' mass centers.

        Returns:
            ndarray[float]: A 1D double array describing y-coordinates of the mesh faces' mass centers.
        """
        return self.meshkernel.mesh2d_get().face_y

    @property
    def mesh2d_face_nodes(self) -> np.ndarray[int, int]:
        """The node indices of the mesh faces

        Returns:
            np.ndarray[int, int]: A 2D integer array describing the nodes composing each mesh 2d face. A 2D integer array (nFaces, maxNodesPerFace) containg the node indices for each face.
        """
        mesh2d_output = self.meshkernel.mesh2d_get()
        npf = mesh2d_output.nodes_per_face
        if self.is_empty():
            return np.empty((0, 0), dtype=np.int32)
        face_node_connectivity = np.full(
            (len(mesh2d_output.face_x), max(npf)), np.iinfo(np.int32).min
        )
        idx = (
            np.ones_like(face_node_connectivity) * np.arange(max(npf))[None, :]
        ) < npf[:, None]
        face_node_connectivity[idx] = mesh2d_output.face_nodes
        return face_node_connectivity

    def is_empty(self) -> bool:
        """Determine whether this Mesh2d is empty.

        Returns:
            (bool): Whether this Mesh2d is empty.
        """
        return self.mesh2d_node_x.size == 0

    def read_file(self, file_path: Path) -> None:
        """Read the Mesh2d from the file at file_path.

        Args:
            file_path (Path): Path to the file to be read.
        """
        reader = UgridReader(file_path)
        reader.read_mesh2d(self)

    def _set_mesh2d(self, node_x, node_y, edge_nodes) -> None:
        mesh2d = mk.Mesh2d(
            node_x=node_x.astype(np.float64),
            node_y=node_y.astype(np.float64),
            edge_nodes=edge_nodes.ravel().astype(np.int32),
        )

        self.meshkernel.mesh2d_set(mesh2d)

    def get_mesh2d(self) -> mk.Mesh2d:
        """Get the mesh2d as represented in the MeshKernel

        Returns:
            (mk.Mesh2d): The mesh2d as represented in the MeshKernel
        """
        return self.meshkernel.mesh2d_get()

    def create_rectilinear(self, extent: tuple, dx: float, dy: float) -> None:
        """Create a rectilinear mesh within a polygon. A rectangular grid is generated within the polygon bounds

        Args:
            extent (tuple): Bounding box of mesh (left, bottom, right, top)
            dx (float): Horizontal distance
            dy (float): Vertical distance

        Raises:
            NotImplementedError: MultiPolygons
        """

        xmin, ymin, xmax, ymax = extent

        rows = int((ymax - ymin) / dy)
        columns = int((xmax - xmin) / dx)

        params = mk.MakeGridParameters(
            num_columns=columns,
            num_rows=rows,
            origin_x=xmin,
            origin_y=ymin,
            block_size_x=dx,
            block_size_y=dy,
        )

        mesh2d_input = self.meshkernel  # mk.MeshKernel()
        mesh2d_input.curvilinear_compute_rectangular_grid(params)
        mesh2d_input.curvilinear_convert_to_mesh2d()  # convert to ugrid/mesh2d

    def create_triangular(self, geometry_list: mk.GeometryList) -> None:
        """Create triangular grid within GeometryList object

        Args:
            geometry_list (mk.GeometryList): GeometryList represeting a polygon within which the mesh is generated.
        """
        # Call meshkernel
        self.meshkernel.mesh2d_make_triangular_mesh_from_polygon(geometry_list)

    def clip(
        self,
        geometrylist: mk.GeometryList,
        deletemeshoption: mk.DeleteMeshOption = mk.DeleteMeshOption.INSIDE_NOT_INTERSECTED,
        inside=False,
    ) -> None:
        """Clip the 2D mesh by a polygon. Both outside the exterior and inside the interiors is clipped

        Args:
            geometrylist (GeometryList): Polygon stored as GeometryList
            deletemeshoption (int, optional): [description]. Defaults to 1.
        """

        # For clipping outside
        if not inside:
            # Check if a multipolygon was provided when clipping outside
            if geometrylist.geometry_separator in geometrylist.x_coordinates:
                raise NotImplementedError(
                    "Deleting outside more than a single exterior (MultiPolygon) is not implemented."
                )

            # Get exterior and interiors
            parts = split_by(geometrylist, geometrylist.inner_outer_separator)

            exteriors = [parts[0]]
            interiors = parts[1:]

        # Inside
        else:
            # Check if any polygon contains holes, when clipping inside
            if geometrylist.inner_outer_separator in geometrylist.x_coordinates:
                raise NotImplementedError(
                    "Deleting inside a (Multi)Polygon with holes is not implemented."
                )

            # Get exterior and interiors
            parts = split_by(geometrylist, geometrylist.geometry_separator)

            exteriors = parts[:]
            interiors = []

        # Check if parts are closed
        for part in exteriors + interiors:
            if (part.x_coordinates[0], part.y_coordinates[0]) != (
                part.x_coordinates[-1],
                part.y_coordinates[-1],
            ):
                raise ValueError(
                    "First and last coordinate of each GeometryList part should match."
                )

        # Delete everything outside the (Multi)Polygon
        for exterior in exteriors:
            self.meshkernel.mesh2d_delete(
                geometry_list=exterior,
                delete_option=deletemeshoption,
                invert_deletion=not inside,
            )

        # Delete all holes.
        for interior in interiors:
            self.meshkernel.mesh2d_delete(
                geometry_list=interior,
                delete_option=deletemeshoption,
                invert_deletion=inside,
            )

    def refine(self, polygon: mk.GeometryList, level: int, min_edge_size=10.0):
        """Refine the mesh within a polygon, by a number of steps (level)

        Args:
            polygon (GeometryList): Polygon in which to refine
            level (int): Number of refinement steps
        """

        # Check if parts are closed
        # if not (polygon.x_coordinates[0], polygon.y_coordinates[0]) == (
        #     polygon.x_coordinates[-1],
        #     polygon.y_coordinates[-1],
        # ):
        #     raise ValueError("First and last coordinate of each GeometryList part should match.")

        parameters = mk.MeshRefinementParameters(
            refine_intersected=True,
            use_mass_center_when_refining=False,
            min_edge_size=min_edge_size,  # Does nothing?
            refinement_type=1,  # No effect?
            connect_hanging_nodes=True,
            account_for_samples_outside_face=False,
            max_refinement_iterations=level,
        )
        self.meshkernel.mesh2d_refine_based_on_polygon(polygon, parameters)


class Branch:
    def __init__(
        self,
        geometry: np.ndarray,
        branch_offsets: np.ndarray = None,
        mask: np.ndarray = None,
    ) -> None:
        # Check that the array has two collumns (x and y)
        assert geometry.shape[1] == 2

        # Split in x and y
        self.geometry = geometry
        self._x_coordinates = geometry[:, 0]
        self._y_coordinates = geometry[:, 1]

        # Calculate distance of coordinates along line
        segment_distances = np.hypot(
            np.diff(self._x_coordinates), np.diff(self._y_coordinates)
        )
        self._distance = np.concatenate([[0], np.cumsum(segment_distances)])
        self.length = segment_distances.sum()

        # Check if mask and branch offsets (if both given) have same shape
        if (
            mask is not None
            and branch_offsets is not None
            and branch_offsets.shape != mask.shape
        ):
            raise ValueError("Mask and branch offset have different shape.")

        # Set branch offsets
        self.branch_offsets = branch_offsets
        # Calculate node positions
        if branch_offsets is not None:
            self.node_xy = self.interpolate(branch_offsets)

        # Set which of the nodes are present
        if (mask is None) and (branch_offsets is not None):
            self.mask = np.full(branch_offsets.shape, False)
        else:
            self.mask = mask

    def generate_nodes(
        self,
        mesh1d_edge_length: float,
        structure_chainage: Optional[List[float]] = None,
        max_dist_to_struc: Optional[float] = None,
    ):
        """Generate the branch offsets and the nodes.

        Args:
            mesh1d_edge_length (float): The edge length of the 1d mesh.
            structure_chainage (Optional[List[float]], optional): A list with the structure chainages. If not specified, calculation will not take it into account. Defaults to None.
            max_dist_to_struc (Optional[float], optional): The maximum distance from a node to a structure. If not specified, calculation will not take it into account. Defaults to None.

        Raises:
            ValueError: Raised when any of the structure offsets, if specified, is smaller than zero.
            ValueError: Raised when any of the structure offsets, if specified, is greater than the branch length.
        """
        # Generate offsets
        self.branch_offsets = self._generate_offsets(
            mesh1d_edge_length, structure_chainage, max_dist_to_struc
        )
        # Calculate node positions
        self.node_xy = self.interpolate(self.branch_offsets)
        # Add mask (all False)
        self.mask = np.full(self.branch_offsets.shape, False)

    def _generate_offsets(
        self,
        mesh1d_edge_length: float,
        structure_offsets: Optional[List[float]] = None,
        max_dist_to_struc: Optional[float] = None,
    ) -> np.ndarray:
        """Generate the branch offsets.

        Args:
            mesh1d_edge_length (float): The edge length of the 1d mesh.
            structure_chainage (Optional[List[float]], optional): A list with the structure chainages. If not specified, calculation will not take it into account. Defaults to None.
            max_dist_to_struc (Optional[float], optional): The maximum distance from a node to a structure. If not specified, calculation will not take it into account. Defaults to None.

        Raises:
            ValueError: Raised when any of the structure offsets, if specified, is smaller than zero.
            ValueError: Raised when any of the structure offsets, if specified, is greater than the branch length.

        Returns:
            np.ndarray: The generated branch offsets.
        """
        # Generate initial offsets
        anchor_pts = [0.0, self.length]
        offsets = self._generate_1d_spacing(anchor_pts, mesh1d_edge_length)

        if structure_offsets is None:
            return offsets

        # Check the limits
        if (excess := min(structure_offsets)) < 0.0 or (
            excess := max(structure_offsets)
        ) > self.length:
            raise ValueError(
                f"Distance {excess} is outside the branch range (0.0 - {self.length})."
            )

        # Merge limits with start and end of branch
        limits = [-1e-3] + list(sorted(structure_offsets)) + [self.length + 1e-3]

        # if requested, check if the calculation point are close enough to the structures
        if max_dist_to_struc is not None:
            limits = self._generate_extended_limits(max_dist_to_struc, limits)

        offsets = self._add_nodes_to_segments(
            offsets, anchor_pts, limits, mesh1d_edge_length
        )

        return offsets

    def _generate_extended_limits(
        self, max_dist_to_struc: float, limits: List[float]
    ) -> List[float]:
        """Generate extended limits by taking into account the maximum distance to a structure.

        Args:
            max_dist_to_struc (float): The maximum distance from a node to a structure.
            limits (List[float]): The limits.

        Returns:
            List[float]: A list with the updated limits.
        """

        additional = []

        # Skip the first and the last, these are no structures
        for i in range(1, len(limits) - 1):
            # if the distance between two limits is large than twice the max distance to structure,
            # the mesh point will be too far away. Add a limit on the minimum of half the length and
            # two times the max distance
            dist_to_prev_limit = limits[i] - (
                max(additional[-1], limits[i - 1]) if any(additional) else limits[i - 1]
            )
            if dist_to_prev_limit > 2 * max_dist_to_struc:
                additional.append(
                    limits[i] - min(2 * max_dist_to_struc, dist_to_prev_limit / 2)
                )

            dist_to_next_limit = limits[i + 1] - limits[i]
            if dist_to_next_limit > 2 * max_dist_to_struc:
                additional.append(
                    limits[i] + min(2 * max_dist_to_struc, dist_to_next_limit / 2)
                )

        # Join the limits
        return sorted(limits + additional)

    def _add_nodes_to_segments(
        self,
        offsets: np.ndarray,
        anchor_pts: List[float],
        limits: List[float],
        mesh1d_edge_length: float,
    ) -> np.ndarray:
        """Add nodes to segments that are missing a mesh node.

        Args:
            offsets (np.ndarray): The branch offsets.
            anchor_pts (List[float]): The anchor points.
            limits (List[float]): The limits.
            mesh1d_edge_length (float): The edge length of the 1d mesh.

        Returns:
            np.ndarray: The array with branch offsets.
        """
        # Get upper and lower limits
        upper_limits = limits[1:]
        lower_limits = limits[:-1]

        def in_range():
            return [
                ((offsets > lower) & (offsets < upper)).any()
                for lower, upper in zip(lower_limits, upper_limits)
            ]

        # Determine the segments that are missing a mesh node
        # Anchor points are added on these segments, such that they will get a mesh node
        nodes_in_range = in_range()

        while not all(nodes_in_range):
            # Get the index of the first segment without grid point
            i = nodes_in_range.index(False)

            # Add it to the anchor pts
            anchor_pts.append((lower_limits[i] + upper_limits[i]) / 2.0)
            anchor_pts = sorted(anchor_pts)

            # Generate new offsets
            offsets = self._generate_1d_spacing(anchor_pts, mesh1d_edge_length)

            # Determine the segments that are missing a grid point
            nodes_in_range = in_range()

        if len(anchor_pts) > 2:
            logger.info(
                f"Added 1d mesh nodes on branch at: {anchor_pts}, due to the structures at {limits}."
            )

        return offsets

    @staticmethod
    def _generate_1d_spacing(
        anchor_pts: List[float], mesh1d_edge_length: float
    ) -> np.ndarray:
        """
        Generates 1d distances, called by function generate offsets
        """
        offsets = []
        # Loop through anchor point pairs
        for i in range(len(anchor_pts) - 1):
            # Determine section length between anchor point
            section_length = anchor_pts[i + 1] - anchor_pts[i]
            if section_length <= 0.0:
                raise ValueError("Section length must be larger than 0.0")
            # Determine number of nodes
            nnodes = max(2, int(round(section_length / mesh1d_edge_length) + 1)) - 1
            # Add nodes
            offsets.extend(
                np.linspace(
                    anchor_pts[i], anchor_pts[i + 1], nnodes, endpoint=False
                ).tolist()
            )
        # Add last node
        offsets.append(anchor_pts[-1])

        return np.asarray(offsets)

    def interpolate(self, distance: npt.ArrayLike) -> np.ndarray:
        """Interpolate coordinates along branch by length

        Args:
            distance (npt.ArrayLike): Length
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
    """Link1d2d defines the 1D2D Links of a model network.

    Attributes:
        meshkernel (Optional[mk.MeshKernel]):
            The MeshKernel used to interact with this Link1d2d
        link1d2d_id (np.ndarray):
            The id of this Link1d2d
        link1d2d_long_name (np.ndarray):
            The long name of this Link1d2d
        link1d2d_contact_type (np.ndarray):
            The contact type of this Link1d2d
        link1d2d (np.ndarray):
            The underlying data object of this Link1d2d
    """

    meshkernel: mk.MeshKernel = Field(default_factory=mk.MeshKernel)

    link1d2d_id: np.ndarray = Field(default_factory=lambda: np.empty(0, object))
    link1d2d_long_name: np.ndarray = Field(default_factory=lambda: np.empty(0, object))
    link1d2d_contact_type: np.ndarray = Field(
        default_factory=lambda: np.empty(0, np.int32)
    )
    link1d2d: np.ndarray = Field(default_factory=lambda: np.empty((0, 2), np.int32))

    def is_empty(self) -> bool:
        """Whether this Link1d2d is currently empty.

        Returns:
            bool: True if the Link1d2d is currently empty; False otherwise.
        """
        return self.link1d2d.size == 0

    def read_file(self, file_path: Path) -> None:
        """Read the Link1d2d data from the specified netCDF file at file_path into this

        Args:
            file_path (Path): Path to the netCDF file.
        """

        reader = UgridReader(file_path)
        reader.read_link1d2d(self)

    def clear(self) -> None:
        """Remove all saved links from the links administration"""
        self.link1d2d_id = np.empty(0, object)
        self.link1d2d_long_name = np.empty(0, object)
        self.link1d2d_contact_type = np.empty(0, np.int32)
        self.link1d2d = np.empty((0, 2), np.int32)
        # The meshkernel object needs to be resetted
        self.meshkernel._deallocate_state()
        self.meshkernel._allocate_state(self.meshkernel.get_projection())
        self.meshkernel.contacts_get()

    def _process(self) -> None:
        """
        Get links from meshkernel and add to the array with link administration
        """
        contacts = self.meshkernel.contacts_get()

        self.link1d2d = np.append(
            self.link1d2d,
            np.stack([contacts.mesh1d_indices, contacts.mesh2d_indices], axis=1),
            axis=0,
        )
        self.link1d2d_contact_type = np.append(
            self.link1d2d_contact_type, np.full(contacts.mesh1d_indices.size, 3)
        )
        self.link1d2d_id = np.append(
            self.link1d2d_id,
            np.array([f"{n1d:d}_{f2d:d}" for n1d, f2d in self.link1d2d]),
        )
        self.link1d2d_long_name = np.append(
            self.link1d2d_long_name,
            np.array([f"{n1d:d}_{f2d:d}" for n1d, f2d in self.link1d2d]),
        )

    def _link_from_1d_to_2d(
        self, node_mask: np.ndarray, polygon: mk.GeometryList = None
    ):
        """Connect 1d nodes to 2d face circumcenters. A list of branchid's can be given
        to indicate where the 1d-side of the connections should be made. A polygon can
        be given to indicate where the 2d-side of the connections should be made.

        Note that the links are added to the already existing links. To remove these, use the method "clear".

        Args:
            node_mask (np.ndarray): Array indicating what 1d nodes should be connected. Defaults to None.
            polygon (mk.GeometryList): Coordinates of the area within which the 2d side of the links are connected.
        """

        # Computes Mesh1d-Mesh2d contacts, where each single Mesh1d node is connected to one Mesh2d face circumcenter.
        # The boundary nodes of Mesh1d (those sharing only one Mesh1d edge) are not connected to any Mesh2d face.
        self.meshkernel.contacts_compute_single(
            node_mask=node_mask, polygons=polygon, projection_factor=1.0
        )
        self._process()

        # Note that the function "contacts_compute_multiple" also computes the connections, but does not take into account
        # a bounding polygon or the end points of the 1d mesh.

    def _link_from_2d_to_1d_embedded(
        self, node_mask: np.ndarray, points: mk.GeometryList
    ):
        """"""
        self.meshkernel.contacts_compute_with_points(node_mask=node_mask, points=points)
        self._process()

    def _link_from_2d_to_1d_lateral(
        self,
        node_mask: np.ndarray,
        # boundary_face_xy: np.ndarray,
        polygon: mk.GeometryList = None,
        search_radius: float = None,
    ):
        # TODO: Missing value double for search radius?

        # Computes Mesh1d-Mesh2d contacts, where Mesh1d nodes are connected to the closest Mesh2d faces at the boundary
        self.meshkernel.contacts_compute_boundary(
            node_mask=node_mask, polygons=polygon, search_radius=search_radius
        )
        self._process()


class Mesh1d(BaseModel):
    """"""

    meshkernel: mk.MeshKernel = Field(default_factory=mk.MeshKernel)

    branches: Dict[str, Branch] = {}

    network1d_node_id: np.ndarray = Field(default_factory=lambda: np.empty(0, object))
    network1d_node_long_name: np.ndarray = Field(
        default_factory=lambda: np.empty(0, object)
    )
    network1d_node_x: np.ndarray = Field(default_factory=lambda: np.empty(0, np.double))
    network1d_node_y: np.ndarray = Field(default_factory=lambda: np.empty(0, np.double))
    network1d_branch_id: np.ndarray = Field(default_factory=lambda: np.empty(0, object))
    network1d_branch_long_name: np.ndarray = Field(
        default_factory=lambda: np.empty(0, object)
    )
    network1d_branch_length: np.ndarray = Field(
        default_factory=lambda: np.empty(0, np.double)
    )
    network1d_branch_order: np.ndarray = Field(
        default_factory=lambda: np.empty(0, np.int32)
    )
    network1d_edge_nodes: np.ndarray = Field(
        default_factory=lambda: np.empty((0, 2), np.int32)
    )
    # TODO: sync with node_x/node_y/edge_nodes with meshkernel: https://github.com/Deltares/HYDROLIB-core/issues/576
    network1d_geom_x: np.ndarray = Field(default_factory=lambda: np.empty(0, np.double))
    network1d_geom_y: np.ndarray = Field(default_factory=lambda: np.empty(0, np.double))
    network1d_part_node_count: np.ndarray = Field(
        default_factory=lambda: np.empty(0, np.int32)
    )

    mesh1d_node_x: np.ndarray = Field(default_factory=lambda: np.empty(0, np.double))
    mesh1d_node_y: np.ndarray = Field(default_factory=lambda: np.empty(0, np.double))
    mesh1d_node_id: np.ndarray = Field(default_factory=lambda: np.empty(0, object))
    mesh1d_node_long_name: np.ndarray = Field(
        default_factory=lambda: np.empty(0, object)
    )
    mesh1d_node_branch_id: np.ndarray = Field(
        default_factory=lambda: np.empty(0, np.int32)
    )
    mesh1d_node_branch_offset: np.ndarray = Field(
        default_factory=lambda: np.empty(0, np.double)
    )

    mesh1d_edge_nodes: np.ndarray = Field(
        default_factory=lambda: np.empty((0, 2), np.int32)
    )
    mesh1d_edge_x: np.ndarray = Field(default_factory=lambda: np.empty(0, np.double))
    mesh1d_edge_y: np.ndarray = Field(default_factory=lambda: np.empty(0, np.double))
    mesh1d_edge_branch_id: np.ndarray = Field(
        default_factory=lambda: np.empty(0, np.int32)
    )
    mesh1d_edge_branch_offset: np.ndarray = Field(
        default_factory=lambda: np.empty(0, np.double)
    )

    def is_empty(self) -> bool:
        return self.mesh1d_node_x.size == 0

    def _get_mesh1d(self) -> mk.Mesh1d:
        """Return mesh1d from meshkernel. Note that the meshkernel.Mesh1d instance
        does not contain all mesh attributes that are contained in this class"""
        return self.meshkernel.mesh1d_get()

    def _set_mesh1d(self) -> None:
        self.meshkernel.mesh1d_set(
            mk.Mesh1d(
                node_x=self.mesh1d_node_x.astype(np.float64),
                node_y=self.mesh1d_node_y.astype(np.float64),
                edge_nodes=self.mesh1d_edge_nodes.ravel().astype(np.int32),
            )
        )

    def _process_network1d(self) -> None:
        """
        Determine x, y locations of mesh1d nodes based on the network1d
        """
        # Create a list of coordinates to create the branches from
        ngeom = list(zip(self.network1d_geom_x, self.network1d_geom_y))

        self.branches.clear()

        for i, (name, nnodes) in enumerate(
            zip(self.network1d_branch_id, self.network1d_part_node_count)
        ):

            # Create network branch
            # Get geometry of branch from network geometry
            geometry = np.array([ngeom.pop(0) for _ in range(nnodes)])
            # Get branch offsets
            idx = self.mesh1d_node_branch_id == i
            branch_offsets = self.mesh1d_node_branch_offset[idx]
            mask = np.full(branch_offsets.shape, False)

            # Determine if a start or end coordinate needs to be added for constructing a complete branch
            # As nodes are re-used, the last and first branch_offsets are often missing. However, they are still used
            # for determining the length along the discretized branch.
            if branch_offsets.size == 0 or not np.isclose(branch_offsets[0], 0.0):
                branch_offsets = np.concatenate([[0], branch_offsets])
                mask = np.concatenate([[True], mask])
            length = np.hypot(*np.diff(geometry, axis=0).T).sum()
            if not np.isclose(branch_offsets[-1], length):
                branch_offsets = np.concatenate([branch_offsets, [length]])
                mask = np.concatenate([mask, [True]])

            # Create instance of branch object and add to dictionary
            geo_branch = Branch(geometry, branch_offsets=branch_offsets, mask=mask)
            self.branches[name.strip()] = geo_branch

        # Convert list with all coordinates (except the appended ones for the schematized branches) to arrays
        node_x, node_y = np.vstack(
            [branch.node_xy[~branch.mask] for branch in self.branches.values()]
        ).T

        # Add to variables
        self.mesh1d_node_x = node_x
        self.mesh1d_node_y = node_y

        # Calculate edge coordinates
        edge_x, edge_y = np.vstack(
            [
                branch.interpolate(
                    self.mesh1d_edge_branch_offset[self.mesh1d_edge_branch_id == i]
                )
                for i, branch in enumerate(self.branches.values())
            ]
        ).T

        # Add to variables
        self.mesh1d_edge_x = edge_x
        self.mesh1d_edge_y = edge_y

    def _network1d_node_position(self, x: float, y: float) -> Union[np.int32, None]:
        """Determine the position (index) of a x, y coordinate in the network nodes

        Args:
            x (float): x-coordinate
            y (float): y-coordinate

        Returns:
            Union[np.int32, None]: The index of the coordinate. None if not found
        """
        return self._node_position(self.network1d_node_x, self.network1d_node_y, x, y)

    def _mesh1d_node_position(self, x: float, y: float) -> Union[np.int32, None]:
        """Determine the position (index) of a x, y coordinate in the mesh nodes

        Args:
            x (float): x-coordinate
            y (float): y-coordinate

        Returns:
            Union[np.int32, None]: The index of the coordinate. None if not found
        """
        return self._node_position(self.mesh1d_node_x, self.mesh1d_node_y, x, y)

    def _node_position(
        self, arrx: np.ndarray, arry: np.ndarray, x: float, y: float
    ) -> Union[np.int32, None]:
        """Determine the position (index) of a x, y coordinate in a given x and y array

        Args:
            arrx (np.ndarray): x-coordinates in which the position is sought
            arry (np.ndarray): y-coordiantes in which the position is sought
            x (float): x-coordinate to be sought
            y (float): y-coordinate to be sought

        Raises:
            ValueError: If multiple positions are found for the coordinate

        Returns:
            Union[np.int32, None]: The index of the coordinate. None if not found
        """
        pos = np.where(np.isclose(arrx, x, rtol=0.0) & np.isclose(arry, y, rtol=0.0))[0]
        if pos.size == 0:
            return None
        elif pos.size == 1:
            return np.int32(pos[0])
        else:
            # Find the nearest
            distance = np.hypot(arrx[pos] - x, arry[pos] - y)
            if np.unique(distance).size == 1:
                raise ValueError("Multiple nodes were found at the same position.")
            else:
                return np.int32(pos[np.argmin(distance)])

    def _add_branch(
        self,
        branch: Branch,
        name: str = None,
        branch_order: int = -1,
        long_name: str = None,
        force_midpoint: bool = True,
    ):
        """Add the branch to mesh1d

        Args:
            branch (Branch): branch to add to the mesh1d
            name (str): id of the branch
            branch_order (int): interpolation order of the branch
            long_name (str): long name of the branch
            force_midpoint(bool): argument to control if a midpoint will be forced on the branch, use False for pipes

        Returns:
            Str: name of the branch.
        """

        # Check if branch had coordinate discretization
        if branch.branch_offsets.size == 0:
            raise ValueError(
                'Branch has no mesh discretization. Use the function "generate_nodes" solve generate a 1d mesh on the branch.'
            )

        if name in self.network1d_branch_id:
            raise KeyError(f'The branch name "{name}" is already used.')
        if long_name in self.network1d_branch_long_name:
            raise KeyError(f'The branch long name "{long_name}" is already used.')

        branch_nr = len(self.network1d_branch_id)
        if name is None:
            name = f"br{branch_nr:05d}"
        if long_name is None:
            long_name = name

        self.branches[name] = branch

        # Add branch administration
        self.network1d_branch_order = np.append(
            self.network1d_branch_order, branch_order
        )
        self.network1d_branch_length = np.append(
            self.network1d_branch_length, branch.length
        )
        self.network1d_branch_id = np.append(self.network1d_branch_id, name)
        self.network1d_branch_long_name = np.append(
            self.network1d_branch_long_name, long_name
        )

        # Add branch geometry coordinates
        self.network1d_part_node_count = np.append(
            self.network1d_part_node_count, len(branch.geometry)
        )
        self.network1d_geom_x = np.append(self.network1d_geom_x, branch._x_coordinates)
        self.network1d_geom_y = np.append(self.network1d_geom_y, branch._y_coordinates)

        # Network edge node administration
        # -------------------------------

        first_point = branch.geometry[0]
        last_point = branch.geometry[-1]

        # Get offsets from dictionary
        offsets = branch.branch_offsets[:]
        # The number of links on the branch
        nlinks = len(offsets) - 1

        # Check if the first and last point of the branch are already in the set
        first_present = self._network1d_node_position(*first_point) is not None
        if first_present:
            # If present, remove from branch offsets
            offsets = offsets[1:]
            branch.mask[0] = True
        else:
            # If not present, add to network nodes
            self.network1d_node_x = np.append(self.network1d_node_x, first_point[0])
            self.network1d_node_y = np.append(self.network1d_node_y, first_point[1])

            self.network1d_node_id = np.append(
                self.network1d_node_id, "{:.6f}_{:.6f}".format(*first_point)
            )
            self.network1d_node_long_name = np.append(
                self.network1d_node_long_name, "x={:.6f}_y={:.6f}".format(*first_point)
            )

        last_present = self._network1d_node_position(*last_point) is not None
        if last_present:
            # If present, remove from branch offsets
            offsets = offsets[:-1]
            branch.mask[-1] = True
        else:
            # If not present, add to network nodes
            self.network1d_node_x = np.append(self.network1d_node_x, last_point[0])
            self.network1d_node_y = np.append(self.network1d_node_y, last_point[1])

            self.network1d_node_id = np.append(
                self.network1d_node_id, "{:.6f}_{:.6f}".format(*last_point)
            )
            self.network1d_node_long_name = np.append(
                self.network1d_node_long_name, "x={:.6f}_y={:.6f}".format(*last_point)
            )

        # If no points remain, add an extra halfway: each branch should have at least 1 node
        # Adjust the branch object as well, by adding the extra point
        if len(offsets) == 0 and force_midpoint:
            # Add extra offset
            extra_offset = branch.length / 2.0
            offsets = np.array([extra_offset])
            nlinks += 1
            # Adjust branch object
            branch.branch_offsets = np.insert(branch.branch_offsets, 1, extra_offset)
            branch.node_xy = np.insert(
                branch.node_xy, 1, branch.interpolate(offsets), axis=0
            )
            branch.mask = np.insert(branch.mask, 1, False)

        # Get the index of the first and last node, add as edge_nodes
        i_from = self._network1d_node_position(first_point[0], first_point[1])
        i_to = self._network1d_node_position(last_point[0], last_point[1])
        if i_from == i_to:
            raise ValueError(
                "Start and end node are the same. Ring geometries are not accepted."
            )

        self.network1d_edge_nodes = np.append(
            self.network1d_edge_nodes,
            np.array([[i_from, i_to]], dtype=np.int32),
            axis=0,
        )

        # Mesh1d edge node administration

        # -------------------------------
        # First determine the start index. This is equal to the number of already present points
        start_index = len(self.mesh1d_node_branch_id)
        # For each link, create a new edge node connection
        # If the first node is already present, subtract 1, since the first number will be substitud with the present node
        if first_present:
            start_index -= 1
        new_edge_nodes = (
            np.stack([np.arange(nlinks), np.arange(nlinks) + 1], axis=1) + start_index
        ).astype(np.int32)

        # If the first node is present, change the first point of the first edge to the existing point
        if first_present:
            new_edge_nodes[0, 0] = self._mesh1d_node_position(*first_point)
        # If the last node is present, change the last point of the last edge too
        if last_present:
            new_edge_nodes[-1, 1] = self._mesh1d_node_position(*last_point)

        # Add to variables
        self.mesh1d_node_x = np.append(
            self.mesh1d_node_x, branch.node_xy[~branch.mask, 0]
        )
        self.mesh1d_node_y = np.append(
            self.mesh1d_node_y, branch.node_xy[~branch.mask, 1]
        )

        # Add to edge_nodes
        self.mesh1d_edge_nodes = np.append(
            self.mesh1d_edge_nodes, new_edge_nodes, axis=0
        )
        edge_coords = np.stack([self.mesh1d_node_x, self.mesh1d_node_y], axis=1)[
            new_edge_nodes
        ].mean(1)
        edge_offsets = (branch.branch_offsets[:-1] + branch.branch_offsets[1:]) / 2

        self.mesh1d_edge_branch_id = np.append(
            self.mesh1d_edge_branch_id, np.full(len(edge_coords), branch_nr)
        )
        self.mesh1d_edge_branch_offset = np.append(
            self.mesh1d_edge_branch_offset, edge_offsets
        )

        self.mesh1d_edge_x = np.append(self.mesh1d_edge_x, edge_coords[:, 0])
        self.mesh1d_edge_y = np.append(self.mesh1d_edge_y, edge_coords[:, 1])

        # Update names of nodes
        mesh_point_names = np.array(
            [f"{name}_{offset:.2f}" for offset in offsets], dtype=object
        )
        self.mesh1d_node_id = np.append(self.mesh1d_node_id, mesh_point_names)
        self.mesh1d_node_long_name = np.append(
            self.mesh1d_node_long_name, mesh_point_names
        )

        # Add mesh1d nodes
        self.mesh1d_node_branch_id = np.append(
            self.mesh1d_node_branch_id, np.full(len(offsets), branch_nr)
        )
        self.mesh1d_node_branch_offset = np.append(
            self.mesh1d_node_branch_offset, offsets
        )
        return name

    def get_node_mask(self, branchids: List[str] = None):
        """Get node mask, give a mask with True for each node that is in the given branchid list"""

        mask = np.full(self.mesh1d_node_id.shape, False, dtype=bool)
        if branchids is None:
            mask[:] = True
            return mask

        # Get number (index) of given branches
        idx = np.where(np.isin(self.network1d_branch_id, branchids))[0]
        if idx.size == 0:
            raise KeyError("No branches corresponding to the given keys were found.")

        mask[np.isin(self.mesh1d_node_branch_id, idx)] = True

        return mask


class Network:
    def __init__(self, is_geographic: bool = False) -> None:
        if not is_geographic:
            projection = mk.ProjectionType.CARTESIAN
        else:
            projection = mk.ProjectionType.SPHERICAL

        self.meshkernel = mk.MeshKernel(projection=projection)
        self._mesh1d = Mesh1d(meshkernel=self.meshkernel)
        self._mesh2d = Mesh2d(meshkernel=self.meshkernel)
        self._link1d2d = Link1d2d(meshkernel=self.meshkernel)

        # Spatial index (rtree)
        # self._idx = index.Index()

    @classmethod
    def from_file(cls, file_path: Path) -> Network:
        """Read network from file. This classmethod checks what mesh components (mesh1d & network1d, mesh2d, link1d2d) are
        present, and loads them one by one.

        Args:
            file_path (Path): path to netcdf file with network data

        Returns:
            Network: The instance of the class itself that is returned
        """

        network = cls()
        ds = nc.Dataset(file_path)  # type: ignore[import]

        reader = UgridReader(file_path)

        reader.read_mesh1d_network1d(network._mesh1d)
        reader.read_mesh2d(network._mesh2d)
        reader.read_link1d2d(network._link1d2d)

        ds.close()

        return network

    def to_file(self, file: Path) -> None:
        """Write network to file

        Args:
            file (Path): File where _net.nc is written to.
        """

        writer = UgridWriter()
        writer.write(self, file)

    @property
    def is_geographic(self) -> bool:
        """Whether or not this network has a geographic projection.

        Returns:
            bool: True if this network is geographic; otherwise, False.
        """
        projection = self.meshkernel.get_projection()
        if projection == mk.ProjectionType.CARTESIAN:
            return False
        else:
            return True

    def link1d2d_from_1d_to_2d(
        self, branchids: List[str] = None, polygon: GeometryList = None
    ) -> None:
        self._mesh1d._set_mesh1d()

        node_mask = self._mesh1d.get_node_mask(branchids)
        if polygon is None:
            polygon = self.meshkernel.mesh2d_get_mesh_boundaries_as_polygons()

        self._link1d2d._link_from_1d_to_2d(node_mask, polygon=polygon)

    def mesh2d_create_rectilinear_within_extent(
        self, extent: tuple, dx: float, dy: float
    ) -> None:
        self._mesh2d.create_rectilinear(extent=extent, dx=dx, dy=dy)

    def mesh2d_create_triangular_within_polygon(self, polygon: mk.GeometryList) -> None:
        """Create triangular grid within GeometryList object. Calls _mesh2d.create_triangular
        directly, but is easier accessible for users.

        Args:
            polygon (mk.GeometryList): GeometryList representing a polygon within which the mesh is generated.
        """
        self._mesh2d.create_triangular(geometry_list=polygon)

    def mesh2d_clip_mesh(
        self,
        geometrylist: mk.GeometryList,
        deletemeshoption: mk.DeleteMeshOption = mk.DeleteMeshOption.INSIDE_NOT_INTERSECTED,
        inside=True,
    ) -> None:
        self._mesh2d.clip(
            geometrylist=geometrylist,
            deletemeshoption=deletemeshoption,
            inside=inside,
        )

    def mesh2d_refine_mesh(self, polygon: mk.GeometryList, level: int = 1) -> None:
        self._mesh2d.refine(polygon=polygon, level=level)

    def mesh1d_add_branch(
        self,
        branch: Branch,
        name: str = None,
        branch_order: int = -1,
        long_name: str = None,
        force_midpoint: bool = True,
    ) -> None:
        name = self._mesh1d._add_branch(
            branch=branch,
            name=name,
            branch_order=branch_order,
            long_name=long_name,
            force_midpoint=force_midpoint,
        )
        self._mesh1d._set_mesh1d()
        return name

    def plot(self, ax=None):
        """Create a plot of the 1d2d links and edges within this network.

        Args:
            ax (matplotlib.pyplot.Axes, optional): The axes where to plot the edges. Defaults to None.
        """
        import matplotlib.pyplot as plt

        if ax is None:
            _, ax = plt.subplots()
        mesh2d_output = self._mesh2d.get_mesh2d()
        mesh1d_output = self._mesh1d._get_mesh1d()
        links_output = self._link1d2d.meshkernel.contacts_get()
        mesh2d_output.plot_edges(ax=ax, color="r")
        mesh1d_output.plot_edges(ax=ax, color="g")
        links_output.plot_edges(
            ax=ax, mesh1d=mesh1d_output, mesh2d=mesh2d_output, color="k"
        )


class NetworkModel(ParsableFileModel):
    """Network model representation."""

    network: Network = Field(default_factory=Network)

    def _post_init_load(self) -> None:
        """
        Load the network file if the filepath exists relative to the
        current FileLoadContext.
        """
        super()._post_init_load()

        if self.filepath is None:
            return

        with file_load_context() as context:
            network_path = context.resolve(self.filepath)

            if network_path.is_file():
                self.network = Network.from_file(network_path)

    @property
    def _mesh1d(self):
        return self.network._mesh1d

    @property
    def _mesh2d(self):
        return self.network._mesh2d

    @property
    def _link1d2d(self):
        return self.network._link1d2d

    @classmethod
    def _ext(cls) -> str:
        return ".nc"

    @classmethod
    def _filename(cls) -> str:
        return "network"

    def _save(self, save_settings: ModelSaveSettings):
        with file_load_context() as context:
            write_path = context.resolve(self.filepath)  # type: ignore[arg-type]

            write_path.parent.mkdir(parents=True, exist_ok=True)
            self.network.to_file(write_path)

    def _export(self, folder: Path) -> None:
        filename = Path(self.filepath.name) if self.filepath else self._generate_name()
        self.filepath = folder / filename
        folder.mkdir(parents=True, exist_ok=True)
        self.network.to_file(self.filepath)

    def _parse(self, _):
        return {}

    @classmethod
    def _get_serializer(cls):
        # Unused, but requires abstract implementation
        pass

    @classmethod
    def _get_parser(cls):
        # Unused, but requires abstract implementation
        pass

    @property
    def plot(self):
        return self.network.plot
