from __future__ import annotations

import json
import logging
from collections import namedtuple
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import netCDF4 as nc
import numpy as np

from hydrolib.core.basemodel import BaseModel

if TYPE_CHECKING:
    from .models import Link1d2d, Mesh1d, Mesh2d


class UgridReader:
    """UgridReader provides the logic to read a specified UGRID file."""

    def __init__(self, file_path: Path) -> None:
        """Creates a new UgridReader, reading the specified path.

        Args:
            file_path (Path): The path to read from.

        Raises:
            OSError: Thrown when file_path does not exist.
        """
        self._ncfile_path = file_path

        if not self._ncfile_path.exists():
            raise OSError(f'File "{self._ncfile_path}" not found.')

        self._explorer = NCExplorer.from_file_path(self._ncfile_path)

    def read_mesh1d_network1d(self, mesh1d: Mesh1d) -> None:
        """
        Read the Ugrid from the netcdf and add the dflowfm cstructure with grid to the
        specified mesh1d.

        Args:
            mesh1d (Mesh1d): The object to which the read network1d is added.
        """
        if (
            self._explorer.mesh1d_var_name_mapping is None
            or self._explorer.network1d_var_name_mapping is None
        ):
            logging.debug(
                "Mesh1d and Network are not found in the dataset, reading is skipped."
            )
            return

        # If the mesh is not given (default), use the networks one
        ds = nc.Dataset(self._ncfile_path)  # type: ignore[import]

        # Read mesh1d
        for meshkey, nckey in self._explorer.mesh1d_var_name_mapping.items():
            setattr(mesh1d, meshkey, self._read_nc_attribute(ds[nckey]))

        # Read network variables
        for meshkey, nckey in self._explorer.network1d_var_name_mapping.items():
            setattr(mesh1d, meshkey, self._read_nc_attribute(ds[nckey]))

        # Process network
        mesh1d._process_network1d()

        ds.close()

    def read_mesh2d(self, mesh2d: Mesh2d) -> None:
        """
        Read the Ugrid from the netcdf and add the dflowfm cstructure with grid to the
        specified mesh2d.

        Args:
            mesh2d (Mesh2d): The object to which the read network1d is added.
        """
        if self._explorer.mesh2d_var_name_mapping is None:
            logging.debug("Mesh2d is not found in the dataset, reading is skipped.")
            return

        ds = nc.Dataset(self._ncfile_path)  # type: ignore[import]

        # Read mesh1d
        for meshkey, nckey in self._explorer.mesh2d_var_name_mapping.items():
            setattr(mesh2d, meshkey, self._read_nc_attribute(ds[nckey]))

        ds.close()

    def read_link1d2d(self, link1d2d: Link1d2d) -> None:
        """Read the Link1d2d from the wrapped netCDF file of this UgridReader.

        Args:
            link1d2d (Link1d2d): The Link1d2d to which the data is added.
        """
        if self._explorer.link1d2d_var_name_mapping is None:
            logging.debug("Link1d2d is not found in the dataset, reading is skipped.")
            return

        ds = nc.Dataset(self._ncfile_path)  # type: ignore[import]

        # Read mesh1d
        for meshkey, nckey in self._explorer.link1d2d_var_name_mapping.items():
            setattr(link1d2d, meshkey, self._read_nc_attribute(ds[nckey]))

        ds.close()

    def _read_nc_attribute(self, attr: nc._netCDF4.Variable) -> np.ndarray:
        """Read values from netcdf attribute.
        - Character arrays are converted to strings
        - Masked arrays are converted to regular arrays where the masked values are filled with the fillvalue
        - The numerical arrays are subtracted by the start value. This is often 1, while python is 0-based.

        Args:
            attr (netCDF4._netCDF4.Variable): Attribute in the file

        Returns:
            np.ndarray: returned array
        """
        values = attr[:]
        if values.dtype == "S1":
            # Convert to strings
            arr = np.array(list(map(str.strip, nc.chartostring(values.data))))  # type: ignore[import]

        else:
            # Get data from masked array
            arr = values[:].data
            # Fill masked values with fillvalue
            if values.mask.any():
                arr[values.mask] = attr._FillValue
            # Substract start index
            if hasattr(attr, "start_index"):
                arr -= attr.start_index

        return arr


class NCExplorer(BaseModel):
    """NCExplorer provides the mapping of the UGRID variable names as used within
    HYDROLIB models to the actual values used within the netCDF file.

    If a component is not present, the corresponding mapping is set to None.
    A NCExplorer can be constructed from a file by using the `from_file_path`
    class method.

    Attributes:
        network1d_var_name_mapping (Optional[Dict[str, str]]):
            The mapping of Network variable names.
        mesh1d_var_name_mapping (Optional[Dict[str, str]]):
            The mapping of Mesh1d variable names.
        mesh2d_var_name_mapping (Optional[Dict[str, str]]):
            The mapping of Mesh2d variable names.
        link1d2d_var_name_mapping (Optional[Dict[str, str]]):
            The mapping of Link1d2d variable names.
    """

    Keys = namedtuple("Keys", ["network1d", "mesh1d", "mesh2d", "link1d2d"])

    network1d_var_name_mapping: Optional[Dict[str, str]]
    mesh1d_var_name_mapping: Optional[Dict[str, str]]
    mesh2d_var_name_mapping: Optional[Dict[str, str]]
    link1d2d_var_name_mapping: Optional[Dict[str, str]]

    @classmethod
    def from_file_path(cls, file_path: Path) -> "NCExplorer":
        """Create a new NCExplorer from the specified file_path.

        Args:
            file_path (Path): The path to the net.nc file.

        Returns:
            NCExplorer: A newly initialized NCExplorer.
        """
        conventions = NCExplorer._read_ugrid_conventions()
        dataset = nc.Dataset(file_path)  # type: ignore[import]

        keys = NCExplorer._determine_keys(dataset)
        network1d_mapping = NCExplorer._retrieve_variable_names_mapping(
            keys.network1d, dataset, conventions["network1d"]
        )
        mesh1d_mapping = NCExplorer._retrieve_variable_names_mapping(
            keys.mesh1d, dataset, conventions["mesh1d"]
        )
        mesh2d_mapping = NCExplorer._retrieve_variable_names_mapping(
            keys.mesh2d, dataset, conventions["mesh2d"]
        )
        link1d2d_mapping = NCExplorer._retrieve_variable_names_mapping(
            keys.link1d2d, dataset, conventions["link1d2d"]
        )

        dataset.close()

        return cls(
            network1d_var_name_mapping=network1d_mapping,
            mesh1d_var_name_mapping=mesh1d_mapping,
            mesh2d_var_name_mapping=mesh2d_mapping,
            link1d2d_var_name_mapping=link1d2d_mapping,
        )

    @staticmethod
    def _read_ugrid_conventions() -> Dict:
        with open(Path(__file__).parent.joinpath("ugrid_conventions.json"), "r") as f:
            return json.load(f)

    @staticmethod
    def _determine_keys(dataset: nc.Dataset) -> NCExplorer.Keys:  # type: ignore[import]
        keys1d = NCExplorer._retrieve_1d_keys(dataset)

        mesh1d = keys1d[0] if keys1d is not None else None
        network1d = keys1d[1] if keys1d is not None else None

        mesh2d = NCExplorer._retrieve_2d_key(dataset)
        link1d2d = NCExplorer._retrieve_1d2d_key(dataset)

        return NCExplorer.Keys(network1d, mesh1d, mesh2d, link1d2d)

    @staticmethod
    def _retrieve_1d_keys(dataset) -> Optional[Tuple[str, str]]:
        def is_mesh1d(ncdata) -> bool:
            return (
                NCExplorer._has_cf_role(ncdata, "mesh_topology")
                and NCExplorer._has_n_topology_dimension(ncdata, 1)
                and NCExplorer._has_attribute(ncdata, "coordinate_space")
            )

        for var_key, ncdata in dataset.variables.items():
            if is_mesh1d(ncdata):
                return var_key, ncdata.getncattr("coordinate_space")
        return None

    @staticmethod
    def _retrieve_2d_key(dataset) -> Optional[str]:
        def is_mesh2d(ncdata) -> bool:
            return NCExplorer._has_cf_role(
                ncdata, "mesh_topology"
            ) and NCExplorer._has_n_topology_dimension(ncdata, 2)

        for var_key, ncdata in dataset.variables.items():
            if is_mesh2d(ncdata):
                return var_key
        return None

    @staticmethod
    def _retrieve_1d2d_key(dataset) -> Optional[str]:
        def is_link1d2d(ncdata) -> bool:
            return NCExplorer._has_cf_role(ncdata, "mesh_topology_contact")

        for var_key, ncdata in dataset.variables.items():
            if is_link1d2d(ncdata):
                return var_key
        return None

    @staticmethod
    def _has_cf_role(ncdata, cf_role_value: str) -> bool:
        return NCExplorer._has_attribute(ncdata, "cf_role", cf_role_value)

    @staticmethod
    def _has_n_topology_dimension(ncdata, n: int) -> bool:
        return NCExplorer._has_attribute(ncdata, "topology_dimension", n)

    @staticmethod
    def _has_attribute(ncdata, name: str, value: Any = None):
        attributes = ncdata.ncattrs()
        return name in attributes and (value is None or ncdata.getncattr(name) == value)

    @staticmethod
    def _retrieve_variable_names_mapping(
        variable_key: Optional[str], dataset, conventions: Dict
    ) -> Optional[Dict]:
        if variable_key is None:
            # particular key does not exist, as such there are no variables either.
            return None

        nc_variables_set = set(dataset.variables.keys())

        result = {}

        for key, value in conventions.items():
            nc_vars = set(variable_key + suffix for suffix in value["suffices"])
            in_dataset = nc_vars & nc_variables_set

            len_in_data_set = len(in_dataset)

            if len_in_data_set == 1:
                result[key] = in_dataset.pop()
            elif len_in_data_set > 1:
                raise KeyError(
                    f'Multiple attributes for "{key}" were found in nc file. Got "{" and ".join(in_dataset)}"'
                )
            elif "is_optional" in value and value["is_optional"]:
                logging.info(
                    "Optional variable '%s' is not present in the nc_file and is skipped",
                    key,
                )
            else:
                raise KeyError(
                    f'An attribute for "{key}" was not found in nc file. Expected "{"/".join(nc_vars)}"'
                )

        return result
