import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from tqdm import tqdm

from hydrolib.core.base.file_manager import PathOrStr
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
from hydrolib.tools.extforce_convert.converters import ConverterFactory
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser
from hydrolib.tools.extforce_convert.utils import (
    backup_file,
    construct_filemodel_new_or_existing,
)


class ExternalForcingConverter:

    def __init__(
        self,
        extold_model: Union[PathOrStr, ExtOldModel],
        ext_file: Optional[PathOrStr] = None,
        inifield_file: Optional[PathOrStr] = None,
        structure_file: Optional[PathOrStr] = None,
        mdu_parser: MDUParser = None,
        verbose: bool = False,
    ):
        """Initialize the converter.

        The converter will create new external forcing, initial field and structure files in the same directory as the
        old external forcing file, if no paths were given by the user for the new models.

        Args:
            extold_model (PathOrStr, ExtOldModel):
                ExtOldModel or path to the old external forcing file.
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

        Raises:
            FileNotFoundError: If the old external forcing file does not exist.

        Examples:
            >>> converter = ExternalForcingConverter("old-external-forcing.ext") #doctest: +SKIP
            >>> converter.update() #doctest: +SKIP
        """
        if isinstance(extold_model, Path) or isinstance(extold_model, str):
            extold_model = self._read_old_file(extold_model)

        self._extold_model = extold_model
        self._verbose = verbose
        rdir = extold_model.filepath.parent
        self._root_dir = rdir

        # create the new models if not provided by the user in the same directory as the old external file
        path = rdir / "new-external-forcing.ext" if ext_file is None else ext_file
        self._ext_model = construct_filemodel_new_or_existing(ExtModel, path)

        path = (
            rdir / "new-initial-conditions.ini"
            if inifield_file is None
            else inifield_file
        )
        self._inifield_model = construct_filemodel_new_or_existing(IniFieldModel, path)

        path = rdir / "new-structure.ini" if structure_file is None else structure_file
        self._structure_model = construct_filemodel_new_or_existing(
            StructureModel, path
        )

        if mdu_parser is not None:
            self.temperature_salinity_data: Dict[str, int] = (
                mdu_parser.temperature_salinity_data
            )
            self._mdu_parser = mdu_parser

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
    def extold_model(self) -> ExtOldModel:
        """old external forcing model."""
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
    def _read_old_file(extoldfile: PathOrStr) -> ExtOldModel:
        """Read a legacy D-Flow FM external forcings file (.ext) into an
               ExtOldModel object.

        Args:
            extoldfile (PathOrStr): path to the external forcings file (.ext)

            Returns:
                ExtOldModel: object with all forcing blocks.

            Raises:
                FileNotFoundError: If the old external forcing file does not exist.
        """
        if not isinstance(extoldfile, Path):
            extoldfile = Path(extoldfile)

        if not extoldfile.exists():
            raise FileNotFoundError(f"File not found: {extoldfile}")

        extold_model = ExtOldModel(extoldfile)

        return extold_model

    def update(
        self,
    ) -> Union[Tuple[ExtModel, IniFieldModel, StructureModel], None]:
        """
        Convert the old external forcing file to a new format files.
        When the output files are existing, output will be appended to them.

        Returns:
            Tuple[ExtOldModel, ExtModel, IniFieldModel, StructureModel]:
                The updated models (already written to disk). Maybe used
                at call site to inspect the updated models.
        """
        self._log_conversion_details()

        for forcing in self.extold_model.forcing:

            new_quantity_block = self._convert_forcing(forcing)

            if isinstance(new_quantity_block, Boundary):
                self.ext_model.boundary.append(new_quantity_block)
            elif isinstance(new_quantity_block, Lateral):
                self.ext_model.lateral.append(new_quantity_block)
            elif isinstance(new_quantity_block, SourceSink):
                self.ext_model.sourcesink.append(new_quantity_block)
            elif isinstance(new_quantity_block, Meteo):
                self.ext_model.meteo.append(new_quantity_block)
            elif isinstance(new_quantity_block, InitialField):
                self.inifield_model.initial.append(new_quantity_block)
            elif isinstance(new_quantity_block, ParameterField):
                self.inifield_model.parameter.append(new_quantity_block)
            elif isinstance(new_quantity_block, Structure):
                self.structure_model.structure.append(new_quantity_block)
            else:
                raise NotImplementedError(
                    f"Unsupported model class {type(new_quantity_block)} for {forcing.quantity} in "
                    f"{self.extold_model.filepath}."
                )

        if self.mdu_parser is not None:
            self._update_mdu_file()

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
        if converter_class.__class__.__name__ == "SourceSinkConverter":

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
        elif converter_class.__class__.__name__ == "BoundaryConditionConverter":
            if self.temperature_salinity_data is None:
                raise ValueError("FM model is required to convert Boundary conditions.")
            else:
                start_time = self.temperature_salinity_data.get("refdate")
                new_quantity_block = converter_class.convert(forcing, start_time)
        else:
            new_quantity_block = converter_class.convert(forcing)

        return new_quantity_block

    def save(self, backup: bool = True, recursive: bool = True):
        """Save the updated models to disk.

        Args:
            backup (bool, optional):
                Create a backup of each file that will be overwritten.
            recursive (bool, optional): Defaults to True.
                Save the models recursively.
        """
        if (
            len(self.inifield_model.parameter) > 0
            or len(self.inifield_model.initial) > 0
        ):
            self._save_inifield_model(backup, recursive)

        if len(self.structure_model.structure) > 0:
            self._save_structure_model(backup, recursive)

        num_quantities_ext = (
            len(self.ext_model.meteo)
            + len(self.ext_model.sourcesink)
            + len(self.ext_model.boundary)
            + len(self.ext_model.lateral)
        )
        if num_quantities_ext:
            if backup and self.ext_model.filepath.exists():
                backup_file(self.ext_model.filepath)
            self.ext_model.save(recurse=recursive)

        if self.mdu_parser is not None:
            self.mdu_parser.save(backup=True)

    def _save_inifield_model(self, backup: bool, recursive: bool):
        if backup and self.inifield_model.filepath.exists():
            backup_file(self.inifield_model.filepath)
        self.inifield_model.save(recurse=recursive)

    def _save_structure_model(self, backup: bool, recursive: bool):
        if backup and self.structure_model.filepath.exists():
            backup_file(self.structure_model.filepath)
        self.structure_model.save(recurse=recursive)

    def clean(self):
        """
        Clean the directory from the old external forcing file and the time file.
        """
        root_dir = self.root_dir
        time_files = list(root_dir.glob("*.tim"))
        if len(time_files) > 0:
            for file in time_files:
                file.unlink()

        self.extold_model.filepath.unlink()

    @classmethod
    def from_mdu(
        cls,
        mdu_file: PathOrStr,
        ext_file: Optional[PathOrStr] = None,
        inifield_file: Optional[PathOrStr] = None,
        structure_file: Optional[PathOrStr] = None,
    ) -> "ExternalForcingConverter":
        """class method to create the converter from MDU file.

        Args:
            mdu_file (PathOrStr): Path to the D-Flow FM main input file (.mdu).
                Must be parsable into a standard FMModel.
                When this contains a valid filename for ExtFile, conversion
                will be performed.
            ext_file (PathOrStr, optional): Path to the output external forcings
                file. Defaults to the given ExtForceFileNew in the MDU file, if
                present, or forcings.ext otherwise.
            inifield_file (PathOrStr, optional): Path to the output initial field
                file. Defaults to the given IniFieldFile in the MDU file, if
                present, or inifields.ini otherwise.
            structure_file (PathOrStr, optional): Path to the output structures.ini
                file. Defaults to the given StructureFile in the MDU file, if
                present, or structures.ini otherwise.

        Returns:
            ExternalForcingConverter: The converter object.

        Raises:
            FileNotFoundError: If the MDU file does not exist.
            ValueError: If the old external forcing file is not found in the MDU file.
            DeprecationWarning: If the MDU file contains unknown keywords.
        """
        if isinstance(mdu_file, str):
            mdu_file = Path(mdu_file)

        mdu_parser = MDUParser(mdu_file)

        external_forcing_data = mdu_parser.loaded_fm_data.get("external_forcing")
        geometry = mdu_parser.loaded_fm_data.get("geometry")

        inifieldfile_mdu = geometry.get("inifieldfile")
        structurefile_mdu = geometry.get("structurefile")

        old_ext_force_file = external_forcing_data.get("extforcefile")
        if old_ext_force_file is None:
            raise ValueError(
                "An old formatted external forcing file (.ext) "
                "could not be found in the mdu file.\n"
                "Conversion is not possible or may not be necessary."
            )

        new_ext_force_file = external_forcing_data.get("extforcefilenew")

        old_ext_force_file = (
            Path(old_ext_force_file)
            if old_ext_force_file is not None
            else old_ext_force_file
        )
        new_ext_force_file = (
            Path(new_ext_force_file)
            if new_ext_force_file is not None
            else new_ext_force_file
        )

        root_dir = mdu_file.parent
        extoldfile = root_dir / old_ext_force_file

        if new_ext_force_file:
            ext_file = new_ext_force_file.resolve()
        else:
            if ext_file is None:
                old_ext = old_ext_force_file.with_stem(old_ext_force_file.stem + "-new")
                ext_file = root_dir / old_ext
            else:
                ext_file = root_dir / ext_file

        inifield_file = ExternalForcingConverter._get_inifield_file(
            inifield_file, root_dir, inifieldfile_mdu
        )
        structure_file = ExternalForcingConverter._get_structure_file(
            structure_file, root_dir, structurefile_mdu
        )

        return cls(extoldfile, ext_file, inifield_file, structure_file, mdu_parser)

    @staticmethod
    def _get_inifield_file(
        inifield_file: Optional[PathOrStr],
        root_dir: Path,
        inifieldfile_mdu: Optional[PathOrStr],
    ) -> Path:
        if inifield_file is not None:
            # user defined initial field file
            inifield_file = root_dir / inifield_file
        elif isinstance(inifieldfile_mdu, Path):
            # from the LegacyFMModel
            inifield_file = inifieldfile_mdu.resolve()
        elif isinstance(inifieldfile_mdu, str):
            # from reading the geometry section
            inifield_file = root_dir / inifieldfile_mdu
        else:
            print(
                f"The initial field file is not found in the mdu file, and not provided by the user. \n "
                f"given: {inifield_file}."
            )
        return inifield_file

    @staticmethod
    def _get_structure_file(
        structure_file: Optional[PathOrStr],
        root_dir: Path,
        structurefile_mdu: Optional[PathOrStr],
    ) -> Path:
        if structure_file is not None:
            # user defined structure file
            structure_file = root_dir / structure_file
        elif isinstance(structurefile_mdu, Path):
            # from the LegacyFMModel
            structure_file = structurefile_mdu.resolve()
        elif isinstance(structurefile_mdu, str):
            # from reading the geometry section
            structure_file = root_dir / structurefile_mdu
        else:
            print(
                "The structure file is not found in the mdu file, and not provide by the user. \n"
                f"given: {structure_file}."
            )
        return structure_file

    def _update_mdu_file(self):
        """Update the FM model with the new external forcings, initial fields and structures files.

        - The FM model will be saved with a postfix added to the filename.
        - The original FM model will be backed up.

        Notes:
            -If the `fm_model` was not read correctly due to `Unknown keywords` the function will update the field of the
            `ExtForceFileNew` in the mdu file, and store the new content in the `mdu_info` dictionary under a
            `new_mdu_content` key.
        """
        new_ext_file = self.ext_model.filepath.name
        self.mdu_parser.new_forcing_file = new_ext_file
        self.mdu_parser.content = self.mdu_parser.update_extforce_file_new()

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
):
    """Migrate all external forcings files in a directory tree to the new format.

    Args:
        root_dir: Directory to recursively find and convert .mdu files in.
        backup (bool, optional): Create a backup of each file that will be overwritten.
        suppress_errors (bool, optional): Suppress errors during conversion.
        remove_legacy (bool, optional): Remove legacy/old files (e.g. .tim) after conversion. Defaults to False.
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
                converter = ExternalForcingConverter.from_mdu(path)
                _, _, _ = converter.update()
                converter.save(backup=backup)
                if remove_legacy:
                    converter.clean()
            except Exception as e:
                if not suppress_errors:
                    print(f"Error processing {path}: {e}")
