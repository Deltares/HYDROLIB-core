from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Union

import meshkernel as mk
import netCDF4 as nc
import numpy as np
import numpy.typing as npt
from meshkernel.py_structures import GeometryList
from pydantic import Field

from hydrolib.core import __version__
from hydrolib.core.basemodel import BaseModel, FileModel, file_load_context
from hydrolib.core.io.net.reader import UgridReader
from hydrolib.core.io.net.writer import UgridWriter


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
        mesh2d_node_x (np.ndarray):
            The node positions on the x-axis. Defaults to np.empty(0, dtype=np.double).
        mesh2d_node_y (np.ndarray):
            The node positions on the y-axis. Defaults to np.empty(0, dtype=np.double).
        mesh2d_node_z (np.ndarray):
            The node positions on the z-axis. Defaults to np.empty(0, dtype=np.double).
        mesh2d_edge_x (np.ndarray):
            The edge positions on the x-axis. Defaults to np.empty(0, dtype=np.double).
        mesh2d_edge_y (np.ndarray):
            The edge positions on the y-axis. Defaults to np.empty(0, dtype=np.double).
        mesh2d_edge_z (np.ndarray):
            The edge positions on the z-axis. Defaults to np.empty(0, dtype=np.double).
        mesh2d_edge_nodes (np.ndarray):
            The mapping of edges to node indices. Defaults to
            np.empty((0, 2), dtype=np.int32).


        mesh2d_face_x (np.ndarray):
            The face positions on the x-axis. Defaults to np.empty(0, dtype=np.double).
        mesh2d_face_y (np.ndarray):
            The face positions on the y-axis. Defaults to np.empty(0, dtype=np.double).
        mesh2d_face_z (np.ndarray):
            The face positions on the z-axis. Defaults to np.empty(0, dtype=np.double).
        mesh2d_face_nodes (np.ndarray):
            The mapping of faces to node indices. Defaults to
            np.empty((0, 0), dtype=np.int32)
    """

    meshkernel: mk.MeshKernel = Field(default_factory=mk.MeshKernel)

    mesh2d_node_x: np.ndarray = Field(
        default_factory=lambda: np.empty(0, dtype=np.double)
    )
    mesh2d_node_y: np.ndarray = Field(
        default_factory=lambda: np.empty(0, dtype=np.double)
    )
    mesh2d_node_z: np.ndarray = Field(
        default_factory=lambda: np.empty(0, dtype=np.double)
    )

    mesh2d_edge_x: np.ndarray = Field(
        default_factory=lambda: np.empty(0, dtype=np.double)
    )
    mesh2d_edge_y: np.ndarray = Field(
        default_factory=lambda: np.empty(0, dtype=np.double)
    )
    mesh2d_edge_z: np.ndarray = Field(
        default_factory=lambda: np.empty(0, dtype=np.double)
    )
    mesh2d_edge_nodes: np.ndarray = Field(
        default_factory=lambda: np.empty((0, 2), dtype=np.int32)
    )

    mesh2d_face_x: np.ndarray = Field(
        default_factory=lambda: np.empty(0, dtype=np.double)
    )
    mesh2d_face_y: np.ndarray = Field(
        default_factory=lambda: np.empty(0, dtype=np.double)
    )
    mesh2d_face_z: np.ndarray = Field(
        default_factory=lambda: np.empty(0, dtype=np.double)
    )
    mesh2d_face_nodes: np.ndarray = Field(
        default_factory=lambda: np.empty((0, 0), dtype=np.int32)
    )

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

    def _set_mesh2d(self) -> None:
        mesh2d = mk.Mesh2d(
            node_x=self.mesh2d_node_x,
            node_y=self.mesh2d_node_y,
            edge_nodes=self.mesh2d_edge_nodes.ravel(),
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

        # Process
        self._process(mesh2d_input)

    def _process(self, mesh2d_input) -> None:
        # Add input
        self.meshkernel.mesh2d_set(mesh2d_input)
        # Get output
        mesh2d_output = self.meshkernel.mesh2d_get()
        # Add to mesh2d variables
        self.mesh2d_node_x = mesh2d_output.node_x
        self.mesh2d_node_y = mesh2d_output.node_y

        self.mesh2d_edge_x = mesh2d_output.edge_x
        self.mesh2d_edge_y = mesh2d_output.edge_y
        self.mesh2d_edge_nodes = mesh2d_output.edge_nodes.reshape((-1, 2))

        self.mesh2d_face_x = mesh2d_output.face_x
        self.mesh2d_face_y = mesh2d_output.face_y
        npf = mesh2d_output.nodes_per_face
        self.mesh2d_face_nodes = np.full(
            (len(self.mesh2d_face_x), max(npf)), np.iinfo(np.int32).min
        )
        idx = (
            np.ones_like(self.mesh2d_face_nodes) * np.arange(max(npf))[None, :]
        ) < npf[:, None]
        self.mesh2d_face_nodes[idx] = mesh2d_output.face_nodes

    def clip(self, polygon: mk.GeometryList, deletemeshoption: int = 1) -> None:
        """Clip the 2D mesh by a polygon. Both outside the exterior and inside the interiors is clipped

        Args:
            polygon (GeometryList): Polygon stored as GeometryList
            deletemeshoption (int, optional): [description]. Defaults to 1.
        """

        # Add current mesh to Mesh2d instance
        self._set_mesh2d()

        # Delete outside polygon
        deletemeshoption = mk.DeleteMeshOption(deletemeshoption)
        parts = split_by(polygon, -998.0)

        # Check if parts are closed
        for part in parts:
            if not (part.x_coordinates[0], part.y_coordinates[0]) == (
                part.x_coordinates[-1],
                part.y_coordinates[-1],
            ):
                raise ValueError(
                    "First and last coordinate of each GeometryList part should match."
                )

        self.meshkernel.mesh2d_delete(parts[0], deletemeshoption, True)

        # Delete all holes
        for interior in parts[1:]:
            self.meshkernel.mesh2d_delete(interior, deletemeshoption, False)

        # Process
        self._process(self.meshkernel.mesh2d_get())

    def refine(self, polygon: mk.GeometryList, level: int):
        """Refine the mesh within a polygon, by a number of steps (level)

        Args:
            polygon (GeometryList): Polygon in which to refine
            level (int): Number of refinement steps
        """
        # Add current mesh to Mesh2d instance
        mesh2d_input = mk.Mesh2d(
            node_x=self.mesh2d_node_x,
            node_y=self.mesh2d_node_y,
            edge_nodes=self.mesh2d_edge_nodes.ravel(),
        )
        self.meshkernel.mesh2d_set(mesh2d_input)

        # Check if parts are closed
        if not (polygon.x_coordinates[0], polygon.y_coordinates[0]) == (
            polygon.x_coordinates[-1],
            polygon.y_coordinates[-1],
        ):
            raise ValueError(
                "First and last coordinate of each GeometryList part should match."
            )

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

        # Process
        self._process(self.meshkernel.mesh2d_get())


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
            # TODO Add validation for offsets smaller than 0 or smaller than the branch length.
            self.node_xy = self.interpolate(branch_offsets)

        # Set which of the nodes are present
        if (mask is None) and (branch_offsets is not None):
            self.mask = np.full(branch_offsets.shape, False)
        else:
            self.mask = mask

    def generate_nodes(
        self,
        mesh1d_edge_length: float,
        seperate_structures: bool = False,
        max_dist_to_struc: float = None,
    ):
        if seperate_structures:
            raise NotImplementedError(
                "Taking into account structure positions is not implemented."
            )

        # Generate offsets
        self.branch_offsets = self._generate_1d_spacing(
            anchor_pts=[0.0, self.length], mesh1d_edge_length=mesh1d_edge_length
        )
        # Calculate node positions
        self.node_xy = self.interpolate(self.branch_offsets)
        # Add mask (all False)
        self.mask = np.full(self.branch_offsets.shape, False)

    def _generate_1d_spacing(self, anchor_pts: List[float], mesh1d_edge_length: float):
        """
        Generates 1d distances, called by function generate offsets
        """
        offsets = []
        for i in range(len(anchor_pts) - 1):
            section_length = anchor_pts[i + 1] - anchor_pts[i]
            if section_length <= 0.0:
                raise ValueError("Section length must be larger than 0.0")
            nnodes = max(2, int(round(section_length / mesh1d_edge_length) + 1))
            offsets.extend(
                np.linspace(
                    anchor_pts[i], anchor_pts[i + 1], nnodes - 1, endpoint=False
                ).tolist()
            )
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
        self.link1d2d_id = Field(default_factory=lambda: np.empty(0, object))
        self.link1d2d_long_name = Field(default_factory=lambda: np.empty(0, object))
        self.link1d2d_contact_type = Field(
            default_factory=lambda: np.empty(0, np.int32)
        )
        self.link1d2d = Field(default_factory=lambda: np.empty((0, 2), np.int32))

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
        self.meshkernel.contacts_compute_single(node_mask=node_mask, polygons=polygon)
        self._process()

        # Note that the function "contacts_compute_multiple" also computes the connections, but does not take into account
        # a bounding polygon or the end points of the 1d mesh.
        # self._mk.contacts_compute_multiple(self, node_mask)

    def _link_from_2d_to_1d_intersecting(self):
        raise NotImplementedError()

    def _link_from_2d_to_1d_lateral(self):
        raise NotImplementedError()

        # # Computes Mesh1d-Mesh2d contacts, where a Mesh2d face per polygon is connected to the closest Mesh1d node.
        # self._mk.contacts_compute_with_polygons(self, node_mask, polygons)

        # # Computes Mesh1d-Mesh2d contacts, where Mesh1d nodes are connected to the Mesh2d face mass centers containing the input point.
        # self._mk.contacts_compute_with_points(self, node_mask, points)

        # # Computes Mesh1d-Mesh2d contacts, where Mesh1d nodes are connected to the closest Mesh2d faces at the boundary
        # self._mk.contacts_compute_boundary(self, node_mask, polygons, search_radius)


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
        pos = np.where(np.isclose(arrx, x) & np.isclose(arry, y))[0]
        if pos.size == 0:
            return None
        elif pos.size == 1:
            return np.int32(pos[0])
        else:
            raise ValueError("Multiple nodes were found at the given position.")

    def _add_branch(
        self,
        branch: Branch,
        name: str = None,
        branch_order: int = -1,
        long_name: str = None,
    ):

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
        self.network1d_branch_order = np.append(self.network1d_branch_order, -1)
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
                self.network1d_node_id, "{:.0f}_{:.0f}".format(*first_point)
            )
            self.network1d_node_long_name = np.append(
                self.network1d_node_long_name, "x={:.0f}_y={:.0f}".format(*first_point)
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
                self.network1d_node_id, "{:.0f}_{:.0f}".format(*last_point)
            )
            self.network1d_node_long_name = np.append(
                self.network1d_node_long_name, "x={:.0f}_y={:.0f}".format(*last_point)
            )

        # If no points remain, add an extra halfway: each branch should have at least 1 node
        if len(offsets) == 0:
            offsets = np.array([branch.length / 2.0])
            nlinks += 1

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

        # self._process_edges_for_branch()

    def _process_edges_for_branch(self, branch_id: str) -> None:

        branch = self.branches[branch_id]

        edge_coords = (branch.node_xy[:-1] + branch.node_xy[1:]) / 2.0
        edge_offsets = (branch.branch_offsets[:-1] + branch.branch_offsets[1:]) / 2

        self.mesh1d_edge_branch_id = np.append(
            self.mesh1d_edge_branch_id, np.full(len(edge_coords), i)
        )
        self.mesh1d_edge_branch_offset = np.append(
            self.mesh1d_edge_branch_offset, edge_offsets
        )
        self.mesh1d_edge_x = np.append(self.mesh1d_edge_x, edge_coords[:, 0])
        self.mesh1d_edge_y = np.append(self.mesh1d_edge_y, edge_coords[:, 1])

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
    def __init__(self) -> None:
        self.meshkernel = mk.MeshKernel()

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

    def link1d2d_from_1d_to_2d(
        self, branchids: List[str] = None, polygon: GeometryList = None
    ) -> None:
        self._mesh1d._set_mesh1d()
        self._mesh2d._set_mesh2d()

        node_mask = self._mesh1d.get_node_mask(branchids)
        if polygon is None:
            polygon = self.meshkernel.mesh2d_get_mesh_boundaries_as_polygons()

        self._link1d2d._link_from_1d_to_2d(node_mask, polygon=polygon)

    def mesh2d_create_rectilinear_within_bounds(
        self, extent: tuple, dx: float, dy: float
    ) -> None:
        self._mesh2d.create_rectilinear(extent=extent, dx=dx, dy=dy)

    def mesh2d_create_triangular_within_polygon(self, polygon: mk.GeometryList) -> None:
        raise NotImplementedError()

    def mesh2d_clip_mesh(
        self, polygon: mk.GeometryList, deletemeshoption: int = 1
    ) -> None:
        self._mesh2d.clip(polygon=polygon, deletemeshoption=deletemeshoption)

    def mesh2d_refine_mesh(self, polygon: mk.GeometryList, level: int = 1) -> None:
        self._mesh2d.refine(polygon=polygon, level=level)

    def mesh1d_add_branch(
        self,
        branch: Branch,
        name: str = None,
        branch_order: int = -1,
        long_name: str = None,
    ) -> None:
        self._mesh1d._add_branch(
            branch=branch, name=name, branch_order=branch_order, long_name=long_name
        )


class NetworkModel(FileModel):
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

    def _save(self):
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
