import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Tuple, Union

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
from hydrolib.core.dflowfm.structure.models import Structure, StructureModel
from hydrolib.tools.ext_old_to_new.converters import ConverterFactory
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
        fm_model: Optional[LegacyFMModel] = None,
        verbose: bool = False,
    ):
        """Initialize the converter.

        The converter will create new external forcing, initial field and structure files in the same directory as the
        old external forcing file, if no paths were given by the user for the new models.

        Args:
            extold_model (PathOrStr, ExtOldModel): ExtOldModel or path to the old external forcing file.
            ext_file (PathOrStr, optional): Path to the new external forcing file.
            inifield_file (PathOrStr, optional): Path to the initial field file.
            structure_file (PathOrStr, optional): Path to the structure file.
            verbose (bool, optional): Enable verbose output. Defaults to False.

        Raises:
            FileNotFoundError: If the old external forcing file does not exist.

        Examples:
            >>> converter = ExternalForcingConverter("old-external-forcing.ext")
            >>> converter.update()
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

        if fm_model is not None:
            self._fm_model = fm_model

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
                self.ext_model.source_sink.append(new_quantity_block)
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

        if self.fm_model is not None:
            self._update_fm_model()

        return self.ext_model, self.inifield_model, self.structure_model

    def _convert_forcing(self, forcing) -> Union[Boundary, Lateral, Meteo, SourceSink]:
        """Convert a single forcing block to the appropriate new format."""

        try:
            converter_class = ConverterFactory.create_converter(forcing.quantity)

            # only the SourceSink converter needs the quantities' list
            if converter_class.__class__.__name__ == "SourceSinkConverter":
                temp_salinity_mdu = {}
                if self.fm_model is not None:
                    salinity = self.fm_model.physics.salinity
                    temperature = self.fm_model.physics.temperature
                    temp_salinity_mdu = {
                        "salinity": salinity,
                        "temperature": temperature,
                    }

                quantities = self.extold_model.quantities
                converter_class.root_dir = self.root_dir
                new_quantity_block = converter_class.convert(
                    forcing, quantities, **temp_salinity_mdu
                )
            else:
                new_quantity_block = converter_class.convert(forcing)
        except ValueError:
            # While this tool is in progress, accept that we do not convert all quantities yet.
            new_quantity_block = None

        return new_quantity_block

    def save(self, backup: bool = True):
        """Save the updated models to disk.

        Args:
            backup (bool, optional): Create a backup of each file that will be overwritten.
        """
        # FIXME: the backup is done is the file is already there, and here is baclup is done before saving the files,
        #  so it is not successfuly done.
        if backup:
            backup_file(self.ext_model.filepath)
            backup_file(self.inifield_model.filepath)
            backup_file(self.structure_model.filepath)

        self.ext_model.save()
        self.inifield_model.save()
        self.structure_model.save()
        if self.fm_model is not None:
            backup_file(self.fm_model.filepath)
            self.fm_model.save(recurse=False, exclude_unset=True)

    @classmethod
    def from_mdu(
        cls,
        mdu_file: PathOrStr,
        ext_file: Optional[PathOrStr] = "forcings.ext",
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
            fm_model = LegacyFMModel(mdu_file, recurse=False)
            root_dir = fm_model._resolved_filepath.parent

            extoldfile = root_dir / fm_model.external_forcing.extforcefile.filepath

            ext_file = (
                fm_model.external_forcing.extforcefilenew._resolved_filepath
                if fm_model.external_forcing.extforcefilenew
                else root_dir / ext_file
            )
            inifield_file = (
                fm_model.geometry.inifieldfile._resolved_filepath
                if fm_model.geometry.inifieldfile
                else root_dir / inifield_file
            )
            structure_file = (
                fm_model.geometry.structurefile[0]._resolved_filepath
                if fm_model.geometry.structurefile
                else root_dir / structure_file
            )
            return cls(extoldfile, ext_file, inifield_file, structure_file, fm_model)

        except Exception as error:
            if suppress_errors:
                print(f"Could not read {mdu_file} as a valid FM model:", error)
            else:
                raise error

    def _update_fm_model(self):
        """Update the FM model with the new external forcings, initial fields and structures files.

        - The FM model will be saved with a postfix added to the filename.
        - The original FM model will be backed up.
        """
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

    outfiles = {"extfile": None, "inifieldfile": None, "structurefile": None}
    if args.outfiles is not None:
        outfiles["extfile"] = args.outfiles[0]
        outfiles["inifieldfile"] = args.outfiles[1]
        outfiles["structurefile"] = args.outfiles[2]

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
