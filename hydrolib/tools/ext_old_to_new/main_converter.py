import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from pydantic.v1 import Extra
from pydantic.v1.error_wrappers import ValidationError
from tqdm import tqdm

from hydrolib.core import __version__
from hydrolib.core.basemodel import PathOrStr
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
from hydrolib.core.dflowfm.mdu.legacy import LegacyFMModel
from hydrolib.core.dflowfm.mdu.models import FMModel, Physics, Time
from hydrolib.core.dflowfm.structure.models import Structure, StructureModel
from hydrolib.tools.ext_old_to_new.converters import (
    ConverterFactory,
    update_extforce_file_new,
)
from hydrolib.tools.ext_old_to_new.utils import (
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
        mdu_info: Optional[Dict[str, int]] = None,
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
            mdu_info (Optional[Dict[LegacyFMModel, str]], optional):
                Dictionary with the FM model and other information.
                >>> mdu_info = {
                ...     "file_path": "path/to/mdu_file.mdu",
                ...     "refdate": "minutes since 2015-01-01 00:00:00",
                ...     "temperature": False,
                ...     "salinity": True,
                ... }

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
            rdir / "new-initial-conditions.ext"
            if inifield_file is None
            else inifield_file
        )
        self._inifield_model = construct_filemodel_new_or_existing(IniFieldModel, path)

        path = rdir / "new-structure.ext" if structure_file is None else structure_file
        self._structure_model = construct_filemodel_new_or_existing(
            StructureModel, path
        )

        if mdu_info is not None:
            self._fm_model = mdu_info.get("fm_model")
            self._mdu_info: Dict[str, int] = mdu_info

    @property
    def verbose(self) -> bool:
        """bool: Enable verbose output."""
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool):
        self._verbose = value

    @property
    def fm_model(self) -> LegacyFMModel:
        """FMModel: object with all blocks."""
        if not hasattr(self, "_fm_model"):
            model = None
        else:
            model = self._fm_model
        return model

    @property
    def mdu_info(self) -> Dict[int, str]:
        """Info from the mdu file needed for the conversion.

        - The SourceSink converter needs the salinity and temperature from the FM model.
        - The BoundaryCondition converter needs the start time from the FM model.
        Examples:
            >>> mdu_info = { #doctest: +SKIP
            ...     "fm_model": FMModel,
            ...     "refdate": "minutes since 2015-01-01 00:00:00",
            ...     "temperature": True,
            ...     "salinity": True,
            ... }
        """
        if not hasattr(self, "_mdu_info"):
            info = None
        else:
            info = self._mdu_info
        return info

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

        if self.mdu_info is not None:
            self._update_fm_model()

        return self.ext_model, self.inifield_model, self.structure_model

    def _convert_forcing(self, forcing) -> Union[Boundary, Lateral, Meteo, SourceSink]:
        """Convert a single forcing block to the appropriate new format."""

        converter_class = ConverterFactory.create_converter(forcing.quantity)
        converter_class.root_dir = self.root_dir

        # only the SourceSink converter needs the quantities' list
        if converter_class.__class__.__name__ == "SourceSinkConverter":

            if self.mdu_info is None:
                raise ValueError(
                    "FM model is required to convert SourcesSink quantities."
                )
            else:
                temp_salinity_mdu = self.mdu_info
                start_time = self.mdu_info.get("refdate")

            quantities = self.extold_model.quantities
            new_quantity_block = converter_class.convert(
                forcing, quantities, start_time=start_time, **temp_salinity_mdu
            )
        elif converter_class.__class__.__name__ == "BoundaryConditionConverter":
            if self.mdu_info is None:
                raise ValueError("FM model is required to convert Boundary conditions.")
            else:
                start_time = self.mdu_info.get("refdate")
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
        # FIXME: the backup is done is the file is already there, and here is backup is done before saving the files,
        #  so it is not successfuly done.
        if (
            len(self.inifield_model.parameter) > 0
            or len(self.inifield_model.initial) > 0
        ):
            if backup:
                backup_file(self.inifield_model.filepath)
            self.inifield_model.save(recurse=recursive)

        if len(self.structure_model.structure) > 0:
            if backup:
                backup_file(self.structure_model.filepath)
            self.structure_model.save(recurse=recursive)

        if backup:
            backup_file(self.ext_model.filepath)
        self.ext_model.save(recurse=recursive)

        if self.mdu_info is not None:
            mdu_file = self.mdu_info.get("file_path")
            backup_file(mdu_file)
            if self.fm_model is not None:
                self.fm_model.save(recurse=False, exclude_unset=True)
            elif "new_mdu_content" in self.mdu_info:
                with open(mdu_file, "w", encoding="utf-8") as file:
                    file.writelines(self.mdu_info.get("new_mdu_content"))
            else:
                raise MDUUpdateError(
                    "The FM model is not saved, and there was no new updated content for the mdu file."
                )

    @staticmethod
    def get_mdu_info(mdu_file: str) -> Tuple[Dict, Dict]:
        """Get the info needed from the mdu to process and convert the old external forcing files.

        Args:
            mdu_file (str):
                path to the mdu file
        Returns:
            data (Dict[str, str]):
                all the data inside the mdu file, with each section in the file as a key and the data of that section is
                the value of that key.
            mdu_info (Dict[str, str]):
                dictionary with the information needed for the conversion tool to convert the `SourceSink` and
                `Boundary` quantities. The dictionary will have three keys `temperature`, `salinity`, and `refdate`.
        """
        data = FMModel._load(FMModel, mdu_file)
        # read sections of the mdu file.
        time_data = data.get("time")
        physics_data = data.get("physics")
        mdu_time = Time(**time_data)
        mdu_physics = MyPhysics(**physics_data)

        ref_time = get_ref_time(mdu_time.refdate)
        mdu_info = {
            "file_path": mdu_file,
            "refdate": ref_time,
            "temperature": False if mdu_physics.temperature == 0 else True,
            "salinity": mdu_physics.salinity,
        }
        return data, mdu_info

    @classmethod
    def from_mdu(
        cls,
        mdu_file: PathOrStr,
        ext_file: Optional[PathOrStr] = None,
        inifield_file: Optional[PathOrStr] = "inifields.ini",
        structure_file: Optional[PathOrStr] = "structures.ini",
        suppress_errors: Optional[bool] = False,
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
            suppress_errors: Optional[bool]: Whether to suppress errors during execution.

        Returns:
            ExternalForcingConverter: The converter object.
        """
        try:
            try:
                fm_model = LegacyFMModel(mdu_file, recurse=False)
                old_ext_force_file = fm_model.external_forcing.extforcefile.filepath
                new_ext_force_file = fm_model.external_forcing.extforcefilenew
                inifieldfile = fm_model.geometry.inifieldfile
                structurefile = fm_model.geometry.structurefile
                mdu_info = {
                    "file_path": mdu_file,
                    "fm_model": fm_model,
                    "refdate": fm_model.time.refdate,
                    "temperature": fm_model.physics.temperature,
                    "salinity": fm_model.physics.salinity,
                }
            except ValidationError:
                data, mdu_info = ExternalForcingConverter.get_mdu_info(mdu_file)

                external_forcing_data = data.get("external_forcing")
                geometry = data.get("geometry")

                inifieldfile = geometry.get("inifieldfile")
                structurefile = geometry.get("structurefile")
                old_ext_force_file = external_forcing_data["extforcefile"]
                new_ext_force_file = external_forcing_data["extforcefilenew"]
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
                ext_file = new_ext_force_file._resolved_filepath
            else:
                if ext_file is None:
                    old_ext = old_ext_force_file.with_stem(
                        old_ext_force_file.stem + "-new"
                    )
                    ext_file = root_dir / old_ext
                else:
                    ext_file = root_dir / ext_file

            inifield_file = (
                inifieldfile._resolved_filepath
                if inifieldfile
                else root_dir / inifield_file
            )
            structure_file = (
                structurefile[0]._resolved_filepath
                if structurefile
                else root_dir / structure_file
            )
            return cls(extoldfile, ext_file, inifield_file, structure_file, mdu_info)

        except Exception as error:
            if suppress_errors:
                print(f"Could not read {mdu_file} as a valid FM model:", error)
            else:
                raise error

    def _update_fm_model(self):
        """Update the FM model with the new external forcings, initial fields and structures files.

        - The FM model will be saved with a postfix added to the filename.
        - The original FM model will be backed up.

        Notes:
            -If the `fm_model` was not read correctly due to `Unknown keywords` the function will update the field of the
            `ExtForceFileNew` in the mdu file, and store the new content in the `mdu_info` dictionary under a
            `new_mdu_content` key.
        """
        if self.fm_model is not None:
            if len(self.extold_model.forcing) > 0:
                self.fm_model.external_forcing.extforcefile = self.extold_model

            # Intentionally always include the new external forcings file, even if empty.
            self.fm_model.external_forcing.extforcefilenew = self.ext_model
            if (
                len(self.inifield_model.initial) > 0
                or len(self.inifield_model.parameter) > 0
            ):
                self.fm_model.geometry.inifieldfile = self.inifield_model
            if len(self.structure_model.structure) > 0:
                self.fm_model.geometry.structurefile[0] = self.structure_model
        else:
            mdu_path = self.mdu_info.get("file_path")
            new_ext_file = self.ext_model.filepath.name
            self.mdu_info["new_mdu_content"] = update_extforce_file_new(
                mdu_path, new_ext_file
            )

        if self.verbose:
            print(f"succesfully saved converted file {self.fm_model.filepath} ")

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


class MDUUpdateError(Exception):
    """mdu file is not updated."""

    def __init__(self, error_message: str):
        """__init__."""
        print(error_message)


class MyPhysics(Physics):
    # Define your attributes here

    class Config:
        extra = Extra.ignore  # Ignore unknown fields instead of raising an error

    def __init__(self, **data):
        # Filter out unexpected fields before initializing Physics
        valid_fields = self.__annotations__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        super().__init__(
            **filtered_data
        )  # Initialize the parent class with valid fields only


def ext_old_to_new_dir_recursive(
    root_dir: PathOrStr, backup: bool = True, suppress_errors: bool = False
):
    """Migrate all external forcings files in a directory tree to the new format.

    Args:
        root_dir: Directory to recursively find and convert .mdu files in.
        backup (bool, optional): Create a backup of each file that will be overwritten.
        suppress_errors (bool, optional): Suppress errors during conversion.
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
                converter = ExternalForcingConverter.from_mdu(
                    path, suppress_errors=suppress_errors
                )
                _, _, _ = converter.update()
                converter.save(backup=backup)
            except Exception as e:
                if not suppress_errors:
                    print(f"Error processing {path}: {e}")


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ext_old_to_new",
        description="Convert D-Flow FM legacy external forcings files to current external forcings file/initial fields file/structures file.",
    )

    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print diagnostic information"
    )
    parser.add_argument(
        "--mdufile",
        "-m",
        action="store",
        help="Automatically take input and output filenames from MDUFILE",
    )
    parser.add_argument(
        "--extoldfile",
        "-e",
        action="store",
        help="Input EXTOLDFILE to be converted.",
    )
    parser.add_argument(
        "--dir",
        "-d",
        action="store",
        help="Directory to recursively find and convert .mdu files in",
    )
    parser.add_argument(
        "--outfiles",
        "-o",
        action="store",
        nargs=3,
        metavar=("EXTFILE", "INIFIELDFILE", "STRUCTUREFILE"),
        help="Save forcings, initial fields and structures to specified filenames",
    )
    parser.add_argument(
        "--postfix",
        "-p",
        action="store",
        help="Append POSTFIX to the output filenames (before the extension).",
    )
    parser.add_argument(
        "--backup",
        "-b",
        action="store_true",
        default=True,
        help="Create a backup of each file that will be overwritten.",
    )
    parser.add_argument(
        "--no-backup",
        dest="backup",
        action="store_false",
        help="Do not create a backup of each file that will be overwritten.",
    )
    return parser


def get_ref_time(input_date: str, date_format: str = "%Y%m%d"):
    date_object = datetime.strptime(f"{input_date}", date_format)
    return f"MINUTES SINCE {date_object}"


def main(args=None):
    """
    Main entry point for ext_old_to_new tool.
    Args:
        args : list
            A of arguments as if they were input in the command line. Leave it
            None to use sys.argv.
    """
    parser = _get_parser()
    args = parser.parse_args(args)
    backup = args.backup is not None

    if args.mdufile is not None and args.extoldfile is not None:
        print("Error: use either input MDUFILE or EXTOLDFILE, not both.")
        sys.exit(1)
    ...

    outfiles = {"ext_file": None, "inifield_file": None, "structure_file": None}
    if args.outfiles is not None:
        outfiles["ext_file"] = args.outfiles[0]
        outfiles["inifield_file"] = args.outfiles[1]
        outfiles["structure_file"] = args.outfiles[2]

    if args.mdufile is not None:
        converter = ExternalForcingConverter.from_mdu(
            args.mdufile, **outfiles, suppress_errors=True
        )
        converter.verbose = args.verbose
        converter.update()
        converter.save(backup=backup)
    elif args.extoldfile is not None:
        converter = ExternalForcingConverter(
            args.extoldfile,
            outfiles["extfile"],
            outfiles["inifieldfile"],
            outfiles["structurefile"],
        )
        converter.update()
        converter.save(backup=backup)
    elif args.dir is not None:
        ext_old_to_new_dir_recursive(args.dir, backup=backup)
    else:
        print("Error: no input specified. Use one of --mdufile, --extoldfile or --dir.")


if __name__ == "__main__":
    main()
