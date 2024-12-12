import argparse
import os
import sys
from pathlib import Path
from typing import Tuple, Union

from hydrolib.core import __version__
from hydrolib.core.basemodel import FileModel, PathOrStr
from hydrolib.core.dflowfm.ext.models import Boundary, ExtModel, Lateral, Meteo
from hydrolib.core.dflowfm.extold.models import ExtOldModel
from hydrolib.core.dflowfm.inifield.models import (
    IniFieldModel,
    InitialField,
    ParameterField,
)
from hydrolib.core.dflowfm.mdu.legacy import LegacyFMModel
from hydrolib.core.dflowfm.structure.models import Structure, StructureModel

from .converter_factory import ConverterFactory
from .utils import (
    backup_file,
    construct_filemodel_new_or_existing,
    construct_filepath_with_postfix,
)

_program: str = "ext_old_to_new"
_verbose: bool = False


class ExternalForcingConverter:

    def __init__(
        self,
        extold_model: Union[PathOrStr, ExtOldModel],
        ext_model_path: PathOrStr = None,
        inifield_model_path: PathOrStr = None,
        structure_model_path: PathOrStr = None,
    ):
        """Initialize the converter.

        The converter will create new external forcing, initial field and structure files in the same directory as the
        old external forcing file, if no paths were given by the user for the new models.

        Args:
            extold_model (PathOrStr, ExtOldModel): ExtOldModel or path to the old external forcing file.
            ext_model_path (PathOrStr, optional): Path to the new external forcing file.
            inifield_model_path (PathOrStr, optional): Path to the initial field file.
            structure_model_path (PathOrStr, optional): Path to the structure file.
        """
        if isinstance(extold_model, Path) or isinstance(extold_model, str):
            extold_model = self._read_old_file(extold_model)

        self._extold_model = extold_model
        rdir = self._extold_model.filepath.parent

        # create the new models if not provided by the user in the same directory as the old external file
        path = (
            rdir.joinpath("new-external-forcing.ext")
            if ext_model_path is None
            else ext_model_path
        )
        self._ext_model = construct_filemodel_new_or_existing(ExtModel, path)

        path = (
            rdir.joinpath("new-initial-conditions.ext")
            if inifield_model_path is None
            else inifield_model_path
        )
        self._inifield_model = construct_filemodel_new_or_existing(IniFieldModel, path)

        path = (
            rdir.joinpath("new-structure.ext")
            if structure_model_path is None
            else structure_model_path
        )
        self._structure_model = construct_filemodel_new_or_existing(
            StructureModel, path
        )

    @property
    def extold_model(self):
        """old external forcing model."""
        return self._extold_model

    @property
    def ext_model(self) -> FileModel:
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
    def inifield_model(self) -> FileModel:
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
    def structure_model(self) -> FileModel:
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
            ExtOldModel: object with all forcing blocks."""
        global _verbose
        if not isinstance(extoldfile, Path):
            extoldfile = Path(extoldfile)

        if not extoldfile.exists():
            raise FileNotFoundError(f"File not found: {extoldfile}")

        extold_model = ExtOldModel(extoldfile)

        if _verbose:
            print(f"Read {len(extold_model.forcing)} forcing blocks from {extoldfile}.")

        return extold_model

    def update(
        self,
        postfix: str = "",
    ) -> Union[Tuple[FileModel, FileModel, FileModel], None]:
        """
        Convert old external forcing file to new format files.
        When the output files are existing, output will be appended to them.

        Args:
            postfix (str, optional): Append POSTFIX to the output filenames. Defaults to "".

        Returns:
            Tuple[ExtOldModel, ExtModel, IniFieldModel, StructureModel]:
                The updated models (already written to disk). Maybe used
                at call site to inspect the updated models.
        """
        if _verbose:
            workdir = os.getcwd() + "\\"
            print(f"Work dir: {workdir}")
            print("Using attribute files:")
            print("Input:")
            print(f"* {self.extold_model.filepath}")
            print("Output:")
            print(f"* {self.ext_model.filepath}")
            print(f"* {self.inifield_model.filepath}")
            print(f"* {self.structure_model.filepath}")

        for forcing in self.extold_model.forcing:
            try:
                converter_class = ConverterFactory.create_converter(forcing.quantity)
                new_quantity_block = converter_class.convert(forcing)
            except ValueError:
                # While this tool is in progress, accept that we do not convert all quantities yet.
                new_quantity_block = None

            if isinstance(new_quantity_block, Boundary):
                self.ext_model.boundary.append(new_quantity_block)
            elif isinstance(new_quantity_block, Lateral):
                self.ext_model.lateral.append(new_quantity_block)
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

        return self.ext_model, self.inifield_model, self.structure_model

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


def ext_old_to_new_from_mdu(
    mdufile: PathOrStr,
    extfile: PathOrStr = "forcings.ext",
    inifieldfile: PathOrStr = "inifields.ini",
    structurefile: PathOrStr = "structures.ini",
    backup: bool = True,
    postfix: str = "_new",
):
    """Wrapper converter function for converting legacy external forcings
    files into cross section .ini files, for files listed in an MDU file.

    Args:
        mdufile (PathOrStr): Path to the D-Flow FM main input file (.mdu).
            Must be parsable into a standard FMModel.
            When this contains a valid filename for ExtFile, conversion
            will be performed.
        extfile (PathOrStr, optional): Path to the output external forcings
            file. Defaults to the given ExtForceFileNew in the MDU file, if
            present, or forcings.ext otherwise.
        inifieldfile (PathOrStr, optional): Path to the output initial field
            file. Defaults to the given IniFieldFile in the MDU file, if
            present, or inifields.ini otherwise.
        structurefile (PathOrStr, optional): Path to the output structures.ini
            file. Defaults to the given StructureFile in the MDU file, if
            present, or structures.ini otherwise.
        backup (bool, optional): Create a backup of each file that will be
            overwritten. Defaults to True.
        postfix (str, optional): Append postfix to the output filenames
            (before the file suffix). Defaults to "_new".
    """
    global _verbose

    # For flexibility, also accept legacy MDU file versions (which does not
    # affect external forcings functionality anyway):
    try:
        fmmodel = LegacyFMModel(mdufile, recurse=False)
    except Exception as error:
        print(f"Could not read {mdufile} as a valid FM model:", error)
        return

    workdir = fmmodel._resolved_filepath.parent
    os.chdir(workdir)
    if fmmodel.external_forcing.extforcefile is None and _verbose:
        print(f"mdufile: {mdufile} does not contain an old style external forcing file")
        return

    extoldfile = fmmodel.external_forcing.extforcefile._resolved_filepath

    extfile = (
        fmmodel.external_forcing.extforcefilenew._resolved_filepath
        if fmmodel.external_forcing.extforcefilenew
        else workdir / extfile
    )
    inifieldfile = (
        fmmodel.geometry.inifieldfile._resolved_filepath
        if fmmodel.geometry.inifieldfile
        else workdir / inifieldfile
    )
    structurefile = (
        fmmodel.geometry.structurefile[0]._resolved_filepath
        if fmmodel.geometry.structurefile
        else workdir / structurefile
    )

    converter = ExternalForcingConverter(
        extoldfile, extfile, inifieldfile, structurefile
    )

    # The actual conversion:
    ext_model, inifield_model, structure_model = converter.update(postfix)
    converter.save(backup)
    extold_model = converter.extold_model
    try:
        # And include the new files in the FM model:
        _ = ExtModel(extfile)
        if len(extold_model.forcing) > 0:
            fmmodel.external_forcing.extforcefile = extold_model
        # Intentionally always include the new external forcings file, even if empty.
        fmmodel.external_forcing.extforcefilenew = ext_model
        if len(inifield_model.initial) > 0 or len(inifield_model.parameter) > 0:
            fmmodel.geometry.inifieldfile = inifield_model
        if len(structure_model.structure) > 0:
            fmmodel.geometry.structurefile[0] = structure_model

        # Save the updated FM model:
        if backup:
            backup_file(fmmodel.filepath)
        converted_mdufile = construct_filepath_with_postfix(mdufile, postfix)
        fmmodel.filepath = converted_mdufile
        fmmodel.save(recurse=False, exclude_unset=True)
        if _verbose:
            print(f"succesfully saved converted file {mdufile} ")

    except Exception as error:
        print("The converter did not produce a valid ext file:", error)
        return


def ext_old_to_new_dir_recursive(dir: PathOrStr, backup: bool = True):

    for path in Path(dir).rglob("*.mdu"):
        if "_ext" not in path.name:
            ext_old_to_new_from_mdu(path, backup)


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_program,
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
    global _verbose

    parser = _get_parser()
    args = parser.parse_args(args)
    _verbose = args.verbose

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
        ext_old_to_new_from_mdu(
            args.mdufile, **outfiles, backup=backup, postfix=args.postfix
        )
    elif args.extoldfile is not None:
        converter = ExternalForcingConverter(
            args.extoldfile,
            outfiles["extfile"],
            outfiles["inifieldfile"],
            outfiles["structurefile"],
        )
        converter.update(postfix=args.postfix)
        converter.save(backup=backup)
    elif args.dir is not None:
        ext_old_to_new_dir_recursive(args.dir, backup=backup)
    else:
        print("Error: no input specified. Use one of --mdufile, --extoldfile or --dir.")

    print(_program + ": done")


if __name__ == "__main__":
    main()
