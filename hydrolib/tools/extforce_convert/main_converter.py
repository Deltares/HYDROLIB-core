"""Converter for old external forcing files to the new format."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from tqdm import tqdm

from hydrolib.core.base.file_manager import PathOrStr
from hydrolib.core.base.utils import PathStyle
from hydrolib.core.dflowfm.ext.models import (
    Boundary,
    ExtModel,
    Lateral,
    Meteo,
    SourceSink,
)
from hydrolib.core.dflowfm.extold.models import ExtOldModel
from hydrolib.core.dflowfm.inifield.models import (
    IniFieldModel,
    InitialField,
    ParameterField,
)
from hydrolib.core.dflowfm.structure.models import Structure, StructureModel
from hydrolib.tools.extforce_convert.converters import (
    BoundaryConditionConverter,
    ConverterFactory,
    InitialConditionConverter,
    ParametersConverter,
    SourceSinkConverter,
)
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser
from hydrolib.tools.extforce_convert.utils import (
    CONVERTER_DATA,
    backup_file,
    construct_filemodel_new_or_existing,
    path_relative_to_parent,
)


class ExternalForcingConverter:
    """Converter for old external forcing files to the new format."""

    def __init__(
        self,
        extold_model: Union[PathOrStr, ExtOldModel],
        ext_file: Optional[PathOrStr] = None,
        inifield_file: Optional[PathOrStr] = None,
        structure_file: Optional[PathOrStr] = None,
        mdu_parser: MDUParser = None,
        verbose: bool = False,
        path_style: PathStyle = None,
        debug: Optional[bool] = False,
    ):
        r"""Initialize the converter.

        The converter will create new external forcing, initial field and structure files in the same directory as the
        old external forcing file, if no paths were given by the user for the new models.

        Args:
            extold_model (PathOrStr, ExtOldModel):
                ExtOldModel or path to the old external forcing file. if `ExtOldModel` without a filepath the
                `ExtOldModel` will be assumed to be in the, current working directory.
            ext_file (PathOrStr, optional):
                Path to the new external forcing file.
            inifield_file (PathOrStr, optional):
                Path to the initial field file.
            structure_file (PathOrStr, optional):
                Path to the structure file.
            mdu_parser (Optional[MDUParser], optional):
                a Parser for the MDU file.
            verbose (bool, optional, Defaults to False):
                Enable verbose output.
            path_style (Optional[PathStyle], optional):
                Specifies how absolute paths in model files are interpreted and converted (unix or windows style).
                Use this to correctly handle Unix paths on Windows or Windows paths on Unix.
                If None, the system's default style is used.
                - Example (Windows): `P:/path/to/file`
                - Example (Unix): `/p/path/to/file`
            debug (bool, Optional):
                Enable debug mode. In debug mode unsupported quantities will be skipped and not raise an error.
                Defaults to False.

        Raises:
            FileNotFoundError: If the old external forcing file does not exist.

        Examples:
            - Create a converter from old external forcing object:
            ```python
            >>> from hydrolib.core.dflowfm.extold.models import ExtOldModel
            >>> root_dir = Path("path/to/your/root/dir")
            >>> forcing_data = {
            ...     'QUANTITY': 'windspeedfactor',
            ...     'FILENAME': rf'{root_dir}/my-poly-file.pol',
            ...     'FILETYPE': '11',
            ...     'METHOD': '4',
            ...     'OPERAND': 'O',
            ... }
            >>> forcing_model_data = {
            ... 'comment': [' Example (old-style) external forcings file'],
            ... 'forcing': [forcing_data]
            ... }
            >>> old_model = ExtOldModel(**forcing_model_data) #doctest: +SKIP
            >>> converter = ExternalForcingConverter(extold_model=old_model) #doctest: +SKIP

            ```
            - Create a converter from an old external forcing file:
            ```python
            >>> converter = ExternalForcingConverter("old-external-forcing.ext") #doctest: +SKIP
            >>> converter.update() #doctest: +SKIP
            ```
        """
        if isinstance(extold_model, Path) or isinstance(extold_model, str):
            # if the extold model is given as path/str then read the file
            extold_model = self._read_old_file(extold_model, path_style=path_style)
        else:
            if not isinstance(extold_model, ExtOldModel):
                raise TypeError(
                    "extold_model must be a PathOrStr or ExtOldModel instance."
                )

        # if the mdu is not given then the root dir is the same as the extold model
        if mdu_parser is not None:
            rdir = mdu_parser.mdu_path.parent
        else:
            rdir = extold_model.filepath.parent

        self._extold_model = extold_model
        self._verbose = verbose
        self._root_dir = rdir
        self._path_style = path_style

        # create the new models if not provided by the user in the same directory as the old external file
        path = rdir / "new-external-forcing.ext" if ext_file is None else ext_file
        self._ext_model = construct_filemodel_new_or_existing(
            ExtModel, path, recurse=False
        )

        path = (
            rdir / "new-initial-conditions.ini"
            if inifield_file is None
            else inifield_file
        )
        self._inifield_model = construct_filemodel_new_or_existing(
            IniFieldModel, path, recurse=False
        )

        path = rdir / "new-structure.ini" if structure_file is None else structure_file
        self._structure_model = construct_filemodel_new_or_existing(
            StructureModel, path, recurse=False
        )

        if mdu_parser is not None:
            self.temperature_salinity_data: Dict[str, int] = (
                mdu_parser.temperature_salinity_data
            )
            self._mdu_parser = mdu_parser

        self._legacy_files = []
        self.debug = debug
        self.un_supported_quantities = self.check_unsupported_quantities()

    def check_unsupported_quantities(self):
        """Check for unsupported quantities in the old external forcing model.

        Returns:
            list[str]: List of unsupported quantities found in the old external forcing model.
        """
        # check if the file contains unsupported quantities
        return CONVERTER_DATA.check_unsupported_quantities(
            self.extold_model, raise_error=not self.debug
        )

    @property
    def legacy_files(self) -> list[Path]:
        """List of legacy files that were created during the conversion."""
        return self._legacy_files

    @legacy_files.setter
    def legacy_files(self, value: list[Path]):
        """Set the legacy files."""
        if not isinstance(value, list):
            raise TypeError("legacy_files must be a list of Path objects.")
        self._legacy_files += value

    @property
    def verbose(self) -> bool:
        """bool: Enable verbose output."""
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool):
        self._verbose = value

    @property
    def mdu_parser(self) -> MDUParser:
        if hasattr(self, "_mdu_parser"):
            val = self._mdu_parser
        else:
            val = None
        return val

    @property
    def root_dir(self) -> Path:
        """Root directory of the external forcing file."""
        return self._root_dir

    @property
    def path_style(self) -> PathStyle:
        """Path style for the absolute paths in the models."""
        return self._path_style

    @property
    def extold_model(self) -> ExtOldModel:
        """Old external forcing model."""
        return self._extold_model

    @property
    def ext_model(self) -> ExtModel:
        """New External forcing Model."""
        if not hasattr(self, "_ext_model"):
            raise ValueError(
                "ext_model not set, please use the `ext_model` setter. to set it."
            )
        return self._ext_model

    @ext_model.setter
    def ext_model(self, path: PathOrStr):
        """New external forcing model.

        Args:
            path (PathOrStr, optional): Path to the new external forcing file.
        """
        self._ext_model = construct_filemodel_new_or_existing(ExtModel, path)

    @property
    def inifield_model(self) -> IniFieldModel:
        """IniFieldModel: object with all initial fields blocks."""
        if not hasattr(self, "_inifield_model"):
            raise ValueError(
                "inifield_model not set, please use the `inifield_model` setter. to set it."
            )
        return self._inifield_model

    @inifield_model.setter
    def inifield_model(self, path: PathOrStr):
        self._inifield_model = construct_filemodel_new_or_existing(IniFieldModel, path)

    @property
    def structure_model(self) -> StructureModel:
        """StructureModel: object with all structure blocks."""
        if not hasattr(self, "_structure_model"):
            raise ValueError(
                "structure_model not set, please use the `structure_model` setter. to set it."
            )
        return self._structure_model

    @structure_model.setter
    def structure_model(self, path: PathOrStr):
        self._structure_model = construct_filemodel_new_or_existing(
            StructureModel, path
        )

    @staticmethod
    def _read_old_file(
        ext_old_file: PathOrStr, path_style: Optional[PathStyle] = None
    ) -> ExtOldModel:
        """Read a legacy D-Flow FM external forcings file (.ext) into an ExtOldModel object.

        Args:
            ext_old_file (PathOrStr):
                path to the external forcings file (.ext)
            path_style (Optional[PathStyle]):
                Path style for the file paths in the models. If None, the system style is used.
                Converts absolute paths based on the provided style to the system style.

            Returns:
                ExtOldModel: object with all forcing blocks.

            Raises:
                FileNotFoundError: If the old external forcing file does not exist.
        """
        if not isinstance(ext_old_file, Path):
            ext_old_file = Path(ext_old_file)

        if not ext_old_file.exists():
            raise FileNotFoundError(f"File not found: {ext_old_file}")

        ext_old_model = ExtOldModel(ext_old_file, path_style=path_style)

        return ext_old_model

    def _type_field_map(self) -> dict[type, tuple[Any, str]]:
        return {
            Boundary: (self.ext_model, "boundary"),
            Lateral: (self.ext_model, "lateral"),
            SourceSink: (self.ext_model, "sourcesink"),
            Meteo: (self.ext_model, "meteo"),
            InitialField: (self.inifield_model, "initial"),
            ParameterField: (self.inifield_model, "parameter"),
            Structure: (self.structure_model, "structure"),
        }

    def update(
        self,
    ) -> Union[Tuple[ExtModel, IniFieldModel, StructureModel], None]:
        """Convert the old external forcing file to a new format files.

        Notes:
            - When the output files exist, output will be appended to them.
            - If there is a new external forcing file, the converted quantities will be appended to it, otherwise a new
            external forcing file will be created.
            - If there is an initial field file, the converted quantities will be appended to it, otherwise a new initial
            field file will be created in the same directory as the mdu file, and the `IniFieldFile` field will be
            added/updated in the geometry section in the mdu file.

        Returns:
            Tuple[ExtOldModel, ExtModel, IniFieldModel, StructureModel]:
                The updated models (already written to disk). Maybe used
                at call site to inspect the updated models.
        """
        self._log_conversion_details()
        num_quantities = len(self.extold_model.forcing)

        type_field_map = self._type_field_map()

        with tqdm(
            total=num_quantities, desc="Converting forcings", unit="forcing"
        ) as progress_bar:
            for forcing in self.extold_model.forcing:
                if forcing.quantity.lower() in self.un_supported_quantities:
                    print(
                        f"The quantity {forcing.quantity} is not supported, and the debug mode is {self.debug}. "
                        "So the forcing will not be converted (stay in the old external forcing file)."
                    )
                    progress_bar.update(1)
                    continue

                # Update the description of tqdm to include the current forcing's filepath
                progress_bar.set_description(
                    f"Processing: {forcing.quantity} - {forcing.filename.filepath}"
                )

                new_quantity_block = self._convert_forcing(forcing)
                model_field = type_field_map.get(type(new_quantity_block))

                if model_field is None:
                    raise NotImplementedError(
                        f"Unsupported model class {type(new_quantity_block)} for {forcing.quantity} in "
                        f"{self.extold_model.filepath}."
                    )

                model, attr = model_field
                setattr(model, attr, getattr(model, attr) + [new_quantity_block])

                progress_bar.update(1)

        if self.mdu_parser is not None:
            self._update_mdu_file()

        if self.un_supported_quantities:
            # replace the forcings by the forcings that were not converted (the unsupported quantities)
            forcing = [
                forcing
                for forcing in self.extold_model.forcing
                if forcing.quantity.lower() in self.un_supported_quantities
            ]
            self.extold_model.forcing = forcing

        return self.ext_model, self.inifield_model, self.structure_model

    def _convert_forcing(self, forcing) -> Union[Boundary, Lateral, Meteo, SourceSink]:
        """Convert a single forcing block to the appropriate new format.

        Notes:
            - The SourceSink converter needs the salinity and temperature from the FM model.
            - The BoundaryCondition converter needs the start time from the FM model.
        """
        converter_class = ConverterFactory.create_converter(forcing.quantity)
        converter_class.root_dir = self.root_dir

        # only the SourceSink converter needs the quantities' list
        if isinstance(converter_class, SourceSinkConverter):

            if self.temperature_salinity_data is None:
                raise ValueError(
                    "FM model is required to convert SourcesSink quantities."
                )
            else:
                temp_salinity_mdu = self.temperature_salinity_data
                start_time = self.temperature_salinity_data.get("refdate")

            quantities = self.extold_model.quantities
            new_quantity_block = converter_class.convert(
                forcing, quantities, start_time=start_time, **temp_salinity_mdu
            )
        elif isinstance(converter_class, BoundaryConditionConverter):
            if self.temperature_salinity_data is None:
                raise ValueError("FM model is required to convert Boundary conditions.")
            else:
                start_time = self.temperature_salinity_data.get("refdate")
                new_quantity_block = converter_class.convert(forcing, start_time)
        elif isinstance(
            converter_class, (InitialConditionConverter, ParametersConverter)
        ):
            forcing_path = path_relative_to_parent(
                forcing,
                self.inifield_model.filepath,
                self.extold_model.filepath,
                self.mdu_parser,
            )
            new_quantity_block = converter_class.convert(forcing, forcing_path)
        else:
            new_quantity_block = converter_class.convert(forcing)

        if hasattr(converter_class, "legacy_files"):
            self.legacy_files = converter_class.legacy_files

        return new_quantity_block

    def save(self, backup: bool = True, recursive: bool = True):
        """Save the updated models to disk.

        Args:
            backup (bool, optional):
                Create a backup of each file that will be overwritten.
            recursive (bool, optional): Defaults to True.
                Save the models recursively.
        """
        num_quantities_inifield = len(self.inifield_model.parameter) + len(
            self.inifield_model.initial
        )
        if num_quantities_inifield > 0:
            self._save_inifield_model(backup, recursive)

        if len(self.structure_model.structure) > 0:
            self._save_structure_model(backup, recursive)

        if self.un_supported_quantities:
            backup_file(self.extold_model.filepath)
            self.extold_model.save(recurse=recursive, exclude_unset=True)

        num_quantities_ext = (
            len(self.ext_model.meteo)
            + len(self.ext_model.sourcesink)
            + len(self.ext_model.boundary)
            + len(self.ext_model.lateral)
        )
        if num_quantities_ext:
            if backup and self.ext_model.filepath.exists():
                backup_file(self.ext_model.filepath)
            self.ext_model.save(
                recurse=recursive, exclude_unset=True, path_style=self.path_style
            )

        if self.mdu_parser is not None:
            self.mdu_parser.clean()
            self.mdu_parser.save(backup=backup)

    def _save_inifield_model(self, backup: bool, recursive: bool):
        """
        The save method for the IniFieldModel.
        the exclude_unset parameter is set to False, to save the general section with the fileversion section as
        required by the Fortran kernel.
        """
        if backup and self.inifield_model.filepath.exists():
            backup_file(self.inifield_model.filepath)
        self.inifield_model.save(
            recurse=recursive, exclude_unset=False, path_style=self.path_style
        )

    def _save_structure_model(self, backup: bool, recursive: bool):
        if backup and self.structure_model.filepath.exists():
            backup_file(self.structure_model.filepath)
        self.structure_model.save(
            recurse=recursive, exclude_unset=True, path_style=self.path_style
        )

    def clean(self):
        """Clean the directory from the old external forcing file and the time file."""
        if len(self.legacy_files) > 0:
            for file in self.legacy_files:
                print(f"Removing legacy file:{file}")
                file.unlink()

        if not self.un_supported_quantities:
            self.extold_model.filepath.unlink()

    @classmethod
    def from_mdu(
        cls,
        mdu_file: PathOrStr,
        ext_file_user: Optional[PathOrStr] = None,
        inifield_file_user: Optional[PathOrStr] = None,
        structure_file_user: Optional[PathOrStr] = None,
        path_style: Optional[PathStyle] = None,
        debug: bool = False,
    ) -> "ExternalForcingConverter":
        """Create the converter from the MDU file.

        Args:
            mdu_file (PathOrStr): Path to the D-Flow FM main input file (.mdu).
                Must be parsable into a standard FMModel.
                When this contains a valid filename for ExtFile, conversion
                will be performed.
            ext_file_user (PathOrStr, optional): Path to the output external forcings
                file. Defaults to the given ExtForceFileNew in the MDU file, if
                present, or forcings.ext otherwise.
            inifield_file_user (PathOrStr, optional): Path to the output initial field
                file. Defaults to the given IniFieldFile in the MDU file, if
                present, or inifields.ini otherwise.
            structure_file_user (PathOrStr, optional): Path to the output structures.ini
                file. Defaults to the given StructureFile in the MDU file, if
                present, or structures.ini otherwise.
            path_style (Optional[PathStyle], optional):
                Path style for the file paths in the models. If None, the system style is used.
                Converts absolute paths based on the provided style to the system style.
            debug (bool, Optional):
                Enable debug mode. In debug mode unsupported quantities will be skipped and not raise an error.
                Defaults to False.

        Returns:
            ExternalForcingConverter: The converter object.

        Raises:
            FileNotFoundError: If the MDU file does not exist.
            ValueError: If the old external forcing file is not found in the MDU file.
            DeprecationWarning: If the MDU file contains unknown keywords.
        """
        mdu_parser = MDUParser(mdu_file)

        extoldfile = (
            mdu_parser.mdu_path.parent / mdu_parser.extforce_block.extforce_file
        )

        ext_file_user = mdu_parser.extforce_block.get_new_extforce_file(ext_file_user)
        inifield_file_user = mdu_parser.get_inifield_file(inifield_file_user)
        structure_file_user = mdu_parser.get_structure_file(structure_file_user)

        return cls(
            extoldfile,
            ext_file_user,
            inifield_file_user,
            structure_file_user,
            mdu_parser,
            path_style=path_style,
            debug=debug,
        )

    def _update_mdu_file(self):
        """Update the MDU file with the new external forcings files, initial fields and structures files.

        Notes:
            - The MDU file is updated in place.
            - The InifieldFile and StructureFile blocks are updated only if they were not present in the file,
            if not, they will be created in the same directory as the mdu file.
        """
        num_ext_model_quantities = (
            len(self.ext_model.boundary)
            + len(self.ext_model.lateral)
            + len(self.ext_model.meteo)
            + len(self.ext_model.sourcesink)
        )

        remove_old_ext_file = False if self.un_supported_quantities else True

        self.mdu_parser.update_extforce_file_new(
            self.ext_model.filepath.name,
            num_quantities=num_ext_model_quantities,
            remove_old_ext_file=remove_old_ext_file,
        )

        num_quantities_inifield = len(self.inifield_model.parameter) + len(
            self.inifield_model.initial
        )

        if num_quantities_inifield > 0:
            self.mdu_parser.update_inifield_file(self.inifield_model.filepath.name)

        if len(self.structure_model.structure) > 0:
            self.mdu_parser.update_structure_file(self.structure_model.filepath.name)

    def _log_conversion_details(self):
        """Log details about the conversion process if verbosity is enabled."""
        if self.verbose:
            workdir = os.getcwd() + "\\"
            print(f"Work dir: {workdir}")
            print("Using attribute files:")
            print("Input:")
            print(f"* {self.extold_model.filepath}")
            print("Output:")
            print(f"* {self.ext_model.filepath}")
            print(f"* {self.inifield_model.filepath}")
            print(f"* {self.structure_model.filepath}")


def recursive_converter(
    root_dir: PathOrStr,
    backup: bool = True,
    suppress_errors: bool = False,
    remove_legacy: bool = False,
    debug: bool = False,
):
    """Migrate all external forcings files in a directory tree to the new format.

    Args:
        root_dir: Directory to recursively find and convert .mdu files in.
        backup (bool, optional): Create a backup of each file that will be overwritten.
        suppress_errors (bool, optional): Suppress errors during conversion.
        remove_legacy (bool, optional): Remove legacy/old files (e.g. .tim) after conversion. Defaults to False.
        debug (bool, Optional):
                Enable debug mode. In debug mode unsupported quantities will be skipped and not raise an error.
                Defaults to False.
    """
    mdu_files = [
        path for path in Path(root_dir).rglob("*.mdu") if "_ext" not in path.name
    ]

    if not mdu_files:
        print("No .mdu files found in the specified directory.")
    else:
        print(f"Found {len(mdu_files)} .mdu files. Starting conversion...")

        for path in tqdm(mdu_files, desc="Converting files"):
            try:
                converter = ExternalForcingConverter.from_mdu(path, debug=debug)
                _, _, _ = converter.update()
                converter.save(backup=backup)
                if remove_legacy:
                    converter.clean()
            except Exception as e:
                if not suppress_errors:
                    print(f"Error processing {path}: {e}")
