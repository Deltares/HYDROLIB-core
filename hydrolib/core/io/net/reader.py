import json
from pathlib import Path

import meshkernel as mk
import netCDF4 as nc
import numpy as np


class UgridReader:
    def __init__(self, file: Path) -> None:

        self.ncfile = file
        if not file.exists():
            raise OSError(f'File "{file}" not found.')

        self._explorer = NCExplorer(file)

    def read_mesh1d_network1d(self, mesh1d) -> None:
        # TODO How do refer to type without circular imports?

        """
        Read Ugrid from netcdf and return dflowfm cstructure with grid
        """
        # If the mesh is not given (default), use the networks one
        ds = nc.Dataset(self.ncfile)

        # Read mesh1d
        for meshkey, nckey in self._explorer.mesh1d_var_dict.items():
            setattr(mesh1d, meshkey, self._read_nc_attribute(ds[nckey]))

        # Read network variables
        for meshkey, nckey in self._explorer.network1d_var_dict.items():
            setattr(mesh1d, meshkey, self._read_nc_attribute(ds[nckey]))

        # Process network
        mesh1d._process_network1d()

        # self.network.mesh1d.add_from_other(mesh1d)

        ds.close()

    def read_mesh2d(self, mesh2d) -> None:

        ds = nc.Dataset(self.ncfile)

        # Read mesh1d
        for meshkey, nckey in self._explorer.mesh2d_var_dict.items():
            setattr(mesh2d, meshkey, self._read_nc_attribute(ds[nckey]))

        ds.close()

    def read_link1d2d(self, link1d2d) -> None:

        ds = nc.Dataset(self.ncfile)

        # Read mesh1d
        for meshkey, nckey in self._explorer.link1d2d_var_dict.items():
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
            arr = np.array(list(map(str.strip, nc.chartostring(values.data))))

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


class NCExplorer:
    def __init__(self, file: Path):

        self.ds = nc.Dataset(file)

        # Get the ugrid version
        ugrid_version = float(self.ds.Conventions.split("-")[-1])

        # Read the key conventions from json, based on nc version number
        with open(Path(__file__).parent.joinpath("ugrid_conventions.json"), "r") as f:
            variable_names = json.load(f)

        self.network1d_var_dict = variable_names["network1d"]
        self.mesh1d_var_dict = variable_names["mesh1d"]
        self.mesh2d_var_dict = variable_names["mesh2d"]
        self.link1d2d_var_dict = variable_names["link1d2d"]

        self.network1d_key = None
        self.mesh1d_key = None
        self.mesh2d_key = None
        self.link1d2d_key = None

        self._get_mesh1d_network1d_key()
        self._get_mesh2d_key()
        self._get_link1d2d_key()

        self._update_dicts()

        self.ds.close()

    def _get_mesh1d_network1d_key(self) -> None:
        for var_key, ncdata in self.ds.variables.items():
            attributes = ncdata.ncattrs()
            if (
                (("cf_role" in attributes) and (ncdata.getncattr("cf_role") == "mesh_topology"))
                and (("topology_dimension" in attributes) and (ncdata.getncattr("topology_dimension") == 1))
                and ("coordinate_space" in attributes)
            ):
                self.mesh1d_key = var_key
                self.network1d_key = ncdata.getncattr("coordinate_space")
                break

    def _get_mesh2d_key(self) -> None:
        for var_key, ncdata in self.ds.variables.items():
            attributes = ncdata.ncattrs()
            if (("cf_role" in attributes) and (ncdata.getncattr("cf_role") == "mesh_topology")) and (
                ("topology_dimension" in attributes) and (ncdata.getncattr("topology_dimension") == 2)
            ):
                self.mesh2d_key = var_key
                break

    def _get_link1d2d_key(self) -> None:
        for var_key, ncdata in self.ds.variables.items():
            attributes = ncdata.ncattrs()
            if ("cf_role" in attributes) and (ncdata.getncattr("cf_role") == "mesh_topology_contact"):
                self.link1d2d_key = var_key
                break

    def _update_dicts(self):
        """Prepend the key to each dictionary value
        Check existance of values from dictionary in netcdf"""
        # Add deduced keys to dictionary
        if self.network1d_key is not None:
            self.network1d_var_dict = {
                k: [self.network1d_key + v for v in vs] for k, vs in self.network1d_var_dict.items()
            }
            self._check_existance(self.network1d_var_dict)

        if self.mesh1d_key is not None:
            self.mesh1d_var_dict = {k: [self.mesh1d_key + v for v in vs] for k, vs in self.mesh1d_var_dict.items()}
            self._check_existance(self.mesh1d_var_dict)

        if self.mesh2d_key is not None:
            self.mesh2d_var_dict = {k: [self.mesh2d_key + v for v in vs] for k, vs in self.mesh2d_var_dict.items()}
            self._check_existance(self.mesh2d_var_dict)

        if self.link1d2d_key is not None:
            self.link1d2d_var_dict = {
                k: [self.link1d2d_key + v for v in vs] for k, vs in self.link1d2d_var_dict.items()
            }
            self._check_existance(self.link1d2d_var_dict)

    def _check_existance(self, dct: dict) -> None:
        ncvariables = list(self.ds.variables.keys())
        for key, values in dct.items():
            # Save origional for error message
            original = values[:]
            # Remove all values that are not in the netcdf
            for v in reversed(values):
                if v not in ncvariables:
                    values.remove(v)
            # One variable should remain
            if len(values) == 0:
                raise KeyError(f'An attribute for "{key}" was not found in nc file. Expected "{"/".join(original)}"')
            elif len(values) > 1:
                raise KeyError(f'Multiple attributes for "{key}" were found in nc file. Got "{" and ".join(values)}"')

            # Update the dictionary from a list to a single string
            dct[key] = values[0]
