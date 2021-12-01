from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List

import netCDF4 as nc
import numpy as np

from hydrolib.core import __version__

if TYPE_CHECKING:
    from .models import Link1d2d, Mesh1d, Mesh2d, NetworkModel


class UgridWriter:
    """Writer for netCDF files with UGrid convention"""

    def __init__(self):
        self.idstrlength = 40
        self.longstrlength = 80

    def write(
        self,
        network: NetworkModel,
        path: Path,
        dfm_version: str = "",
        dimr_version: str = "",
        suite_version: str = "",
    ) -> None:
        """write ugrid file from GWSW model"""

        ncfile = self._create_netcdf(path, dfm_version, dimr_version, suite_version)
        self._write_mesh1d_to(network._mesh1d, ncfile)
        self._write_mesh2d_to(network._mesh2d, ncfile)
        self._write_1d2dlinks_to(network._link1d2d, ncfile)
        ncfile.close()

    def _write_mesh1d_to(self, mesh1d: Mesh1d, ncfile: nc.Dataset) -> None:  # type: ignore[import]
        if mesh1d.is_empty():
            return

        self._init_1dnetwork(ncfile, mesh1d)
        self._set_1dmesh(ncfile, mesh1d)
        self._set_1dnetwork(ncfile, mesh1d)

    def _write_mesh2d_to(self, mesh2d: Mesh2d, ncfile) -> None:
        if mesh2d.is_empty():
            return

        self._init_2dmesh(ncfile, mesh2d)
        self._set_2dmesh(ncfile, mesh2d)

    def _write_1d2dlinks_to(self, link1d2d: Link1d2d, ncfile) -> None:
        if link1d2d.is_empty():
            return

        self._init_1d2dlinks(ncfile, link1d2d)
        self._set_1d2dlinks(ncfile, link1d2d)

    @staticmethod
    def to_char_list(lst: List[str], size: int) -> List[str]:
        """Convert list of strings to list of stings with a fixed number of characters"""
        return [item.ljust(size)[:size] for item in lst]

    def _create_netcdf(
        self, path: Path, dfm_version: str, dimr_version: str, suite_version: str
    ) -> nc.Dataset:  # type: ignore[import]

        file_format = "NETCDF3_CLASSIC"  # "NETCDF4"
        ncfile = nc.Dataset(path, "w", format=file_format)  # type: ignore[import]

        UgridWriter._set_global_attributes(ncfile, path)
        ncfile.comment = f"Tested and compatible with D-Flow FM {dfm_version}, DIMRset {dimr_version} and D-HYDRO suite 1D2D {suite_version}"

        return ncfile

    @staticmethod
    def _set_global_attributes(ncfile: nc.Dataset, path: Path) -> None:  # type: ignore[import]
        ncfile.Conventions = "CF-1.8 UGRID-1.0"
        ncfile.title = "Delft3D-FM 1D2D network for model " + path.name.rstrip(
            "_net.nc"
        )
        ncfile.source = f"HYDROLIB-core v.{__version__}, D-HyDAMO, model {path.name.rstrip('_net.nc')}"
        ncfile.history = f"Created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by {Path(__file__).name}."
        ncfile.institution = "Deltares/HKV"
        ncfile.references = "https://github.com/openearth/delft3dfmpy/; https://www.deltares.nl; https://www.hkv.nl"

    def _init_1dnetwork(self, ncfile: nc.Dataset, mesh1d: Mesh1d) -> None:  # type: ignore[import]
        # dimensions of the network
        ncfile.createDimension("time", None)
        ncfile.createDimension("network1d_nEdges", mesh1d.network1d_edge_nodes.shape[0])
        ncfile.createDimension("network1d_nNodes", mesh1d.network1d_node_x.size)
        ncfile.createDimension("network1d_nGeometryNodes", mesh1d.network1d_geom_x.size)
        ncfile.createDimension("idstrlength", self.idstrlength)
        ncfile.createDimension("longstrlength", self.longstrlength)
        ncfile.createDimension("mesh1d_nEdges", mesh1d.mesh1d_edge_nodes.shape[0])
        ncfile.createDimension("mesh1d_nNodes", mesh1d.mesh1d_node_id.size)
        if not "Two" in ncfile.dimensions:
            ncfile.createDimension("Two", 2)

    def _init_2dmesh(self, ncfile: nc.Dataset, mesh2d: Mesh2d) -> None:  # type: ignore[import]
        ncfile.createDimension(
            "max_nmesh2d_face_nodes", mesh2d.mesh2d_face_nodes.shape[1]
        )
        ncfile.createDimension("mesh2d_nEdges", mesh2d.mesh2d_edge_nodes.shape[0])
        ncfile.createDimension("mesh2d_nFaces", mesh2d.mesh2d_face_nodes.shape[0])
        ncfile.createDimension("mesh2d_nNodes", mesh2d.mesh2d_node_x.size)
        if not "Two" in ncfile.dimensions:
            ncfile.createDimension("Two", 2)

    def _init_1d2dlinks(self, ncfile: nc.Dataset, link1d2d: Link1d2d) -> None:  # type: ignore[import]
        ncfile.createDimension("nLink1D2D_edge", link1d2d.link1d2d.shape[0])

        cm = ncfile.createVariable("composite_mesh", "i4", ())
        cm.cf_role = "parent_mesh_topology"
        cm.meshes = "mesh1d mesh2d"
        cm.mesh_contact = "link1d2d"

    def _set_1dnetwork(self, ncfile: nc.Dataset, mesh1d: Mesh1d) -> None:  # type: ignore[import]
        #  network topology
        ntw = ncfile.createVariable("network1d", "i4", ())
        ntw.cf_role = "mesh_topology"
        ntw.edge_dimension = "network1d_nEdges"
        ntw.edge_geometry = "network1d_geometry"
        ntw.edge_node_connectivity = "network1d_edge_nodes"
        ntw.long_name = "Topology data of 1D network"
        ntw.node_coordinates = "network1d_node_x network1d_node_y"
        ntw.node_dimension = "network1d_nNodes"
        ntw.topology_dimension = 1
        ntw.node_id = "network1d_node_id"
        ntw.node_long_name = "network1d_node_long_name"
        ntw.branch_id = "network1d_branch_id"
        ntw.branch_long_name = "network1d_branch_long_name"
        ntw.edge_length = "network1d_edge_length"
        ntw.branch_order = "network1d_branch_order"

        ntw_node_id = ncfile.createVariable(
            "network1d_node_id", "c", ("network1d_nNodes", "idstrlength")
        )
        ntw_node_id.long_name = "ID of network nodes"
        ntw_node_id[:] = self.to_char_list(mesh1d.network1d_node_id, self.idstrlength)

        ntw_node_longname = ncfile.createVariable(
            "network1d_node_long_name", "c", ("network1d_nNodes", "longstrlength")
        )
        ntw_node_longname.long_name = "Long name of network nodes"
        ntw_node_longname[:] = self.to_char_list(
            mesh1d.network1d_node_long_name, self.longstrlength
        )

        # network nodes
        ntw_node_x = ncfile.createVariable(
            "network1d_node_x", np.float64, "network1d_nNodes"
        )
        ntw_node_x.standard_name = "projection_x_coordinate"
        ntw_node_x.long_name = "x coordinates of network nodes"
        ntw_node_x.units = "m"
        ntw_node_x[:] = mesh1d.network1d_node_x

        ntw_node_y = ncfile.createVariable(
            "network1d_node_y", np.float64, "network1d_nNodes"
        )
        ntw_node_y.standard_name = "projection_y_coordinate"
        ntw_node_y.long_name = "y coordinates of network nodes"
        ntw_node_y.units = "m"
        ntw_node_y[:] = mesh1d.network1d_node_y

        ntw_branch_id_name = ncfile.createVariable(
            "network1d_branch_id", "c", ("network1d_nEdges", "idstrlength")
        )
        ntw_branch_id_name.long_name = "ID of branch geometries"
        ntw_branch_id_name[:] = self.to_char_list(
            mesh1d.network1d_branch_id, self.idstrlength
        )

        ntw_branch_id_longname = ncfile.createVariable(
            "network1d_branch_long_name", "c", ("network1d_nEdges", "longstrlength")
        )
        ntw_branch_id_longname.long_name = "Long name of branch geometries"
        ntw_branch_id_longname[:] = self.to_char_list(
            mesh1d.network1d_branch_long_name, self.longstrlength
        )

        ntw_edge_length = ncfile.createVariable(
            "network1d_edge_length", np.float64, "network1d_nEdges"
        )
        ntw_edge_length.long_name = "Real length of branch geometries"
        ntw_edge_length.units = "m"
        ntw_edge_length[:] = mesh1d.network1d_branch_length

        ntw_branch_order = ncfile.createVariable(
            "network1d_branch_order", "i4", "network1d_nEdges"
        )
        ntw_branch_order.long_name = "Order of branches for interpolation"
        ntw_branch_order.mesh = "network1d"
        ntw_branch_order.location = "edge"
        ntw_branch_order[:] = mesh1d.network1d_branch_order

        # network edges
        ntw_edge_node = ncfile.createVariable(
            "network1d_edge_nodes", "i4", ("network1d_nEdges", "Two")
        )
        ntw_edge_node.cf_role = "edge_node_connectivity"
        ntw_edge_node.long_name = "start and end nodes of network edges"
        ntw_edge_node.start_index = 1
        ntw_edge_node[:] = mesh1d.network1d_edge_nodes + ntw_edge_node.start_index

        # network geometry
        ntw_geom = ncfile.createVariable("network1d_geometry", "i4", ())
        ntw_geom.geometry_type = "line"
        ntw_geom.long_name = "1D Geometry"
        ntw_geom.node_count = "network1d_geom_node_count"
        ntw_geom.node_coordinates = "network1d_geom_x network1d_geom_y"

        ntw_geom_node_count = ncfile.createVariable(
            "network1d_geom_node_count", "i4", "network1d_nEdges"
        )
        ntw_geom_node_count.long_name = "Number of geometry nodes per branch"
        ntw_geom_node_count[:] = mesh1d.network1d_part_node_count

        ntw_geom_x = ncfile.createVariable(
            "network1d_geom_x", np.float64, ("network1d_nGeometryNodes")
        )
        ntw_geom_x.standard_name = "projection_x_coordinate"
        ntw_geom_x.long_name = "x-coordinate of branch geometry nodes"
        ntw_geom_x.units = "m"
        ntw_geom_x[:] = mesh1d.network1d_geom_x

        ntw_geom_y = ncfile.createVariable(
            "network1d_geom_y", np.float64, ("network1d_nGeometryNodes")
        )
        ntw_geom_y.standard_name = "projection_y_coordinate"
        ntw_geom_y.long_name = "y-coordinate of branch geometry nodes"
        ntw_geom_y.units = "m"
        ntw_geom_y[:] = mesh1d.network1d_geom_y

    def _set_1dmesh(self, ncfile: nc.Dataset, mesh1d: Mesh1d) -> None:  # type: ignore[import]

        nc_mesh1d = ncfile.createVariable("mesh1d", "i4", ())
        nc_mesh1d.cf_role = "mesh_topology"
        nc_mesh1d.long_name = "Topology data of 1D Mesh"
        nc_mesh1d.coordinate_space = "network1d"
        nc_mesh1d.edge_dimension = "mesh1d_nEdges"
        nc_mesh1d.edge_node_connectivity = "mesh1d_edge_nodes"
        nc_mesh1d.edge_coordinates = "mesh1d_edge_branch mesh1d_edge_offset"
        nc_mesh1d.node_coordinates = "mesh1d_node_branch mesh1d_node_offset"
        nc_mesh1d.node_dimension = "mesh1d_nNodes"
        nc_mesh1d.node_id = "mesh1d_node_id"
        nc_mesh1d.node_long_name = "mesh1d_node_long_name"
        nc_mesh1d.topology_dimension = 1

        mesh1d_node_id = ncfile.createVariable(
            "mesh1d_node_id", "c", ("mesh1d_nNodes", "idstrlength")
        )
        mesh1d_node_id.long_name = "ID of mesh nodes"
        mesh1d_node_id[:] = self.to_char_list(mesh1d.mesh1d_node_id, self.idstrlength)

        mesh1d_node_longname = ncfile.createVariable(
            "mesh1d_node_long_name", "c", ("mesh1d_nNodes", "longstrlength")
        )
        mesh1d_node_longname.long_name = "Long name of mesh nodes"
        mesh1d_node_longname[:] = self.to_char_list(
            mesh1d.mesh1d_node_long_name, self.longstrlength
        )

        mesh1d_edge_node = ncfile.createVariable(
            "mesh1d_edge_nodes", "i4", ("mesh1d_nEdges", "Two")
        )
        mesh1d_edge_node.cf_role = "edge_node_connectivity"
        mesh1d_edge_node.long_name = "Start and end nodes of mesh edges"
        mesh1d_edge_node.start_index = 1
        mesh1d_edge_node[:] = mesh1d.mesh1d_edge_nodes + mesh1d_edge_node.start_index

        mesh1d_edge_branch = ncfile.createVariable(
            "mesh1d_edge_branch", "i4", "mesh1d_nEdges"
        )
        mesh1d_edge_branch.long_name = "Index of branch on which mesh edges are located"
        mesh1d_edge_branch.start_index = 1
        mesh1d_edge_branch[:] = (
            mesh1d.mesh1d_edge_branch_id + mesh1d_edge_branch.start_index
        )

        mesh1d_edge_offset = ncfile.createVariable(
            "mesh1d_edge_offset", np.float64, "mesh1d_nEdges"
        )
        mesh1d_edge_offset.long_name = "Offset along branch of mesh edges"
        mesh1d_edge_offset.units = "m"
        mesh1d_edge_offset[:] = mesh1d.mesh1d_edge_branch_offset

        mesh1d_node_branch = ncfile.createVariable(
            "mesh1d_node_branch", "i4", "mesh1d_nNodes"
        )
        mesh1d_node_branch.long_name = "Index of branch on which mesh nodes are located"
        mesh1d_node_branch.start_index = 1
        mesh1d_node_branch[:] = (
            mesh1d.mesh1d_node_branch_id + mesh1d_node_branch.start_index
        )

        mesh1d_node_offset = ncfile.createVariable(
            "mesh1d_node_offset", np.float64, "mesh1d_nNodes", fill_value=np.nan
        )
        mesh1d_node_offset.long_name = "Offset along branch of mesh nodes"
        mesh1d_node_offset.units = "m"
        mesh1d_node_offset[:] = mesh1d.mesh1d_node_branch_offset

    def _set_2dmesh(self, ncfile: nc.Dataset, mesh2d: Mesh2d) -> None:  # type: ignore[import]

        nc_mesh2d = ncfile.createVariable("mesh2d", "i4", ())
        nc_mesh2d.long_name = "Topology data of 2D network"
        nc_mesh2d.topology_dimension = 2
        nc_mesh2d.cf_role = "mesh_topology"
        nc_mesh2d.node_coordinates = "mesh2d_node_x mesh2d_node_y"
        nc_mesh2d.node_dimension = "mesh2d_nNodes"
        nc_mesh2d.edge_coordinates = "mesh2d_edge_x mesh2d_edge_y"
        nc_mesh2d.edge_dimension = "mesh2d_nEdges"
        nc_mesh2d.edge_node_connectivity = "mesh2d_edge_nodes"
        nc_mesh2d.face_node_connectivity = "mesh2d_face_nodes"
        nc_mesh2d.max_face_nodes_dimension = "max_nmesh2d_face_nodes"
        nc_mesh2d.face_dimension = "mesh2d_nFaces"
        nc_mesh2d.face_coordinates = "mesh2d_face_x mesh2d_face_y"

        # Nodes:
        mesh2d_node_x = ncfile.createVariable(
            "mesh2d_node_x", np.float64, nc_mesh2d.node_dimension
        )
        mesh2d_node_y = ncfile.createVariable(
            "mesh2d_node_y", np.float64, nc_mesh2d.node_dimension
        )
        mesh2d_node_z = ncfile.createVariable(
            "mesh2d_node_z", np.float64, nc_mesh2d.node_dimension, fill_value=np.nan
        )

        mesh2d_node_x.standard_name = "projection_x_coordinate"
        mesh2d_node_y.standard_name = "projection_y_coordinate"
        mesh2d_node_z.standard_name = "altitude"

        for var, dim in zip([mesh2d_node_x, mesh2d_node_y, mesh2d_node_z], list("xyz")):
            setattr(var, "units", "m")
            setattr(var, "mesh", "mesh2d")
            setattr(var, "location", "node")
            setattr(var, "long_name", f"{dim}-coordinate of mesh nodes")

        mesh2d_node_z.coordinates = "mesh2d_node_x mesh2d_node_y"
        mesh2d_node_z.grid_mapping = ""

        mesh2d_node_x[:] = mesh2d.mesh2d_node_x
        mesh2d_node_y[:] = mesh2d.mesh2d_node_y

        mesh2d_en = ncfile.createVariable(
            "mesh2d_edge_nodes",
            "i4",
            (nc_mesh2d.edge_dimension, "Two"),
            fill_value=np.iinfo(np.int32).min,
        )
        mesh2d_en.cf_role = "edge_node_connectivity"
        mesh2d_en.long_name = "maps every edge to the two nodes that it connects"
        mesh2d_en.start_index = 1
        mesh2d_en.location = "edge"
        mesh2d_en.mesh = "mesh2d"
        mesh2d_en[:] = mesh2d.mesh2d_edge_nodes + mesh2d_en.start_index

        mesh2d_fn = ncfile.createVariable(
            "mesh2d_face_nodes",
            "i4",
            (nc_mesh2d.face_dimension, nc_mesh2d.max_face_nodes_dimension),
            fill_value=np.iinfo(np.int32).min,
        )
        mesh2d_fn.cf_role = "face_node_connectivity"
        mesh2d_fn.mesh = "mesh2d"
        mesh2d_fn.location = "face"
        mesh2d_fn.long_name = "maps every face to the nodes that it defines"
        mesh2d_fn.start_index = 1
        mesh2d_fn[:] = mesh2d.mesh2d_face_nodes + mesh2d_fn.start_index

        mesh2d_face_x = ncfile.createVariable(
            "mesh2d_face_x", np.float64, nc_mesh2d.face_dimension
        )
        mesh2d_face_y = ncfile.createVariable(
            "mesh2d_face_y", np.float64, nc_mesh2d.face_dimension
        )
        mesh2d_face_z = ncfile.createVariable(
            "mesh2d_face_z", np.float64, nc_mesh2d.face_dimension, fill_value=np.nan
        )

        for var, dim in zip([mesh2d_face_x, mesh2d_face_y, mesh2d_face_z], list("xyz")):
            setattr(var, "units", "m")
            setattr(var, "mesh", "mesh2d")
            setattr(var, "location", "face")
            setattr(
                var,
                "standard_name",
                f"projection_{dim}_coordinate" if dim != "z" else "altitude",
            )
            setattr(var, "long_name", f"{dim}-coordinate of face nodes")

        mesh2d_face_z.coordinates = "mesh2d_face_x mesh2d_face_y"
        mesh2d_face_z.grid_mapping = ""

        mesh2d_face_x[:] = mesh2d.mesh2d_face_x
        mesh2d_face_y[:] = mesh2d.mesh2d_face_y

        # Assign altitude data
        # To faces
        if mesh2d.mesh2d_face_z.size > 0:
            mesh2d_face_z[:] = mesh2d.mesh2d_face_z
        # Assign to nodes
        if mesh2d.mesh2d_node_z.size > 0:
            mesh2d_node_z[:] = mesh2d.mesh2d_node_z

    def _set_1d2dlinks(self, ncfile: nc.Dataset, link1d2d: Link1d2d) -> None:  # type: ignore[import]
        nc_link1d2d = ncfile.createVariable(
            "link1d2d",
            "i4",
            ("nLink1D2D_edge", "Two"),
        )
        nc_link1d2d.cf_role = "mesh_topology_contact"
        nc_link1d2d.contact = "mesh1d:node mesh2d:face"
        nc_link1d2d.contact_type = "link1d2d_contact_type"
        nc_link1d2d.contact_ids = "link1d2d_ids"
        nc_link1d2d.contact_long_names = "link1d2d_long_names"
        nc_link1d2d.start_index = 1
        nc_link1d2d[:, :] = link1d2d.link1d2d + nc_link1d2d.start_index

        link1d2d_ids = ncfile.createVariable(
            "link1d2d_ids", "c", ("nLink1D2D_edge", "idstrlength")
        )
        link1d2d_ids.long_name = "ids of the contact"
        link1d2d_ids[:] = self.to_char_list(link1d2d.link1d2d_id, self.idstrlength)

        link1d2d_long_names = ncfile.createVariable(
            "link1d2d_long_names", "c", ("nLink1D2D_edge", "longstrlength")
        )
        link1d2d_long_names.long_name = "long names of the contact"
        link1d2d_long_names[:] = self.to_char_list(
            link1d2d.link1d2d_long_name, self.longstrlength
        )

        link1d2d_contact_type = ncfile.createVariable(
            "link1d2d_contact_type",
            "i4",
            "nLink1D2D_edge",
            fill_value=np.iinfo(np.int32).min,
        )
        link1d2d_contact_type[:] = link1d2d.link1d2d_contact_type

    def str2chars(self, string, size):
        return string.ljust(size)[:size]
